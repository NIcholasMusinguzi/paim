from django.urls import path

from .views import FarmerDeclarationView, FarmerHomeView, FarmerProfileView, ReferenceDataView

urlpatterns = [
    path("farmer/home/", FarmerHomeView.as_view()),
    path("reference/", ReferenceDataView.as_view()),
    path("farmer/profile/", FarmerProfileView.as_view()),
    path("farmer/declarations/", FarmerDeclarationView.as_view()),
]
