from rest_framework import serializers

from apps.advisory.models import AdvisoryResponse, Comment


class PostSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    author_name = serializers.CharField(source="author.full_name")
    scope_level = serializers.CharField()
    scope_id = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    body = serializers.CharField()
    created_at = serializers.DateTimeField()
    comment_count = serializers.SerializerMethodField()

    def get_comment_count(self, post) -> int:
        return post.comments.count()


class PostCreateSerializer(serializers.Serializer):
    scope_level = serializers.ChoiceField(
        choices=["national", "district", "subcounty", "parish"])
    scope_id = serializers.IntegerField(
        required=False, allow_null=True, default=None)
    title = serializers.CharField(max_length=160)
    body = serializers.CharField(max_length=2000)


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(
        source="author.full_name", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author_name", "body", "created_at"]
        read_only_fields = ["id", "author_name", "created_at"]


class AdvisoryResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.CharField(
        source="responder.full_name", read_only=True)

    class Meta:
        model = AdvisoryResponse
        fields = ["id", "responder_name", "body", "created_at"]
        read_only_fields = ["id", "responder_name", "created_at"]


class AdvisoryRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    farmer_name = serializers.SerializerMethodField()
    parish_name = serializers.SerializerMethodField()
    message = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    responses = AdvisoryResponseSerializer(many=True)

    def get_farmer_name(self, request):
        return request.farmer.full_name if request.farmer_id else request.requester.full_name

    def get_parish_name(self, request):
        if request.farmer_id:
            return request.farmer.village.parish.name
        if request.requester.scope_level == "parish":
            from apps.geo.models import Parish

            return Parish.objects.get(pk=request.requester.scope_id).name
        return "General queue"


class AdvisoryRequestCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
