from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import serializers

from app.models import Bodega, Envio, EnvioDetalle, Familia, Producto, StockActual, Notificacion
from app.models import Ingreso, Retiro
from app.serializer import EnvioSerializerAnidado, IngresoSerializer, RetiroSerializer


class EnvioConfirmacionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='12345678')
        self.bodega_origen = Bodega.objects.create(nombre='Origen', ubicacion='A')
        self.bodega_destino = Bodega.objects.create(nombre='Destino', ubicacion='B')
        self.familia = Familia.objects.create(nombre='General')
        self.producto = Producto.objects.create(
            codigo_barras='ABC123',
            nombre='Producto 1',
            descripcion='Prueba',
            precio=1000,
            familia=self.familia,
        )

    def test_confirmar_envio_mueve_stock_origen_y_destino(self):
        envio = Envio.objects.create(
            bodega_origen=self.bodega_origen,
            bodega_destino=self.bodega_destino,
            usuario=self.user,
            confirmado=False,
        )
        EnvioDetalle.objects.create(envio=envio, producto=self.producto, cantidad=4)
        StockActual.objects.create(producto=self.producto, bodega=self.bodega_origen, cantidad=10)

        serializer = EnvioSerializerAnidado(
            instance=envio,
            data={'confirmado': True},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        stock_origen = StockActual.objects.get(producto=self.producto, bodega=self.bodega_origen)
        stock_destino = StockActual.objects.get(producto=self.producto, bodega=self.bodega_destino)
        envio.refresh_from_db()

        self.assertTrue(envio.confirmado)
        self.assertEqual(stock_origen.cantidad, 6)
        self.assertEqual(stock_destino.cantidad, 4)

    def test_confirmar_envio_falla_si_hay_stock_insuficiente(self):
        envio = Envio.objects.create(
            bodega_origen=self.bodega_origen,
            bodega_destino=self.bodega_destino,
            usuario=self.user,
            confirmado=False,
        )
        EnvioDetalle.objects.create(envio=envio, producto=self.producto, cantidad=8)
        StockActual.objects.create(producto=self.producto, bodega=self.bodega_origen, cantidad=3)

        serializer = EnvioSerializerAnidado(
            instance=envio,
            data={'confirmado': True},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(serializers.ValidationError):
            serializer.save()

        envio.refresh_from_db()
        stock_origen = StockActual.objects.get(producto=self.producto, bodega=self.bodega_origen)

        self.assertFalse(envio.confirmado)
        self.assertEqual(stock_origen.cantidad, 3)
        self.assertFalse(
            StockActual.objects.filter(producto=self.producto, bodega=self.bodega_destino).exists()
        )


class MovimientosStockTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mov-user', password='12345678')
        self.bodega = Bodega.objects.create(nombre='Bodega 1', ubicacion='X')
        self.familia = Familia.objects.create(nombre='Familia Mov')
        self.producto = Producto.objects.create(
            codigo_barras='MOV123',
            nombre='Producto Mov',
            descripcion='Prueba movimiento',
            precio=500,
            familia=self.familia,
        )

    def test_crear_ingreso_aumenta_stock(self):
        serializer = IngresoSerializer(data={
            'id_producto': self.producto.id,
            'id_usuario': self.user.id,
            'bodega': self.bodega.id,
            'cantidad': 7,
            'observacion': 'Ingreso test',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        stock = StockActual.objects.get(producto=self.producto, bodega=self.bodega)
        self.assertEqual(stock.cantidad, 7)
        self.assertEqual(Ingreso.objects.count(), 1)

    def test_crear_retiro_disminuye_stock(self):
        StockActual.objects.create(producto=self.producto, bodega=self.bodega, cantidad=10)
        serializer = RetiroSerializer(data={
            'id_producto': self.producto.id,
            'id_usuario': self.user.id,
            'bodega': self.bodega.id,
            'cantidad': 4,
            'observacion': 'Retiro test',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        stock = StockActual.objects.get(producto=self.producto, bodega=self.bodega)
        self.assertEqual(stock.cantidad, 6)
        self.assertEqual(Retiro.objects.count(), 1)

    def test_crear_retiro_con_stock_insuficiente_falla(self):
        StockActual.objects.create(producto=self.producto, bodega=self.bodega, cantidad=2)
        serializer = RetiroSerializer(data={
            'id_producto': self.producto.id,
            'id_usuario': self.user.id,
            'bodega': self.bodega.id,
            'cantidad': 5,
            'observacion': 'Retiro inválido',
        })

        self.assertFalse(serializer.is_valid())
        stock = StockActual.objects.get(producto=self.producto, bodega=self.bodega)
        self.assertEqual(stock.cantidad, 2)
        self.assertEqual(Retiro.objects.count(), 0)

    def test_crear_retiro_elimina_stock_si_queda_en_cero(self):
        StockActual.objects.create(producto=self.producto, bodega=self.bodega, cantidad=4)
        serializer = RetiroSerializer(data={
            'id_producto': self.producto.id,
            'id_usuario': self.user.id,
            'bodega': self.bodega.id,
            'cantidad': 4,
            'observacion': 'Retiro total',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertFalse(
            StockActual.objects.filter(producto=self.producto, bodega=self.bodega).exists()
        )
        self.assertEqual(Retiro.objects.count(), 1)


class EnvioNotificacionTests(TestCase):
    def test_crear_envio_crea_notificaciones_en_bodega_destino(self):
        creador = User.objects.create_user(username='creador', password='12345678')
        user_destino_1 = User.objects.create_user(username='destino1', password='12345678')
        user_destino_2 = User.objects.create_user(username='destino2', password='12345678')

        bodega_origen = Bodega.objects.create(nombre='Origen N', ubicacion='O')
        bodega_destino = Bodega.objects.create(nombre='Destino N', ubicacion='D')
        bodega_destino.usuarios.add(user_destino_1, user_destino_2)

        envio = Envio.objects.create(
            bodega_origen=bodega_origen,
            bodega_destino=bodega_destino,
            usuario=creador,
            confirmado=False,
        )

        notificaciones = Notificacion.objects.filter(envio=envio).order_by('usuario_id')
        self.assertEqual(notificaciones.count(), 2)
        self.assertEqual(notificaciones[0].titulo, 'Envío en camino')
        self.assertIn(f'/envios/{envio.id}', notificaciones[0].mensaje)
        self.assertIn(notificaciones[0].usuario_id, [user_destino_1.id, user_destino_2.id])
        self.assertIn(notificaciones[1].usuario_id, [user_destino_1.id, user_destino_2.id])
