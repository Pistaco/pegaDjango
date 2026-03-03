import factory
import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from app.models import Bodega, Envio, EnvioDetalle, Gerencia, Ingreso, Notificacion, Producto, Retiro, StockActual
from app.serializer import EnvioSerializerAnidado, IngresoSerializer, RetiroSerializer

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")


class BodegaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bodega

    nombre = factory.Sequence(lambda n: f"Bodega {n}")
    ubicacion = "A"


class GerenciaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Gerencia

    nombre = factory.Sequence(lambda n: f"Gerencia {n}")


class ProductoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Producto

    codigo_barras = factory.Sequence(lambda n: f"COD{n:06d}")
    nombre = factory.Sequence(lambda n: f"Producto {n}")
    descripcion = "Prueba"
    precio = 1000
    gerencia = factory.SubFactory(GerenciaFactory)


@pytest.mark.django_db
def test_confirmar_envio_mueve_stock_origen_y_destino():
    user = UserFactory()
    bodega_origen = BodegaFactory(nombre="Origen")
    bodega_destino = BodegaFactory(nombre="Destino")
    producto = ProductoFactory()

    envio = Envio.objects.create(
        bodega_origen=bodega_origen,
        bodega_destino=bodega_destino,
        usuario=user,
        confirmado=False,
    )
    EnvioDetalle.objects.create(envio=envio, producto=producto, cantidad=4)
    StockActual.objects.create(producto=producto, bodega=bodega_origen, cantidad=10)

    serializer = EnvioSerializerAnidado(instance=envio, data={"confirmado": True}, partial=True)
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    stock_origen = StockActual.objects.get(producto=producto, bodega=bodega_origen)
    stock_destino = StockActual.objects.get(producto=producto, bodega=bodega_destino)
    envio.refresh_from_db()

    assert envio.confirmado is True
    assert stock_origen.cantidad == 6
    assert stock_destino.cantidad == 4


@pytest.mark.django_db
def test_confirmar_envio_falla_si_hay_stock_insuficiente():
    user = UserFactory()
    bodega_origen = BodegaFactory(nombre="Origen")
    bodega_destino = BodegaFactory(nombre="Destino")
    producto = ProductoFactory()

    envio = Envio.objects.create(
        bodega_origen=bodega_origen,
        bodega_destino=bodega_destino,
        usuario=user,
        confirmado=False,
    )
    EnvioDetalle.objects.create(envio=envio, producto=producto, cantidad=8)
    StockActual.objects.create(producto=producto, bodega=bodega_origen, cantidad=3)

    serializer = EnvioSerializerAnidado(instance=envio, data={"confirmado": True}, partial=True)
    assert serializer.is_valid(), serializer.errors

    with pytest.raises(serializers.ValidationError):
        serializer.save()

    envio.refresh_from_db()
    stock_origen = StockActual.objects.get(producto=producto, bodega=bodega_origen)

    assert envio.confirmado is False
    assert stock_origen.cantidad == 3
    assert not StockActual.objects.filter(producto=producto, bodega=bodega_destino).exists()


@pytest.mark.django_db
def test_crear_ingreso_aumenta_stock():
    user = UserFactory()
    bodega = BodegaFactory()
    producto = ProductoFactory()

    serializer = IngresoSerializer(
        data={
            "producto": producto.id,
            "usuario": user.id,
            "bodega": bodega.id,
            "cantidad": 7,
            "observacion": "Ingreso test",
        }
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    stock = StockActual.objects.get(producto=producto, bodega=bodega)
    assert stock.cantidad == 7
    assert Ingreso.objects.count() == 1


@pytest.mark.django_db
def test_crear_retiro_disminuye_stock():
    user = UserFactory()
    bodega = BodegaFactory()
    producto = ProductoFactory()
    StockActual.objects.create(producto=producto, bodega=bodega, cantidad=10)

    serializer = RetiroSerializer(
        data={
            "producto": producto.id,
            "usuario": user.id,
            "bodega": bodega.id,
            "cantidad": 4,
            "observacion": "Retiro test",
        }
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    stock = StockActual.objects.get(producto=producto, bodega=bodega)
    assert stock.cantidad == 6
    assert Retiro.objects.count() == 1


@pytest.mark.django_db
def test_crear_retiro_con_stock_insuficiente_falla():
    user = UserFactory()
    bodega = BodegaFactory()
    producto = ProductoFactory()
    StockActual.objects.create(producto=producto, bodega=bodega, cantidad=2)

    serializer = RetiroSerializer(
        data={
            "producto": producto.id,
            "usuario": user.id,
            "bodega": bodega.id,
            "cantidad": 5,
            "observacion": "Retiro invalido",
        }
    )

    assert not serializer.is_valid()
    stock = StockActual.objects.get(producto=producto, bodega=bodega)
    assert stock.cantidad == 2
    assert Retiro.objects.count() == 0


@pytest.mark.django_db
def test_crear_retiro_elimina_stock_si_queda_en_cero():
    user = UserFactory()
    bodega = BodegaFactory()
    producto = ProductoFactory()
    StockActual.objects.create(producto=producto, bodega=bodega, cantidad=4)

    serializer = RetiroSerializer(
        data={
            "producto": producto.id,
            "usuario": user.id,
            "bodega": bodega.id,
            "cantidad": 4,
            "observacion": "Retiro total",
        }
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert not StockActual.objects.filter(producto=producto, bodega=bodega).exists()
    assert Retiro.objects.count() == 1


@pytest.mark.django_db
def test_crear_envio_crea_notificaciones_en_bodega_destino():
    creador = UserFactory(username="creador")
    user_destino_1 = UserFactory(username="destino1")
    user_destino_2 = UserFactory(username="destino2")
    bodega_origen = BodegaFactory(nombre="Origen N")
    bodega_destino = BodegaFactory(nombre="Destino N")
    bodega_destino.usuarios.add(user_destino_1, user_destino_2)

    envio = Envio.objects.create(
        bodega_origen=bodega_origen,
        bodega_destino=bodega_destino,
        usuario=creador,
        confirmado=False,
    )

    notificaciones = Notificacion.objects.filter(envio=envio).order_by("usuario_id")
    assert notificaciones.count() == 2
    assert "camino" in notificaciones[0].titulo.lower()
    assert f"/envios/{envio.id}" in notificaciones[0].mensaje
    assert notificaciones[0].usuario_id in [user_destino_1.id, user_destino_2.id]
    assert notificaciones[1].usuario_id in [user_destino_1.id, user_destino_2.id]
