"""Shared Django settings used by all environments."""

from pathlib import Path
import os
import sys

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

sendgrid_env_path = BASE_DIR / "sendgrid.env"
if not os.getenv("SENDGRID_API_KEY") and sendgrid_env_path.exists():
    load_dotenv(sendgrid_env_path, encoding="utf-16")

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0:8000", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts",
    "inventory",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.RequestLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ims_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ims_backend.wsgi.application"

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

POSTGRES_TEST_USER = os.getenv("POSTGRES_TEST_USER", "test_user")
POSTGRES_TEST_PASSWORD = os.getenv("POSTGRES_TEST_PASSWORD", "test")

if "test" in sys.argv:
    POSTGRES_USER = POSTGRES_TEST_USER
    POSTGRES_PASSWORD = POSTGRES_TEST_PASSWORD

if not (POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD):
    raise RuntimeError(
        "PostgreSQL configuration is required. "
        "Set POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD in your environment."
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    }
}

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = ["*"]
CORS_ALLOW_METHODS = ["*"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",
        "register": "10/hour",
        "password_reset": "5/hour",
        "token_refresh": "30/minute",
        "inventory_write": "60/hour",
        "profile": "120/hour",
    },
}

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")
ADMIN_PANEL_URL = os.getenv(
    "ADMIN_PANEL_URL", "http://localhost:8000/admin/inventory/inventoryitem/"
)
PASSWORD_RESET_CODE_EXPIRY_MINUTES = int(
    os.getenv("PASSWORD_RESET_CODE_EXPIRY_MINUTES", "10")
)

AUTH_USER_MODEL = "accounts.User"
