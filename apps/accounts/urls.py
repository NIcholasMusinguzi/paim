from django.urls import path

from .views import LoginView, LogoutView, MeView, RefreshView, SignupView

urlpatterns = [
    path("auth/login/", LoginView.as_view()),
    path("auth/signup/", SignupView.as_view()),
    path("auth/refresh/", RefreshView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
]
