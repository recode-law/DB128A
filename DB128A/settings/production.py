from DB128A.settings.base import *
import os

DEBUG = False
SECRET_FILE = os.path.join(BASE_DIR, 'DB128A/settings/django_secret_key.txt')
try:
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        import random

        SECRET_KEY = ''.join([
            random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)
        ])
        secret = open(SECRET_FILE, 'w')
        secret.write(SECRET_KEY)
        secret.close()
    except IOError:
        Exception('Please create a %s file with random characters to generate your secret key!' % SECRET_FILE)

ALLOWED_HOSTS = os.environ.get('VVDE_HOSTNAME').split(',')


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('VVDE_DB_NAME'),
        'USER': os.environ.get('VVDE_DB_USERNAME'),
        'PASSWORD': os.environ.get('VVDE_DB_PASSWORD'),
        'HOST': os.environ.get('VVDE_DB_HOSTNAME'),
        'PORT': os.environ.get('VVDE_DB_PORT')
    }
}
