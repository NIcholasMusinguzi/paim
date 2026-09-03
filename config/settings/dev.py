from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
JWT_COOKIE_SECURE = False  # plain http in local dev
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
