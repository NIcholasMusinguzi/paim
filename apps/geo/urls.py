from django.urls import path

from .views import ParishListView, PublicVillageListView, WeatherView

urlpatterns = [
    path("parishes/", ParishListView.as_view()),
    path("villages/", PublicVillageListView.as_view()),
    path("weather/", WeatherView.as_view()),
]
