from django.urls import path

from .views import BootstrapView, SyncBatchView

urlpatterns = [
    path("sync/batch/", SyncBatchView.as_view()),
    path("sync/bootstrap/", BootstrapView.as_view()),
]
