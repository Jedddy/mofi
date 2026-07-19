"""Minimal settings for the Mofi Django example."""

import os


SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS: list[str] = []
ROOT_URLCONF = "examples.django_app.urls"
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
INSTALLED_APPS: list[str] = []
