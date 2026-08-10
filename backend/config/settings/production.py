from .base import *

DEBUG = False

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    cast=lambda value: [host.strip() for host in value.split(",")],
    default="",
)