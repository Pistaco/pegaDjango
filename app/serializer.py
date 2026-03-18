from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload, EnvioDetalle, Envio, \
    Bodega, Gerencia, Notificacion, Pendiente, ImportJob, ImportRow

User = get_user_model()

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'
    codigo_barras = serializers.CharField(required=False, allow_blank=True)

class ProductoInventarioSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField()
    class Meta:
        model = Producto
        fields = ('id', 'nombre', 'precio', 'cantidad')

class ProductoStockSerializer(serializers.ModelSerializer):
    # Campos anidados para compatibilidad con el frontend.
    nombre = serializers.CharField(source="producto.nombre", read_only=True)
    codigo_barras = serializers.CharField(source="producto.codigo_barras", read_only=True)
    descripcion = serializers.CharField(source="producto.descripcion", read_only=True)
    precio = serializers.IntegerField(source="producto.precio", read_only=True)
    parte = serializers.IntegerField(source="producto.parte", read_only=True)
    gerencia = serializers.CharField(source="producto.gerencia.nombre", read_only=True)
    cantidad_en_stock = serializers.IntegerField(source="cantidad", read_only=True)

    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    producto_codigo_barras = serializers.CharField(source="producto.codigo_barras", read_only=True)
    producto_parte = serializers.IntegerField(source="producto.parte", read_only=True)
    producto_descripcion = serializers.CharField(source="producto.descripcion", read_only=True)
    producto_precio = serializers.IntegerField(source="producto.precio", read_only=True)
    producto_gerencia = serializers.CharField(source="producto.gerencia.nombre", read_only=True)
    producto_gerencia_id = serializers.IntegerField(source="producto.gerencia.id", read_only=True)
    bodega_nombre = serializers.CharField(source="bodega.nombre", read_only=True)

    class Meta:
        model = StockActual
        fields = [
            "id",
            "producto",
            "nombre",
            "codigo_barras",
            "descripcion",
            "precio",
            "parte",
            "gerencia",
            "cantidad_en_stock",
            "producto_nombre",
            "producto_codigo_barras",
            "producto_parte",
            "producto_descripcion",
            "producto_precio",
            "producto_gerencia",
            "producto_gerencia_id",
            "bodega",
            "bodega_nombre",
            "cantidad",
            "actualizado_en",
        ]


class PendienteSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Pendiente
        fields = ['id', 'producto', 'producto_nombre', 'descripcion', 'completado', 'creado_en', "bodega"]




class NotificacionSerializer(serializers.ModelSerializer):
    envio_confirmado = serializers.BooleanField(source='envio.confirmado', read_only=True)
    stock_producto_nombre = serializers.CharField(source='stock.producto.nombre', read_only=True)
    stock_producto_id = serializers.IntegerField(source='stock.producto.id', read_only=True)

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

class GerenciaSerializer(serializers.ModelSerializer):
    ruta_completa = serializers.SerializerMethodField()
    class Meta:
        model = Gerencia
        fields = '__all__'


    def validate(self, attrs):
        parent = attrs.get('parent')
        instance = getattr(self, 'instance', None)
        if instance and parent and parent.id == instance.id:
            raise serializers.ValidationError("Una gerencia no puede ser su propio padre.")
        return attrs

    def get_ruta_completa(self, obj):
        return obj.get_ruta_completa()

