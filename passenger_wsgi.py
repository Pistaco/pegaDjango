#!/usr/bin/env python3
"""
Passenger WSGI file para Django en cPanel
Configuración robusta con manejo de errores
"""
import sys
import os
from pathlib import Path

# Configurar rutas del proyecto
CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR
sys.path.insert(0, str(PROJECT_ROOT))

# Agregar directorio padre si es necesario
sys.path.insert(0, str(PROJECT_ROOT.parent))

# Configurar variable de entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

try:
    # Cargar variables de entorno desde .env si existe
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # Importar aplicación Django
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

except ImportError as e:
    # Logging de errores para debugging
    import traceback
    with open(PROJECT_ROOT.parent / 'logs' / 'passenger_error.log', 'a') as f:
        f.write(f"Import Error: {e}\n")
        f.write(traceback.format_exc())
        f.write(f"Python Path: {sys.path}\n")
        f.write(f"Current Dir: {CURRENT_DIR}\n")
    raise
except Exception as e:
    # Cualquier otro error
    import traceback
    with open(PROJECT_ROOT.parent / 'logs' / 'passenger_error.log', 'a') as f:
        f.write(f"General Error: {e}\n")
        f.write(traceback.format_exc())
    raise

# Verificación de configuración (solo para debugging)
if __name__ == "__main__":
    print("Passenger WSGI configurado correctamente")
    print(f"Directorio del proyecto: {PROJECT_ROOT}")
    print(f"Python path: {sys.path}")