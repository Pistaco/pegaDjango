import os
import sys
from django.core.wsgi import get_wsgi_application

# Agregar el directorio del proyecto al Python path
sys.path.append(os.getcwd())

# Configurar Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Configurar variables de entorno para producción
os.environ['DJANGO_ENV'] = 'production'
os.environ['DB_NAME'] = 'cpanelusername_myproject_db'
os.environ['DB_USER'] = 'cpanelusername_myproject_user'
os.environ['DB_PASSWORD'] = 'tu_password_db'
os.environ['DJANGO_SECRET_KEY'] = 'tu-secret-key-produccion'

application = get_wsgi_application()