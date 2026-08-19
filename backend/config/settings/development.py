import sys
from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Use SQLite for local development
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# DEFAULT_FROM_EMAIL = "noreply@onlinelearning.local"
