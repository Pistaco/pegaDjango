from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload


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
        cantidad_retirar = data['cantidad']
        stock_actual = producto.stock.cantidad  # Asumiendo relación OneToOne con Stock

        if cantidad_retirar == 0:
            raise serializers.ValidationError( {"cantidad": "no puede ser zero"})

        if cantidad_retirar > stock_actual:
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