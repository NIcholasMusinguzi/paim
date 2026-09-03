from django.urls import path

from .views import ParishListView, PublicVillageListView

urlpatterns = [
    path("parishes/", ParishListView.as_view()),
    path("villages/", PublicVillageListView.as_view()),
]
