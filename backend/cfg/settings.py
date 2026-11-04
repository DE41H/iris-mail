from os import getenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_USER_MODEL = 'plugins.CustomUser'


# Security
DEBUG = getenv('DJANGO_DEBUG', 'False') == 'True'
SECRET_KEY = getenv('DJANGO_SECRET_KEY') or ('django-insecure-dev-only-key' if DEBUG else None)
ALLOWED_HOSTS = [ host.strip() for host in getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') ]
CSRF_TRUSTED_ORIGINS = [ origin.strip() for origin in getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip() ]

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 3600
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if getenv('DJANGO_BEHIND_PROXY') == 'True' else None
ALLAUTH_TRUSTED_PROXY_COUNT = 1 if getenv('DJANGO_BEHIND_PROXY') == 'True' else 0


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'procrastinate.contrib.django',
    'cacheops',
    'rest_framework',
    'drf_spectacular',
    'plugins',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cfg.middleware.SecurityHeaders',
]

ROOT_URLCONF = 'cfg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
        'HOST': getenv('POSTGRES_HOST', 'db'),
        'PORT': getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}


# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': getenv('VALKEY_URL', 'redis://127.0.0.1:6379/1'),
    }
}

CACHEOPS_REDIS = getenv('CACHEOPS_URL', 'redis://127.0.0.1:6379/2')
CACHEOPS_DEGRADE_ON_FAILURE = True
CACHEOPS_DEFAULTS = {'timeout': 60 * 15}
CACHEOPS = {
    'plugins.customuser': {'ops': 'all'},
    'plugins.plugin': {'ops': 'all'},
    'plugins.subscription': {'ops': 'all'},
    'plugins.result': {'ops': ()},
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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']


# Auth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
LOGIN_REDIRECT_URL = '/plugins'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': getenv('GOOGLE_CLIENT_ID', ''),
            'secret': getenv('GOOGLE_CLIENT_SECRET', ''),
        },
        'SCOPE': [
            'profile',
            'email',
            'https://www.googleapis.com/auth/gmail.readonly',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'consent',
        },
    },
}


# REST framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'plugins.throttling.PluginKeyThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '500/hour',
        'user': '200/minute'
    },
    'DEFAULT_PAGINATION_CLASS': 'plugins.pagination.UUIDCursorPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Iris API',
    'DESCRIPTION': 'Plugin endpoints authenticate with `Authorization: Bearer <api key>`.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # Documented endpoints are the plugin API, so hide session auth from the docs.
    'AUTHENTICATION_WHITELIST': ['plugins.authentication.PluginKeyAuthentication'],
}


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'json': {
        '()': 'pythonjsonlogger.json.JsonFormatter',
        'fmt': ['levelname', 'name', 'message'],
        'rename_fields': {'levelname': 'level', 'name': 'logger', 'exc_info': 'exception'},
        'timestamp': 'time',
    }},
    'handlers': {'json': {'class': 'logging.StreamHandler', 'formatter': 'json'}},
    'root': {'handlers': ['json'], 'level': 'INFO'},
    'loggers': {name: {'handlers': [], 'propagate': True} for name in ('django', 'django.server')},
}
