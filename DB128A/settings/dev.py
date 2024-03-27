from DB128A.settings.base import *

DEBUG = True
SECRET_KEY = 'django-insecure-u3a8anoz&!o^89zu_bby0x8u6^4tly=ws^dw@xb_ddns0xanqu'
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1'
]


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
