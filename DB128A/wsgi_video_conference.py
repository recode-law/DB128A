"""
WSGI config for DB128A project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DB128A.settings.production')
os.environ.setdefault('DB128A_CONTEXT', 'video_conference')

application = get_wsgi_application()
