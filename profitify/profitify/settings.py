"""
Django settings for profitify project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-aiz1h2)gc0g(ot!2coxrap7zh8*00ft9&%+qzap%1w#hukhl_u'

DEBUG = True

# Allow localhost, 127.0.0.1, and ANY frontend tool you use.
ALLOWED_HOSTS = ["*",]

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------
# APPLICATIONS
# -------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your app
    'APP',

    # CORS (useful for fetch requests from browsers)
    'corsheaders',
]


# -------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------

MIDDLEWARE = [
    # CORS must be at the top
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'profitify.urls'


# -------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],   # You can add extra template dirs here
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


WSGI_APPLICATION = 'profitify.wsgi.application'


# -------------------------------------------------------
# DATABASE
# -------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# -------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# -------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# -------------------------------------------------------
# STATIC FILES
# -------------------------------------------------------

STATIC_URL = 'static/'
STATICFILES_DIRS = []  # You can add frontend static folder if needed
STATIC_ROOT = BASE_DIR / "staticfiles"


# -------------------------------------------------------
# DEFAULT PRIMARY KEY FIELD
# -------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# -------------------------------------------------------
# CORS & CSRF SETTINGS
# -------------------------------------------------------

# Allow all origins for dev (safe)
CORS_ALLOW_ALL_ORIGINS = True

# If fetch() does POST, cookies, or CSRF, this helps
CORS_ALLOW_CREDENTIALS = True

# Allow frontend localhost ports
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
