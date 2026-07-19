"""Minimal Django settings for Mofi's integration tests."""

SECRET_KEY = "mofi-tests-only"
DEBUG = False
ALLOWED_HOSTS = ["testserver"]
ROOT_URLCONF = "tests.django_urls"
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
INSTALLED_APPS: list[str] = []
MOFI_VERIFICATION_TOKEN = "fixture-token"
USE_TZ = True
