from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual
from .serializer import CargoSerializer, ProductoSerializer, IngresoSerializer, RetiroSerializer, UsuarioSerializer, \
    StockActualSerializer, ProductoStockSerializer


class BodegueroNOT(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_active and not request.user.groups.filter(name='Bodeguero').exists():
            return True
        return False

class BodegueroYES(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and  request.user.is_active:
            if request.user.groups.filter(name='Bodeguero').exists():
                if request.method == 'POST':
                    return True
                else:
                    return False
            return True


class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [BodegueroNOT]

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [BodegueroNOT]

class ProductoStockViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('stock').all()
    serializer_class = ProductoStockSerializer
    permission_classes = [BodegueroNOT]
class IngresoViewSet(viewsets.ModelViewSet):
    queryset = Ingreso.objects.all()
    serializer_class = IngresoSerializer
    permission_classes = [BodegueroYES]

class RetiroViewSet(viewsets.ModelViewSet):
    queryset = Retiro.objects.all()
    serializer_class = RetiroSerializer
    permission_classes = [BodegueroYES]

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [BodegueroNOT]

class StockViewSet(viewsets.ModelViewSet):
    queryset = StockActual.objects.all()
    serializer_class = StockActualSerializer
    permission_classes = [BodegueroNOT]
