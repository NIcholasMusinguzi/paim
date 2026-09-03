from http.cookies import SimpleCookie

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_token(raw_token: str):
    from django.contrib.auth import get_user_model

    try:
        validated = AccessToken(raw_token)
    except TokenError:
        return AnonymousUser()
    User = get_user_model()
    try:
        return User.objects.get(pk=validated["user_id"], is_active=True)
    except User.DoesNotExist:
        return AnonymousUser()


def _cookies_from_scope(scope) -> dict:
    for name, value in scope.get("headers", []):
        if name == b"cookie":
            jar = SimpleCookie()
            jar.load(value.decode("latin-1"))
            return {k: m.value for k, m in jar.items()}
    return {}


class JWTCookieAuthMiddleware:
    """ASGI middleware: validates the access-token cookie on the WS handshake
    and attaches scope["user"], mirroring CookieJWTAuthentication on HTTP so
    there is exactly one notion of "who is this" across both transports."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        cookies = _cookies_from_scope(scope)
        raw = cookies.get(settings.JWT_ACCESS_COOKIE)
        scope["user"] = await _user_from_token(raw) if raw else AnonymousUser()
        return await self.app(scope, receive, send)


def JWTCookieAuthMiddlewareStack(app):
    from channels.auth import AuthMiddlewareStack

    return JWTCookieAuthMiddleware(AuthMiddlewareStack(app))
