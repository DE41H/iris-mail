from os import getenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_USER_MODEL = 'plugins.CustomUser'


# Security
SECRET_KEY = getenv('DJANGO_SECRET_KEY', 'django-insecure-)qpo_w^=h(#0$emn@-%z+90!g0rva&pkxs1e!6x&ch90qxs4*y')
DEBUG = getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [ host.strip() for host in getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') ]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'procrastinate.contrib.django',
    'plugins',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cfg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cfg.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('POSTGRES_DB', 'name'),
        'USER': getenv('POSTGRES_USER', 'user'),
        'PASSWORD': getenv('POSTGRES_PASSWORD', 'password'),
        'HOST': 'db',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}


# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': getenv('VALKEY_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django.core.cache.backends.redis.PyRedisClient',
        }
    }
}


# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# Staticfiles
STATIC_URL = 'static/'


# Email
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
