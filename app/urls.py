from django.urls import path, include
from rest_framework import routers
from .views import CargoViewSet, ProductoViewSet, IngresoViewSet, RetiroViewSet, UsuarioViewSet, StockViewSet, \
    ProductoStockViewSet, UserViewSet, EnvioViewSet, Envio, EnvioDetalleViewSet, BodegaViewSet, EnvioAnidadoViewSet, \
    StockDeMiBodegaViewSet, ProductosEnMiBodegaViewSet, StockBajoStockViewSet, StockDeMiBodegaBajoStockViewSet, \
    FamiliaViewSet, NotificacionViewSet, PendienteViewSet, ProductoEnvioViewSet, ProductoViewSetReferenceInput, \
    BodegaTodasViewSet, ProductoInventarioViewSet

router = routers.DefaultRouter()
router.register(r'cargos', CargoViewSet)

router.register(r'productos/porBodega', ProductoInventarioViewSet, basename='productos-por-bodega')
router.register(r'productos/referenceFields', ProductoViewSetReferenceInput, basename='productos-referenceFields')
router.register('productos/envios', ProductoEnvioViewSet, basename='productos-envio')
router.register('productos/mi-bodega', ProductosEnMiBodegaViewSet, basename='productos-mi-bodega')


router.register(r'productos', ProductoViewSet)

router.register(r'familias', FamiliaViewSet)
router.register(r'ingresos', IngresoViewSet)
router.register(r'retiros', RetiroViewSet)
router.register(r'usuarios', UsuarioViewSet)

router.register(r'notificaciones', NotificacionViewSet, basename='notificaciones')

router.register(r'pendientes', PendienteViewSet, basename='pendiente')

router.register(r'users', UserViewSet)
router.register('stock/mi-bodega/bajo_stock', StockDeMiBodegaBajoStockViewSet, basename='stock-mi-bodega-bajo-stock')
router.register('stock/mi-bodega', StockDeMiBodegaViewSet, basename='stock-mi-bodega')
router.register(r'stock/bajo_stock', StockBajoStockViewSet, basename='stock-bajo-stock')
router.register(r'stock', StockViewSet)



router.register(r'envios', EnvioViewSet)
router.register(r'enviosAnidados', EnvioAnidadoViewSet, basename='enviosAnidados')
router.register(r'envio_detalles', EnvioDetalleViewSet)
router.register(r'bodegas/todas', BodegaTodasViewSet, basename='bodegas-todas')
router.register(r'bodegas', BodegaViewSet)

router.register(r'productosStock', ProductoStockViewSet, basename='productosStock')


urlpatterns = [
    path('', include(router.urls)),
]