class IngresoSerializer(serializers.ModelSerializer):
    # Compatibilidad de payload legado: id_producto/id_usuario.
    id_producto = serializers.PrimaryKeyRelatedField(
        source='producto',
        queryset=Producto.objects.all(),
        write_only=True,
        required=False,
    )
    id_usuario = serializers.PrimaryKeyRelatedField(
        source='usuario',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Ingreso
        fields = ['id', 'producto', 'usuario', 'bodega', 'cantidad', 'fecha', 'observacion', 'id_producto', 'id_usuario']
        read_only_fields = ['id', 'fecha']
        extra_kwargs = {
            'producto': {'required': False},
            'usuario': {'required': False},
        }

    def validate(self, attrs):
        if 'producto' not in attrs:
            raise serializers.ValidationError({'producto': 'Este campo es obligatorio.'})
        if 'usuario' not in attrs:
            raise serializers.ValidationError({'usuario': 'Este campo es obligatorio.'})
        return attrs

    def create(self, validated_data):
        from .domain.bus import bus
        from .domain.events import StockChanged
        
        with transaction.atomic():
            ingreso = super().create(validated_data)
            
            # Publicar evento de cambio de stock
            bus.publish(StockChanged(
                producto_id=ingreso.producto_id,
                bodega_id=ingreso.bodega_id,
                cantidad_delta=ingreso.cantidad,
                razon=f"Ingreso #{ingreso.id}"
            ))
            
            return ingreso


class RetiroSerializer(serializers.ModelSerializer):
    # Compatibilidad de payload legado: id_producto/id_usuario.
    id_producto = serializers.PrimaryKeyRelatedField(
        source='producto',
        queryset=Producto.objects.all(),
        write_only=True,
        required=False,
    )
    id_usuario = serializers.PrimaryKeyRelatedField(
        source='usuario',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Retiro
        fields = ['id', 'producto', 'usuario', 'bodega', 'cantidad', 'fecha', 'observacion', 'id_producto', 'id_usuario']
        read_only_fields = ['id', 'fecha']
        extra_kwargs = {
            'producto': {'required': False},
            'usuario': {'required': False},
        }

    def validate(self, data):
        if 'producto' not in data:
            raise serializers.ValidationError({'producto': 'Este campo es obligatorio.'})
        if 'usuario' not in data:
            raise serializers.ValidationError({'usuario': 'Este campo es obligatorio.'})

        producto = data['producto']
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

    def create(self, validated_data):
        from .domain.bus import bus
        from .domain.events import StockChanged
        
        with transaction.atomic():
            retiro = super().create(validated_data)
            
            # Publicar evento de retiro (negativo)
            bus.publish(StockChanged(
                producto_id=retiro.producto_id,
                bodega_id=retiro.bodega_id,
                cantidad_delta=-retiro.cantidad,
                razon=f"Retiro #{retiro.id}"
            ))
            
            return retiro

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
    usuario = serializers.PrimaryKeyRelatedField(read_only=True)
    usuario_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Envio
        fields = ['id', 'bodega_origen', 'bodega_destino', 'fecha', 'confirmado', 'detalles', 'usuario', 'usuario_username']
        read_only_fields = ['usuario']

    def validate(self, data):
        detalles = data.get('detalles', [])
        if self.instance is None and len(detalles) == 0:
            raise serializers.ValidationError(
                "Necesita al menos un producto en detalles"
            )

        return data

    def create(self, validated_data):
        from .domain.bus import bus
        from .domain.events import EnvioCreado, EnvioConfirmado
        
        detalles_data = validated_data.pop('detalles')
        with transaction.atomic():
            envio = Envio.objects.create(**validated_data)
            for detalle_data in detalles_data:
                EnvioDetalle.objects.create(envio=envio, **detalle_data)

            # 1. Notificar envío creado
            bus.publish(EnvioCreado(envio_id=envio.id))
            
            # 2. Si ya viene confirmado, procesar stock
            if envio.confirmado:
                bus.publish(EnvioConfirmado(envio_id=envio.id))
                
        return envio

    def update(self, instance, validated_data):
        from .domain.bus import bus
        from .domain.events import EnvioConfirmado
        
        if instance.confirmado and not validated_data.get('confirmado', True):
            raise serializers.ValidationError("No se puede desconfirmar un envío ya confirmado.")

        if instance.confirmado:
            raise serializers.ValidationError("No se puede modificar un envío confirmado.")

        was_confirmado = instance.confirmado
        detalles_data = validated_data.pop('detalles', None)

        with transaction.atomic():
            instance.bodega_origen = validated_data.get('bodega_origen', instance.bodega_origen)
            instance.bodega_destino = validated_data.get('bodega_destino', instance.bodega_destino)
            instance.confirmado = validated_data.get('confirmado', instance.confirmado)
            instance.save()

            if detalles_data is not None:
                instance.detalles.all().delete()
                for detalle_data in detalles_data:
                    EnvioDetalle.objects.create(envio=instance, **detalle_data)

            if not was_confirmado and instance.confirmado:
                # 3. Disparar confirmación
                bus.publish(EnvioConfirmado(envio_id=instance.id))

        return instance

    def get_usuario_username(self, obj):
        return getattr(obj.usuario, 'username', None)


class ImportJobSerializer(serializers.ModelSerializer):
    bodega = serializers.PrimaryKeyRelatedField(queryset=Bodega.objects.all())

    class Meta:
        model = ImportJob
        fields = ['id', 'usuario', 'bodega', 'filename', 'total_rows', 'created_at', 'finished_at', 'status', 'error_message']
        read_only_fields = ['id', 'usuario', 'filename', 'total_rows', 'created_at', 'finished_at', 'status', 'error_message']


class ImportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRow
        fields = ['id', 'import_job', 'row_number', 'nombre', 'cantidad', 'precio', 'producto', 'status', 'message']
        read_only_fields = ['id', 'import_job', 'producto', 'status', 'message']


class ImportUploadSerializer(serializers.Serializer):
    """
    Para el endpoint de carga:
    - bodega (id)
    - file (xlsx/xls/csv)
    """
    bodega = serializers.PrimaryKeyRelatedField(queryset=Bodega.objects.all())
    gerencia = serializers.PrimaryKeyRelatedField(queryset=Gerencia.objects.all())
    file = serializers.FileField()

    def validate_file(self, f):
        name = f.name.lower()
        if not (name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv')):
            raise serializers.ValidationError('Archivo debe ser .xlsx, .xls o .csv')
        if f.size > 25 * 1024 * 1024:
            raise serializers.ValidationError('Archivo demasiado grande (máx 25 MB)')
        return f
