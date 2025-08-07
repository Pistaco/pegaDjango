from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload, EnvioDetalle, Envio, \
    Bodega, Familia, Notificacion, Pendiente


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class ProductoStockSerializer(serializers.ModelSerializer):
    stock_id = serializers.IntegerField(source="stock.id", read_only=True)
    class Meta:
        model = Producto
        fields = '__all__'

class PendienteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Pendiente
        fields = ['id', 'producto', 'producto_nombre', 'descripcion', 'completado', 'creado_en']


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['usuario', 'creada_en']


    def validate(self, data):
    # Permitir actualizaciones parciales sin validación completa
        if data.get('mensaje') is None:
            return data

    # Contar cuántos están definidos
        asociados = sum([
            1 if data.get('stock') is not None else 0,
            1 if data.get('envio') is not None else 0,
            1 if data.get('pendiente') is not None else 0,
        ])

        if asociados == 0:
            return data

        if asociados != 1:
            raise serializers.ValidationError(
                "Debe asociar la notificación a exactamente uno entre stock, envío o pendiente."
            )

        return data

class FamiliaSerializer(serializers.ModelSerializer):
    ruta_completa = serializers.SerializerMethodField()
    class Meta:
        model = Familia
        fields = '__all__'

    def get_ruta_completa(self, obj):
        return obj.get_ruta_completa()

class IngresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingreso
        fields = '__all__'


class RetiroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retiro
        fields = '__all__'

    def validate(self, data):
        producto = data['id_producto']
        bodega = data['bodega']
        cantidad_retirar = data['cantidad']

        try:
            stock = StockActual.objects.get(producto=producto, bodega=bodega)
        except StockActual.DoesNotExist:
            raise serializers.ValidationError(
                {"bodega": "No hay stock de este producto en la bodega seleccionada."}
            )

        if cantidad_retirar == 0:
            raise serializers.ValidationError({"cantidad": "No puede ser cero."})

        if cantidad_retirar > stock.cantidad:
            raise serializers.ValidationError(
                {"cantidad": "No hay suficiente stock para este retiro."}
            )

        return data

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class StockActualSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockActual
        fields = '__all__'

class PDFUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFUpload
        fields = ['id', 'archivo']

class ExcelUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelUpload
        fields = ['id', 'archivo']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']  # No 'password', 'email', etc.


class BodegaSerializer(serializers.ModelSerializer):
    usuarios = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    class Meta:
        model = Bodega
        fields = ["id", "nombre", "ubicacion", "usuarios"]

class EnvioDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvioDetalle
        fields = ['producto', 'cantidad']

class EnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        fields = '__all__'


class EnvioSerializerAnidado(serializers.ModelSerializer):
    detalles = EnvioDetalleSerializer(many=True)

    class Meta:
        model = Envio
        fields = ['id', 'bodega_origen', 'bodega_destino', 'fecha', 'confirmado', 'detalles']

    def validate(self, data):
        # Detectar si se está intentando confirmar
        confirmar = data.get('confirmado', getattr(self.instance, 'confirmado', False))
        detalles = data.get('detalles', [])

        origen = data.get('origen', getattr(self.instance, 'origen', None))

        if confirmar and detalles and origen:
            for detalle in detalles:
                producto = detalle['producto']
                cantidad = detalle['cantidad']
                try:
                    stock = StockActual.objects.get(bodega=origen, producto=producto)
                except StockActual.DoesNotExist:
                    raise serializers.ValidationError(
                        f"No hay stock registrado para el producto {producto} en la bodega origen."
                    )

                if stock.cantidad < cantidad:
                    raise serializers.ValidationError(
                        f"Stock insuficiente de '{producto}' en la bodega origen. Disponible: {stock.cantidad}, requerido: {cantidad}."
                    )

        return data

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        envio = Envio.objects.create(**validated_data)
        for detalle_data in detalles_data:
            EnvioDetalle.objects.create(envio=envio, **detalle_data)
        return envio

    def update(self, instance, validated_data):
        if instance.confirmado and not validated_data.get('confirmado', True):
            raise serializers.ValidationError("No se puede desconfirmar un envío ya confirmado.")

            # Permitir solo editar si no está confirmado
        if instance.confirmado:
            raise serializers.ValidationError("No se puede modificar un envío confirmado.")

        detalles_data = validated_data.pop('detalles', None)
        instance.bodega_origen = validated_data.get('bodega_origen', instance.bodega_origen)
        instance.bodega_destino = validated_data.get('bodega_destino', instance.bodega_destino)
        instance.confirmado = validated_data.get('confirmado', instance.confirmado)
        instance.save()

        if detalles_data is not None:
            instance.detalles.all().delete()
            for detalle_data in detalles_data:
                EnvioDetalle.objects.create(envio=instance, **detalle_data)

        return instance
