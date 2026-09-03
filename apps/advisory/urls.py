from django.urls import path

from .views import (
    AdvisoryRequestQueueView,
    AdvisoryRequestRespondView,
    MyAdvisoryRequestsView,
    PostCommentsView,
    PostListView,
)

urlpatterns = [
    path("posts/", PostListView.as_view()),
    path("posts/<int:post_id>/comments/", PostCommentsView.as_view()),
    path("advisory-requests/queue/", AdvisoryRequestQueueView.as_view()),
    path("advisory-requests/mine/", MyAdvisoryRequestsView.as_view()),
    path("advisory-requests/<int:request_id>/respond/", AdvisoryRequestRespondView.as_view()),
]
