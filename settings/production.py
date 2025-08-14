from .base import *

print("cargado")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hosts permitidos - CRÍTICO para seguridad
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# CSRF trusted origins para AJAX requests
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
# Database configuration
# Opción A: PostgreSQL en cPanel
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',  # opcional si usas cookies
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    "SEARCH_PARAM": "q",
    'DEFAULT_PAGINATION_CLASS': 'app.pagination.RADefaultPagination',
    "PAGE_SIZE": 25
}


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'cpanel_user_dbname',     # Formato: usuario_nombredb
#         'USER': 'cpanel_user_dbuser',     # Formato: usuario_nombreusuario
#         'PASSWORD': 'password_seguro',
#         'HOST': 'localhost',
#         'PORT': '5432',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#     }
# }

# Opción B: Database URL (para proveedores externos con SSL)
# if os.environ.get('DATABASE_URL'):
#     DATABASES['default'] = dj_database_url.parse(
#         os.environ.get('DATABASE_URL'),
#         conn_max_age=600,
#         conn_health_checks=True,
#     )
#     # SSL obligatorio para conexiones externas
#     if 'neon.tech' in os.environ.get('DATABASE_URL', '') or 'aiven.io' in os.environ.get('DATABASE_URL', ''):
#         DATABASES['default']['OPTIONS'] = {
#             'sslmode': 'require',
#         }

# Security settings - HTTPS obligatorio
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# HSTS settings - Configurar después de verificar SSL
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy básico
# Ajustar según necesidades específicas de React Admin
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'", "data:")
CSP_IMG_SRC = ("'self'", "data:", "https:")

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Admin URL segura (usar variable de entorno)
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')

# Email configuration (ajustar según proveedor)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Cache configuration (opcional - Redis en VPS)
if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
