from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def validate_scope(user):
    if user.scope_level == "national" and user.scope_id is not None:
        raise ValidationError("National users cannot have a scope id.")
    if user.scope_level != "national" and user.scope_id is None:
        raise ValidationError("Scoped users require a scope id.")


class InvalidCredentials(Exception):
    pass


def authenticate_user(phone: str, password: str):
    user = authenticate(phone=phone, password=password)
    if user is None or not user.is_active:
        raise InvalidCredentials()
    return user


def issue_tokens(user) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def rotate_access_token(raw_refresh: str) -> tuple[str, str]:
    """Returns (access, refresh). Raises TokenError on an invalid/blacklisted token."""
    from django.contrib.auth import get_user_model

    old = RefreshToken(raw_refresh)
    user = get_user_model().objects.get(pk=old["user_id"])
    old.blacklist()
    new_refresh = RefreshToken.for_user(user)
    return str(new_refresh.access_token), str(new_refresh)


def blacklist_refresh_token(raw_refresh: str) -> None:
    try:
        RefreshToken(raw_refresh).blacklist()
    except TokenError:
        pass


def _cookie_kwargs(max_age: timedelta) -> dict:
    return {"httponly": True, "secure": settings.JWT_COOKIE_SECURE, "samesite": "Lax",
            "max_age": int(max_age.total_seconds())}


def set_access_cookie(response, access: str) -> None:
    response.set_cookie(settings.JWT_ACCESS_COOKIE, access,
                         **_cookie_kwargs(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]))


def set_auth_cookies(response, access: str, refresh: str) -> None:
    set_access_cookie(response, access)
    response.set_cookie(settings.JWT_REFRESH_COOKIE, refresh,
                         **_cookie_kwargs(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]))


def clear_auth_cookies(response) -> None:
    response.delete_cookie(settings.JWT_ACCESS_COOKIE)
    response.delete_cookie(settings.JWT_REFRESH_COOKIE)
