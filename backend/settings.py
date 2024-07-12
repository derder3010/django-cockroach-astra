import os
from datetime import timedelta
from pathlib import Path
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('DJ_SECRET_KEY')

DEBUG = config("DEBUG")

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'storages',
    'django_cockroachdb',
    'api.apps.ApiConfig',
]

INSTALLED_APPS = ['django_cassandra_engine'] + INSTALLED_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

CORS_ALLOWED_ORIGINS = ["*"]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
CSRF_TRUSTED_ORIGINS = ["*"]


MIDDLEWARE = [
    'api.middleware.TokenBlacklistMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.AnonymousSessionMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django_cockroachdb',
        'NAME': config('CRD_DB_NAME'),
        'USER': config('CRD_USER'),
        'PASSWORD': config('CRD_PASS'),
        'HOST': config('CRD_HOST'),
        'PORT': config('CRD_PORT'),
        'OPTIONS': {
            'sslmode': 'verify-full',
            'sslrootcert': config('CRD_SSLROOTCERT_FILE'),
        },
    },
    'cassandra': {
        'ENGINE': 'django_cassandra_engine',
        'NAME': config('KEYSPACE_NAME'),
        'OPTIONS': {
            'connection': {
                'consistency': ConsistencyLevel.LOCAL_QUORUM,
                'retry_connect': True,
                'auth_provider': PlainTextAuthProvider("token", config('TOKEN')),
                'cloud': {
                    'secure_connect_bundle': config('SECURE_CONNECT_FILE_PATH')
                }
            },
            'session': {
                'default_timeout': 30,
                'default_fetch_size': 10000
            }
        },
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('LOCATION_URL'),
    }
}



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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('BUCKET_NAME')
AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.r2.cloudflarestorage.com/static/'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.r2.cloudflarestorage.com/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CASSANDRA_FALLBACK_ORDER_BY_PYTHON = True
