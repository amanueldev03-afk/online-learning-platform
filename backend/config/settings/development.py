from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Use Supabase PostgreSQL for development
# DATABASES configuration inherited from base.py using DATABASE_URL

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# DEFAULT_FROM_EMAIL = "noreply@onlinelearning.local"
