"""
Production-specific Django settings.
"""
import os
from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# CORS – restrict to specific origins in production
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", ""
).split(",")

# ---------------------------------------------------------------------------
# Static files via WhiteNoise
# ---------------------------------------------------------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------------
# Caching – longer TTL in production
# ---------------------------------------------------------------------------
CACHES["default"]["TIMEOUT"] = 600  # noqa: F405

# ---------------------------------------------------------------------------
# Email – real SMTP in production
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# ---------------------------------------------------------------------------
# Logging – less verbose, structured
# ---------------------------------------------------------------------------
LOGGING["root"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405
