import os

from .base import *


def env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


SECRET_KEY = env_required('SECRET_KEY')
DEBUG = False

allowed_hosts_values = env_list('DJANGO_ALLOWED_HOSTS', 'ALLOWED_HOSTS')
if not allowed_hosts_values:
    raise RuntimeError('Missing required environment variable: DJANGO_ALLOWED_HOSTS or ALLOWED_HOSTS')
ALLOWED_HOSTS = normalize_hosts(allowed_hosts_values)

cors_allowed_origins = env_list('CORS_ALLOWED_ORIGINS')
if cors_allowed_origins:
    CORS_ALLOWED_ORIGINS = cors_allowed_origins
else:
    CORS_ALLOW_ALL_ORIGINS = False

csrf_trusted_origins = env_list('CSRF_TRUSTED_ORIGINS')
if csrf_trusted_origins:
    CSRF_TRUSTED_ORIGINS = csrf_trusted_origins

CORS_ALLOW_CREDENTIALS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env_required('DB_NAME'),
        'USER': env_required('DB_USER'),
        'PASSWORD': env_required('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
