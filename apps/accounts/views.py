from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts import services
from apps.accounts.serializers import LoginSerializer, MeSerializer, SignupSerializer
from apps.farmers.services import SignupError, sign_up_farmer
from apps.geo.models import Village


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: MeSerializer, 401: OpenApiResponse(description="Incorrect phone number or password.")})
    def post(self, request):
        data = LoginSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            user = services.authenticate_user(**data.validated_data)
        except services.InvalidCredentials:
            return Response({"detail": "Incorrect phone number or password."},
                             status=status.HTTP_401_UNAUTHORIZED)
        access, refresh = services.issue_tokens(user)
        response = Response(MeSerializer(user).data)
        services.set_auth_cookies(response, access, refresh)
        return response


class SignupView(APIView):
    """Self-service farmer registration. Every other role (agent, chief,
    officer, buyer, admin) is created by someone else — an agent's offline
    flow, or an admin — but a farmer can create their own account and
    profile directly, matching how F1 (self-registration) is meant to work
    alongside agent-assisted registration, not instead of it."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=SignupSerializer, responses={200: MeSerializer, 409: OpenApiResponse(description="An account with this phone number already exists.")})
    def post(self, request):
        data = SignupSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data
        try:
            village = Village.objects.get(pk=fields.pop("village_id"))
        except Village.DoesNotExist:
            return Response({"detail": "Select a valid village."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = sign_up_farmer(village=village, **fields)
        except SignupError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        access, refresh = services.issue_tokens(user)
        response = Response(MeSerializer(user).data)
        services.set_auth_cookies(response, access, refresh)
        return response


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: None, 401: OpenApiResponse(description="Session expired.")})
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if not raw_refresh:
            return Response({"detail": "Session expired."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            access, refresh = services.rotate_access_token(raw_refresh)
        except TokenError:
            response = Response({"detail": "Session expired."}, status=status.HTTP_401_UNAUTHORIZED)
            services.clear_auth_cookies(response)
            return response
        response = Response(status=status.HTTP_204_NO_CONTENT)
        services.set_auth_cookies(response, access, refresh)
        return response


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        if raw_refresh:
            services.blacklist_refresh_token(raw_refresh)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        services.clear_auth_cookies(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)
