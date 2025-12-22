from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Support for reverse proxy (Traefik) - trust X-Forwarded headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = None  # Set to ('HTTP_X_FORWARDED_PROTO', 'https') if using HTTPS

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE (docker default)
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://paperless:paperless@localhost:5432/paperless")
# Simple parse (v1). For production, use dj-database-url.
import urllib.parse as up
u = up.urlparse(DATABASE_URL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": u.path.lstrip("/"),
        "USER": u.username,
        "PASSWORD": u.password,
        "HOST": u.hostname,
        "PORT": u.port or 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# Support for subpath deployment (e.g., /mordoc) via Traefik
FORCE_SCRIPT_NAME = os.getenv("DJANGO_FORCE_SCRIPT_NAME", "")

STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/" if FORCE_SCRIPT_NAME else "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
# Frontend build is copied to frontend_build/ during Docker build (relative to /app)
frontend_build_path = BASE_DIR / "frontend_build"
STATICFILES_DIRS = [str(frontend_build_path)] if frontend_build_path.exists() else []

MEDIA_URL = f"{FORCE_SCRIPT_NAME}/media/" if FORCE_SCRIPT_NAME else "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

# WhiteNoise configuration - serve index.html from root
WHITENOISE_INDEX_FILE = True

# CORS configuration - when using Traefik, origins should not include port numbers
# Example: http://localhost,http://example.com (not http://localhost:5173)
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
