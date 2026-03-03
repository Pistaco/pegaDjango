from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Envio, Notificacion


@receiver(post_save, sender=Envio)
def crear_notificacion_envio_en_camino(sender, instance, created, **kwargs):
    if not created:
        return

    usuarios_destino = instance.bodega_destino.usuarios.all()
    if not usuarios_destino.exists():
        return

    notificaciones = [
        Notificacion(
            usuario=usuario,
            titulo='Envío en camino',
            mensaje=f'Se ha creado un nuevo envío hacia tu bodega. Ver: /envios/{instance.id}',
            envio=instance,
        )
        for usuario in usuarios_destino
    ]
    Notificacion.objects.bulk_create(notificaciones)
