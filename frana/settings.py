"""
Django settings for frana project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-qb=id52b2^3+-tb_86@=j&#969sfol(=+n2*v7ca5z_%8@vqct'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'frana.onrender.com',
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'finances',
    'pwa',
    'feedback',
]

AUTH_USER_MODEL = 'finances.Utilisateur'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'frana.urls'

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

WSGI_APPLICATION = 'frana.wsgi.application'


# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# =========================================================
# PWA — Frana
# =========================================================
PWA_APP_NAME = "Frana"
PWA_APP_DESCRIPTION = "SaaS de gestion des finances Made in Africa"
PWA_APP_THEME_COLOR = "#1e140d"
PWA_APP_BACKGROUND_COLOR = "#1e140d"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "portrait"
PWA_APP_START_URL = "/dashboard/"
PWA_APP_STATUS_BAR_COLOR = "default"
PWA_APP_DIR = "ltr"
PWA_APP_LANG = "fr-FR"

PWA_APP_ICONS = [
    {"src": "/static/finances/img/pwa-icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/finances/img/pwa-icon-512.png", "sizes": "512x512", "type": "image/png"},
]

PWA_APP_ICONS_APPLE = [
    {"src": "/static/finances/img/pwa-icon-192.png", "sizes": "192x192", "type": "image/png"},
]

PWA_APP_SPLASH_SCREEN = [
    {
        "src": "/static/finances/img/pwa-icon-512.png",
        "media": "(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)"
    }
]

PWA_APP_SCREENSHOTS = [
    {
        "src": "/static/finances/img/screenshot-mobile.png",
        "sizes": "540x720",
        "type": "image/png",
        "form_factor": "narrow"
    }
]

PWA_APP_SHORTCUTS = [
    {
        "name": "Nouvelle transaction",
        "short_name": "Transaction",
        "description": "Enregistrer une transaction rapidement",
        "url": "/transactions/nouvelle/",
        "icons": [{"src": "/static/finances/img/pwa-icon-192.png", "sizes": "192x192"}]
    },
    {
        "name": "Mes objectifs",
        "short_name": "Objectifs",
        "description": "Voir mes objectifs d'épargne",
        "url": "/objectifs/",
        "icons": [{"src": "/static/finances/img/pwa-icon-192.png", "sizes": "192x192"}]
    }
]

PWA_APP_DEBUG_MODE = False
PWA_SERVICE_WORKER_PATH = BASE_DIR / "finances" / "static" / "finances" / "js" / "serviceworker.js"