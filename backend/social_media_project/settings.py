"""
Django settings for social_media_project project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import sys
from datetime import timedelta
from pathlib import Path
from decouple import Csv, config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")
# used to secure =, session, etc. with Signer class

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", cast=bool)
# cannot be True in hosted environment
# if DEBUG is True, then the static files can be accessed from the browser

# it has meaning when DEBUG is False otherwise it is ignored
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())


# Application definition

DEFAULT_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "drf_spectacular_sidecar",  # required for Django collectstatic discovery
    "django_extensions",
    "rest_framework_simplejwt.token_blacklist",
    "drf_queryfields",
    "django_prometheus",
    "django_redis",
    "channels",
]

LOCAL_APPS = [
    "users_app.apps.UsersAppConfig",
    "posts_app.apps.PostsAppConfig",
    "notifications_app.apps.NotificationsAppConfig",
]

INSTALLED_APPS = LOCAL_APPS + DEFAULT_APPS + THIRD_PARTY_APPS

# customizing user model
AUTH_USER_MODEL = "users_app.User"

SHELL_PLUS = "ipython"

SITE_ID = 1

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

PROMETHEUS_LATENCY_BUCKETS = (
    0.1,
    0.2,
    0.5,
    0.6,
    0.8,
    1.0,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    7.5,
    9.0,
    12.0,
    15.0,
    20.0,
    30.0,
    float("inf"),
)

PROMETHEUS_EXPORT_MIGRATIONS = False  # to avoid migrations dependencies

ROOT_URLCONF = "social_media_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "social_media_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        # "ENGINE": "django.db.backends.sqlite3",
        # "NAME": BASE_DIR / "db.sqlite3",
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": "localhost",
        "PORT": 5432,
    }
}

SPECTACULAR_SETTINGS = {
    "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "PARSER_WHITELIST": ["rest_framework.parsers.JSONParser"],
    # OTHER SETTINGS
    "TITLE": "Social Media API",
    "DESCRIPTION": "This API is made with django and rest framework to simulate social media applications",
    "AUTHOR": "Social Media API",
    "VERSION": "1.0.0 (v1)",
    "LICENSE": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    "CONTACT": {
        "name": "Author ",
        "email": "motasemalmobayyed@gmail.com",
    },
    "EXTERNAL_DOCS": {
        "url": "https://github.com/Motasem20007204978/Social_Media_API",
        "description": "Social Media API Source Code",
    },
    "SORT_OPERATIONS": False,
    "SORT_OPERATION_PARAMETERS": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "SERVERS": [
        {"url": "http://localhost:5000", "description": "API Server"},
        {
            "url": "http://localhost:5555",
            "description": "Flower Server For Executed Tasks",
        },
        {
            "url": "http://localhost:9090",
            "description": "Prometheus Server For Monitoring Requests",
        },
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "GENERIC_ADDITIONAL_PROPERTIES": "dict",
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "SWAGGER_UI_SETTINGS": {
        "url": "/schema",  # relative path
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=10),
    "UPDATE_LAST_LOGIN": True,  # for TokenObtainBairView
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    # create new refresh and access token with RefrshTokenview and blacklist the old
    # "ROTATE_REFRESH_TOKENS": True,
    # "BLACKLIST_AFTER_ROTATION": True,
}

# celery settings
CELERY_BROKER_URL = "redis://"
CELERY_RESULT_BACKEND = "redis://"  # for caching
CELERY_TIMEZONE = "Asia/Gaza"

# redis (remote dictionary server) for caching
CHACHE = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "MAX_ENTRIES": 2000,
        },
        "KEY_PREFIX": "API",
    }
}
# to make redis does not interfere with django admin panel and current session
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    }
}


WSGI_APPLICATION = "social_media_project.wsgi.application"

ASGI_APPLICATION = "social_media_project.routing.application"

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# email verification requirements
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_ID")
EMAIL_HOST_PASSWORD = config("EMAIL_PW")

# the alias email instead of my emial
DEFAULT_FROM_EMAIL = "noreply<no_reply@domain.com>"


# Social Media Configs
GOOGLE_CLIENT_KEY = config("GOOGLE_CLIENT_KEY")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET")
GOOGLE_CALLBACK_URI = "http://localhost:5000/api/v1/google/callback"

TWITTER_CLIENT_KEY = config("TWITTER_CLIENT_KEY")
TWITTER_CLIENT_SECRET = config("TWITTER_CLIENT_SECRET")
TWITTER_CALLBACK_URI = "http://localhost:5000/api/v1/twitter/callback"

LOGIN_WITH_SOCIAL_MEDIA_PASS = config("LOGIN_WITH_SOCIAL_MEDIA_PASS")

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "assets", "static")]
# to collect static files in host machine
# cammoand: python manage.py collectstatic

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# activation link using default django token generator in seconds
PASSWORD_RESET_TIMEOUT = 4000

# https://medium.com/@arnopretorius/django-web-application-security-checklist-64bfe2438a29

# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True

# SECURE_HSTS_SECONDS = 86400
# SECURE_HSTS_PRELOAD = True
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# SECURE_SSL_REDIRECT = True
