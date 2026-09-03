from django.urls import path

from .views import FarmerHomeView, ReferenceDataView

urlpatterns = [
    path("farmer/home/", FarmerHomeView.as_view()),
    path("reference/", ReferenceDataView.as_view()),
]
