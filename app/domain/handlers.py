from django.db import transaction
from .events import StockChanged, EnvioCreado, EnvioConfirmado
import logging

logger = logging.getLogger(__name__)

def handle_stock_change(event: StockChanged):
    """Maneja cualquier cambio de stock (ingreso, retiro, envío).
    Centraliza la regla de: SI EL STOCK ES 0, SE ELIMINA LA FILA.
    """
    from app.models import StockActual
    
    with transaction.atomic():
        stock, created = StockActual.objects.select_for_update().get_or_create(
            producto_id=event.producto_id,
            bodega_id=event.bodega_id,
            defaults={'cantidad': 0}
        )
        
        # Aplicar el cambio
        stock.cantidad += event.cantidad_delta
        
        if stock.cantidad < 0:
            raise ValueError(f"Stock insuficiente para producto {event.producto_id} en bodega {event.bodega_id}")
            
        if stock.cantidad == 0:
            logger.info(f"Stock del producto {event.producto_id} llegó a 0 en bodega {event.bodega_id}. Eliminando registro.")
            stock.delete()
        else:
            stock.save()

def handle_envio_creado_notif(event: EnvioCreado):
    """Crea notificaciones para la bodega destino cuando se crea un envío."""
    from app.models import Envio, Notificacion
    
    envio = Envio.objects.select_related('bodega_destino').get(id=event.envio_id)
    usuarios_destino = envio.bodega_destino.usuarios.all()
    
    notificaciones = [
        Notificacion(
            usuario=usuario,
            titulo='Envío en camino',
            mensaje=f'Se ha creado un nuevo envío hacia tu bodega. Ver: /envios/{envio.id}',
            envio=envio,
        )
        for usuario in usuarios_destino
    ]
    Notificacion.objects.bulk_create(notificaciones)

def handle_envio_confirmado(event: EnvioConfirmado):
    """Dispara los movimientos de stock cuando se confirma un envío."""
    from app.models import Envio, EnvioDetalle
    from .bus import bus
    
    envio = Envio.objects.get(id=event.envio_id)
    detalles = EnvioDetalle.objects.filter(envio=envio)
    
    for detalle in detalles:
        # Descontar de origen
        bus.publish(StockChanged(
            producto_id=detalle.producto_id,
            bodega_id=envio.bodega_origen_id,
            cantidad_delta=-detalle.cantidad,
            razon=f"Envio {envio.id} confirmado (salida)"
        ))
        # Aumentar en destino
        bus.publish(StockChanged(
            producto_id=detalle.producto_id,
            bodega_id=envio.bodega_destino_id,
            cantidad_delta=detalle.cantidad,
            razon=f"Envio {envio.id} confirmado (entrada)"
        ))
