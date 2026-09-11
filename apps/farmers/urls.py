from django.urls import path

from .views import FarmerDeclarationView, FarmerDirectoryView, FarmerHomeView, FarmerProfileView, ReferenceDataView

urlpatterns = [
    path("farmers/", FarmerDirectoryView.as_view()),
    path("farmer/home/", FarmerHomeView.as_view()),
    path("reference/", ReferenceDataView.as_view()),
    path("farmer/profile/", FarmerProfileView.as_view()),
    path("farmer/declarations/", FarmerDeclarationView.as_view()),
]
