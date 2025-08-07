from celery import shared_task
from django.db import connection

@shared_task
def ejecutar_funcion_pendientes():
    with connection.cursor() as cursor:
        cursor.execute("SELECT generar_notificaciones_pendientes_atrasados();")
