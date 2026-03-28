"""
Development-specific Django settings.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar (optional – install if needed)
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]

# Use console email backend in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Weaker throttling for development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "10000/hour",
}

# Simplified static file serving
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Show SQL queries in console (optional – can be noisy)
# LOGGING["loggers"]["django.db.backends"] = {
#     "handlers": ["console"],
#     "level": "DEBUG",
#     "propagate": False,
# }
