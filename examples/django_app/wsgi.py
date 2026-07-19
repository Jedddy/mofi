"""WSGI entry point for the Mofi Django example."""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examples.django_app.settings")
application = get_wsgi_application()
