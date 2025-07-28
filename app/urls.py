from django.urls import path, include
from rest_framework import routers
from .views import CargoViewSet, ProductoViewSet, IngresoViewSet, RetiroViewSet, UsuarioViewSet, StockViewSet, ProductoStockViewSet

router = routers.DefaultRouter()
router.register(r'cargos', CargoViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'ingresos', IngresoViewSet)
router.register(r'retiros', RetiroViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'stock', StockViewSet)

router.register(r'productosStock', ProductoStockViewSet, basename='productosStock')


urlpatterns = [
    path('', include(router.urls)),
]
