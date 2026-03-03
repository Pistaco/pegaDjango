from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload, EnvioDetalle, Envio, \
    Bodega, Familia, Notificacion, Pendiente, ImportJob, ImportRow


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
    familia = serializers.CharField(source="producto.familia.nombre", read_only=True)
    cantidad_en_stock = serializers.IntegerField(source="cantidad", read_only=True)

    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    producto_codigo_barras = serializers.CharField(source="producto.codigo_barras", read_only=True)
    producto_parte = serializers.IntegerField(source="producto.parte", read_only=True)
    producto_descripcion = serializers.CharField(source="producto.descripcion", read_only=True)
    producto_precio = serializers.IntegerField(source="producto.precio", read_only=True)
    producto_familia = serializers.CharField(source="producto.familia.nombre", read_only=True)
    producto_familia_id = serializers.IntegerField(source="producto.familia.id", read_only=True)
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
            "familia",
            "cantidad_en_stock",
            "producto_nombre",
            "producto_codigo_barras",
            "producto_parte",
            "producto_descripcion",
            "producto_precio",
            "producto_familia",
            "producto_familia_id",
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


    def validate(self, attrs):
        parent = attrs.get('parent')
        instance = getattr(self, 'instance', None)
        if instance and parent and parent.id == instance.id:
            raise serializers.ValidationError("Una familia no puede ser su propio padre.")
        return attrs

    def get_ruta_completa(self, obj):
        return obj.get_ruta_completa()

class IngresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingreso
        fields = '__all__'

    def create(self, validated_data):
        producto = validated_data['id_producto']
        bodega = validated_data['bodega']
        cantidad_ingreso = validated_data['cantidad']

        if cantidad_ingreso <= 0:
            raise serializers.ValidationError({"cantidad": "Debe ser mayor a cero."})

        with transaction.atomic():
            stock = (
                StockActual.objects
                .select_for_update()
                .filter(producto=producto, bodega=bodega)
                .first()
            )
            if stock is None:
                StockActual.objects.create(
                    producto=producto,
                    bodega=bodega,
                    cantidad=cantidad_ingreso,
                )
            else:
                stock.cantidad += cantidad_ingreso
                stock.save(update_fields=['cantidad', 'actualizado_en'])

            return super().create(validated_data)


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

    def create(self, validated_data):
        producto = validated_data['id_producto']
        bodega = validated_data['bodega']
        cantidad_retirar = validated_data['cantidad']

        if cantidad_retirar <= 0:
            raise serializers.ValidationError({"cantidad": "Debe ser mayor a cero."})

        with transaction.atomic():
            try:
                stock = (
                    StockActual.objects
                    .select_for_update()
                    .get(producto=producto, bodega=bodega)
                )
            except StockActual.DoesNotExist:
                raise serializers.ValidationError(
                    {"bodega": "No hay stock de este producto en la bodega seleccionada."}
                )

            if cantidad_retirar > stock.cantidad:
                raise serializers.ValidationError(
                    {"cantidad": "No hay suficiente stock para este retiro."}
                )

            stock.cantidad -= cantidad_retirar
            if stock.cantidad == 0:
                stock.delete()
            else:
                stock.save(update_fields=['cantidad', 'actualizado_en'])

            return super().create(validated_data)

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["username"]

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

    def _obtener_requerimientos_envio(self, envio):
        return list(
            envio.detalles
            .values('producto_id')
            .annotate(cantidad=Sum('cantidad'))
            .order_by('producto_id')
        )

    def _aplicar_movimiento_confirmacion(self, envio):
        req = self._obtener_requerimientos_envio(envio)
        if not req:
            raise serializers.ValidationError(
                "Necesita al menos un producto en detalles para confirmar el envío."
            )

        origen_id = envio.bodega_origen_id
        destino_id = envio.bodega_destino_id
        ahora = timezone.now()

        requeridas = {item['producto_id']: int(item['cantidad']) for item in req}
        producto_ids = list(requeridas.keys())

        stock_origen = {
            s.producto_id: s
            for s in StockActual.objects.select_for_update().filter(
                bodega_id=origen_id,
                producto_id__in=producto_ids,
            )
        }

        hay_faltantes = any(
            stock_origen.get(producto_id) is None or stock_origen[producto_id].cantidad < cantidad_req
            for producto_id, cantidad_req in requeridas.items()
        )
        if hay_faltantes:
            raise serializers.ValidationError(
                f"Stock insuficiente en la bodega de origen para uno o más productos del envío {envio.id}."
            )

        for producto_id, cantidad_req in requeridas.items():
            row_origen = stock_origen[producto_id]
            row_origen.cantidad -= cantidad_req
            row_origen.actualizado_en = ahora
            row_origen.save(update_fields=['cantidad', 'actualizado_en'])

        stock_destino = {
            s.producto_id: s
            for s in StockActual.objects.select_for_update().filter(
                bodega_id=destino_id,
                producto_id__in=producto_ids,
            )
        }
        for producto_id, cantidad_req in requeridas.items():
            row_destino = stock_destino.get(producto_id)
            if row_destino is None:
                StockActual.objects.create(
                    producto_id=producto_id,
                    bodega_id=destino_id,
                    cantidad=cantidad_req,
                    actualizado_en=ahora,
                )
                continue

            row_destino.cantidad += cantidad_req
            row_destino.actualizado_en = ahora
            row_destino.save(update_fields=['cantidad', 'actualizado_en'])

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        with transaction.atomic():
            envio = Envio.objects.create(**validated_data)
            for detalle_data in detalles_data:
                EnvioDetalle.objects.create(envio=envio, **detalle_data)

            if envio.confirmado:
                self._aplicar_movimiento_confirmacion(envio)
        return envio

    def update(self, instance, validated_data):
        if instance.confirmado and not validated_data.get('confirmado', True):
            raise serializers.ValidationError("No se puede desconfirmar un envío ya confirmado.")

            # Permitir solo editar si no está confirmado
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
                self._aplicar_movimiento_confirmacion(instance)

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
    familia = serializers.PrimaryKeyRelatedField(queryset=Familia.objects.all())
    file = serializers.FileField()

    def validate_file(self, f):
        name = f.name.lower()
        if not (name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv')):
            raise serializers.ValidationError('Archivo debe ser .xlsx, .xls o .csv')
        if f.size > 25 * 1024 * 1024:
            raise serializers.ValidationError('Archivo demasiado grande (máx 25 MB)')
        return f
