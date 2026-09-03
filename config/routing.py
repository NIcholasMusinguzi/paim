from django.urls import re_path

from apps.realtime.consumers import ParishConsumer, ScopeConsumer

websocket_urlpatterns = [
    re_path(r"^ws/parish/(?P<parish_id>\d+)/$", ParishConsumer.as_asgi()),
    re_path(r"^ws/scope/(?P<level>national|district)/(?P<scope_id>\d*)/$", ScopeConsumer.as_asgi()),
]
