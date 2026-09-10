from .dev import *

# Channels docs recommend the in-memory layer for tests: it needs no redis
# and each test process gets an isolated layer.
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "paim-test"}}
