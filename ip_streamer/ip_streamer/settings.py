import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-rw2i5#ic3wsrc!poi4s8ds*fb*%x*lhz%3h9!4d9ti+!+yhm6&",
)

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ip_streamer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "ip_streamer.wsgi.application"
ASGI_APPLICATION = "ip_streamer.asgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "national_id_db"),
        "USER": os.getenv("POSTGRES_USER", "admin"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "admin123"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en-us")

TIME_ZONE = os.getenv("TIME_ZONE", "UTC")

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
PROJECT_STATIC_DIR = BASE_DIR / "static"
if PROJECT_STATIC_DIR.exists():
    STATICFILES_DIRS.append(PROJECT_STATIC_DIR)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Africa/Cairo")

REDIS_URL = os.getenv("REDIS_URL", CELERY_BROKER_URL)


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_CACHE_LOCATION", "redis://redis:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 1000,
        },
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "api_key": os.getenv("DEFAULT_THROTTLE_RATE", "10/minute"),
        "api_key_daily": os.getenv("DEFAULT_THROTTLE_RATE_DAILY", "100/day"),
    },
}


IPINFO_BASE_URL = os.getenv("IPINFO_BASE_URL", "https://ipinfo.io")
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")
IPINFO_HTTP_TIMEOUT_SECONDS = float(os.getenv("IPINFO_HTTP_TIMEOUT_SECONDS", "10"))
IP_LOOKUP_CACHE_TTL_SECONDS = int(os.getenv("IP_LOOKUP_CACHE_TTL_SECONDS", "10"))
IP_LOOKUP_JOB_TTL_SECONDS = int(os.getenv("IP_LOOKUP_JOB_TTL_SECONDS", "3600"))
IP_LOOKUP_SSE_HEARTBEAT_SECONDS = int(
    os.getenv("IP_LOOKUP_SSE_HEARTBEAT_SECONDS", "15")
)
IP_LOOKUP_SSE_MAX_IDLE_SECONDS = int(
    os.getenv("IP_LOOKUP_SSE_MAX_IDLE_SECONDS", str(IP_LOOKUP_JOB_TTL_SECONDS))
)
