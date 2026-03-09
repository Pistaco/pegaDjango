import os
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Cambia a 'production' para el entorno real.
# En desarrollo puedes dejarlo vacío o poner 'development'.
ENV = os.getenv('DJANGO_ENV', 'development')

if ENV == 'development':
    from .dev import *
else:
    from .prod import *
