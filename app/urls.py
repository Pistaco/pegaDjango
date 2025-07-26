from django.urls import path, include
from rest_framework import routers
from .views import CargoViewSet, ProductoViewSet, IngresoViewSet, RetiroViewSet, UsuarioViewSet

router = routers.DefaultRouter()
router.register(r'cargos', CargoViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'ingresos', IngresoViewSet)
router.register(r'retiros', RetiroViewSet)
router.register(r'usuarios', UsuarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
