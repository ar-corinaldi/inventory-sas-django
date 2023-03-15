"""
Django settings for djangoAPI project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-p1rv0+=a!0dtr^2)_1##ffvw1)bz@&j__3jg%gx9bchyp(umwg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.ngrok.io', '127.0.0.1', 'localhost', '.ngrok.io']

CSRF_TRUSTED_ORIGINS = ['https://*.ngrok.io', 'http://*.ngrok.io']

# Application definition

DJANGO_DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]

THIRD_PARTY_APPS = [
    'explorer',
    'django_extensions',
    'rest_framework',
    'corsheaders',
    'django_pgviews',
    'import_export',
    'rest_framework_simplejwt',
]

MY_APPS = [
    'inventorySAS'
]

INSTALLED_APPS = DJANGO_DEFAULT_APPS + THIRD_PARTY_APPS + MY_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'inventorySAS.middleware.RlsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

ROOT_URLCONF = 'djangoAPI.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'djangoAPI.wsgi.application'

print('os', os.environ['password'])

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
# It's not
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # },
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'InventorySAS',
        'USER': 'this is not the password',
        # 'PASSWORD': 'this is not the password',
        'OPTIONS': {
            'options': '-c glb.tenant_id=0'
        },
        'HOST': 'localhost',
        'PORT': '5432'
    },
    'admin': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'InventorySAS',
        'USER': 'this is not the password',
        'PASSWORD': 'this is not the password',
        'OPTIONS': {
            'options': '-c glb.tenant_id=0'
        },
        'HOST': 'localhost',
        'PORT': '5432'
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Explorer app
EXPLORER_CONNECTIONS = {'Default': 'default'}
EXPLORER_DEFAULT_CONNECTION = 'default'

INTERNAL_IPS = [
    "127.0.0.1",
]

'''
Things to add:
0. Mandar error si no hay suficientes cosas para devolver (done)
1. Spanish
2. Order debe tener origen y destino?
3. Tables for sell, buy?
4. How to attach price to sell and buy, in an order? or another type of order? there should be order types to buy rent or sell?
5. What about adding transport prices to order?
6. Insumos/supplies?
7. Raro como se anade el precio a las ordenes no es obvio ni facil no tiene flujo 


0, Assign a user that is not super user to the DB connection
1. ALTER TABLE inventorySAS_inventorytransaction ENABLE ROW LEVEL SECURITY;
2. 
CREATE POLICY RLS_Transactions ON inventorySAS_inventorytransaction FOR ALL
  USING (order_id = (SELECT order_id FROM inventorySAS_inventorytransaction WHERE order_id));
# CREATE POLICY fp_u ON information FOR UPDATE
#   USING (order_id = current_user);


3. DROP POLICY RLS_Transactions;
or
ALTER TABLE inventorySAS_inventorytransaction DISABLE ROW LEVEL SECURITY;





GRANT USAGE ON SCHEMA public TO company;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO company;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO company;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO company;
GRANT ALL PRIVILEGES ON DATABASE database_name TO username;


'''
