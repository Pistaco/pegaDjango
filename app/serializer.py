from rest_framework import serializers
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class ProductoStockSerializer(serializers.ModelSerializer):
    stock = serializers.IntegerField(source='stock.cantidad', read_only=True)
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


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class StockActualSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockActual
        fields = '__all__'