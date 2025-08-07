import os

print("cargado")
# Determinar qué configuración usar basado en variable de entorno
environment = os.environ.get('DJANGO_ENV', 'local')

if environment == 'production':
    from .production import *
else:
    from .local import *