from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import OFFICER_ROLES
from apps.advisory.models import AdvisoryRequest
from apps.advisory.selectors import advisory_requests_visible_to, posts_visible_to
from apps.advisory.serializers import (
    AdvisoryRequestCreateSerializer,
    AdvisoryRequestSerializer,
    AdvisoryResponseSerializer,
    CommentSerializer,
    PostCreateSerializer,
    PostSerializer,
)
from apps.advisory.services import (
    AdvisoryRequestError,
    PostScopeError,
    add_comment,
    create_post,
    respond_to_request,
    submit_advisory_request,
)


class PostListView(APIView):
    """Officer-authored, scope-visible announcements (section: "posting
    information"). Any signed-in user can read; only an officer can post,
    and only within their own scope (enforced in create_post())."""

    @extend_schema(responses={200: PostSerializer(many=True)})
    def get(self, request):
        return Response(PostSerializer(posts_visible_to(request.user), many=True).data)

    @extend_schema(request=PostCreateSerializer, responses={201: PostSerializer})
    def post(self, request):
        if request.user.role not in OFFICER_ROLES:
            raise PermissionDenied("Only an officer may post.")
        data = PostCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            post = create_post(author=request.user, **data.validated_data)
        except PostScopeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)


class PostCommentsView(APIView):
    """Any signed-in user who can see the post can comment on it — visibility
    of the thread always matches visibility of the post itself, never
    checked separately."""

    def _visible_post(self, user, post_id):
        post = posts_visible_to(user).filter(pk=post_id).first()
        if post is None:
            raise NotFound("Post not found.")
        return post

    @extend_schema(responses={200: CommentSerializer(many=True)})
    def get(self, request, post_id):
        post = self._visible_post(request.user, post_id)
        return Response(CommentSerializer(post.comments.select_related("author").order_by("created_at"), many=True).data)

    @extend_schema(request=CommentSerializer, responses={201: CommentSerializer})
    def post(self, request, post_id):
        post = self._visible_post(request.user, post_id)
        data = CommentSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        comment = add_comment(post=post, author=request.user,
                              body=data.validated_data["body"])
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class AdvisoryRequestQueueView(APIView):
    """The shared parish queue an officer works from — every open (and
    answered) request they have authority to see."""

    @extend_schema(responses={200: AdvisoryRequestSerializer(many=True)})
    def get(self, request):
        if request.user.role not in OFFICER_ROLES:
            raise PermissionDenied(
                "Only an officer may view the advisory request queue.")
        return Response(AdvisoryRequestSerializer(advisory_requests_visible_to(request.user), many=True).data)


class MyAdvisoryRequestsView(APIView):
    """A farmer's own questions and any responses — the flip side of the
    officer queue above."""

    @extend_schema(responses={200: AdvisoryRequestSerializer(many=True)})
    def get(self, request):
        farmer = getattr(request.user, "farmer_profile", None)
        return Response(AdvisoryRequestSerializer(
            AdvisoryRequest.objects.filter(requester=request.user).select_related(
                "farmer", "farmer__village__parish")
            .prefetch_related("responses__responder").order_by("-created_at"), many=True).data)

    @extend_schema(request=AdvisoryRequestCreateSerializer, responses={201: AdvisoryRequestSerializer})
    def post(self, request):
        farmer = getattr(request.user, "farmer_profile", None)
        data = AdvisoryRequestCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        advisory_request = submit_advisory_request(
            requester=request.user, farmer=farmer, **data.validated_data)
        return Response(AdvisoryRequestSerializer(advisory_request).data, status=status.HTTP_201_CREATED)


class AdvisoryRequestRespondView(APIView):
    @extend_schema(request=AdvisoryResponseSerializer, responses={200: AdvisoryRequestSerializer})
    def post(self, request, request_id):
        advisory_request = get_object_or_404(AdvisoryRequest, pk=request_id)
        data = AdvisoryResponseSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            respond_to_request(advisory_request=advisory_request,
                               responder=request.user, **data.validated_data)
        except AdvisoryRequestError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        advisory_request.refresh_from_db()
        return Response(AdvisoryRequestSerializer(advisory_request).data)
