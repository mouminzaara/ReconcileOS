"""
Django settings for ReconcileOS project.

Generated for ReconcileOS - Continuous Integrity & Self-Healing Platform.
"""

import os
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# Core deployment mode
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

INSECURE_DEV_SECRET = 'django-insecure-reconcileos-dev-key-milestone1-change-in-production'
SECRET_KEY = os.getenv('SECRET_KEY', INSECURE_DEV_SECRET if DEBUG else '')

# In production mode (DEBUG=False), fail safely if required cryptographic configuration is missing
if not DEBUG:
    if not SECRET_KEY or SECRET_KEY == INSECURE_DEV_SECRET or SECRET_KEY.startswith('django-insecure-'):
        raise ImproperlyConfigured(
            "SECRET_KEY must be set to a unique, cryptographically secure value in production (DEBUG=False). "
            "Insecure defaults prefixed with 'django-insecure-' are prohibited."
        )

# Allowed Hosts configuration
env_allowed_hosts = os.getenv('ALLOWED_HOSTS')
if env_allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in env_allowed_hosts.split(',') if host.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
else:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must be explicitly defined in environment variables when DEBUG=False."
    )


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
]

LOCAL_APPS = [
    'apps.accounts.apps.AccountsConfig',
    'apps.employees.apps.EmployeesConfig',
    'apps.connectors.apps.ConnectorsConfig',
    'apps.rules.apps.RulesConfig',
    'apps.reconciliation.apps.ReconciliationConfig',
    'apps.workflows.apps.WorkflowsConfig',
    'apps.approvals.apps.ApprovalsConfig',
    'apps.audit.apps.AuditConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reconcileos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'reconcileos.wsgi.application'
ASGI_APPLICATION = 'reconcileos.asgi.application'


# Database Configuration
# Supports DATABASE_URL (12-factor format) or individual DB_* variables.
# Preserves SQLite as default for local development and test suite integrity.

DATABASE_URL = os.getenv('DATABASE_URL')
DB_ENGINE = os.getenv('DB_ENGINE', '').lower()

if DATABASE_URL:
    parsed_db = urlparse(DATABASE_URL)
    is_postgres = parsed_db.scheme in ('postgres', 'postgresql')
    if is_postgres:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed_db.path.lstrip('/') or 'reconcileos_db',
                'USER': unquote(parsed_db.username or ''),
                'PASSWORD': unquote(parsed_db.password or ''),
                'HOST': parsed_db.hostname or 'localhost',
                'PORT': str(parsed_db.port or 5432),
                'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600' if not DEBUG else '0')),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
elif DB_ENGINE in ('postgres', 'postgresql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'reconcileos_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600' if not DEBUG else '0')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images) & Production WhiteNoise
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage" if not DEBUG else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY', SECRET_KEY),
}

# CORS & CSRF Configuration
# Wildcard CORS is prohibited in production
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True').lower() in ('true', '1', 't')
else:
    CORS_ALLOW_ALL_ORIGINS = False

DEFAULT_ORIGINS = 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173'
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', DEFAULT_ORIGINS).split(',') if origin.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', DEFAULT_ORIGINS).split(',') if origin.strip()
]


# Production HTTPS & Cookie Security Configuration
# Controlled via ENABLE_HTTPS; avoids breaking local HTTP development
ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', 'False' if DEBUG else 'True').lower() in ('true', '1', 't')

SECURE_SSL_REDIRECT = ENABLE_HTTPS and not DEBUG
SESSION_COOKIE_SECURE = ENABLE_HTTPS and not DEBUG
CSRF_COOKIE_SECURE = ENABLE_HTTPS and not DEBUG

SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if ENABLE_HTTPS and not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() in ('true', '1', 't')
    SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True').lower() in ('true', '1', 't')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
