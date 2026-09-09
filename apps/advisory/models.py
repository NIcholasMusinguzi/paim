from django.db import models
from django.db.models import Q

from apps.accounts.models import ScopeLevel
from apps.core.models import TimeStampedModel


class AdvisoryContent(TimeStampedModel):
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    agro_zone = models.CharField(max_length=32, blank=True)
    week_from = models.PositiveSmallIntegerField()
    week_to = models.PositiveSmallIntegerField()
    language = models.CharField(max_length=16)
    body = models.TextField(max_length=480)
    source = models.CharField(max_length=64)
    status = models.CharField(max_length=12, choices=[(
        "draft", "Draft"), ("validated", "Validated"), ("retired", "Retired")])


class AdvisoryDelivery(TimeStampedModel):
    # Either seasonal content or a published trend insight — never neither
    # (see the constraint below). A trend delivery has no AdvisoryContent
    # row: it is a computed insight, not curated crop-week content.
    content = models.ForeignKey(
        AdvisoryContent, null=True, blank=True, on_delete=models.PROTECT)
    trend = models.ForeignKey(
        "analytics.TrendInsight", null=True, blank=True, on_delete=models.SET_NULL, related_name="deliveries")
    farmer = models.ForeignKey(
        "farmers.Farmer", on_delete=models.CASCADE, related_name="deliveries")
    channel = models.CharField(max_length=16)
    fallback_language = models.BooleanField(default=False)

    class Meta:
        constraints = [models.CheckConstraint(
            check=Q(content__isnull=False) | Q(trend__isnull=False),
            name="delivery_has_content_or_trend")]


class Post(TimeStampedModel):
    """An officer-authored announcement, scoped like TrendInsight (parish,
    district or national) — a farmer sees a post if it targets their own
    parish, their district, or everyone."""

    author = models.ForeignKey(
        "accounts.SystemUser", on_delete=models.PROTECT, related_name="posts")
    scope_level = models.CharField(max_length=16, choices=ScopeLevel.choices)
    scope_id = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=160)
    body = models.TextField(max_length=2000)


class Comment(TimeStampedModel):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        "accounts.SystemUser", on_delete=models.PROTECT, related_name="comments")
    body = models.TextField(max_length=1000)


class AdvisoryRequest(TimeStampedModel):
    """A signed-in user's question, routed to the shared insight queue."""

    farmer = models.ForeignKey("farmers.Farmer", null=True, blank=True,
                               on_delete=models.CASCADE, related_name="advisory_requests")
    requester = models.ForeignKey("accounts.SystemUser", null=True, blank=True, on_delete=models.CASCADE,
                                  related_name="advisory_requests_submitted")
    message = models.TextField(max_length=1000)
    status = models.CharField(max_length=12, choices=[(
        "open", "Open"), ("answered", "Answered")], default="open")


class AdvisoryResponse(TimeStampedModel):
    request = models.ForeignKey(
        AdvisoryRequest, on_delete=models.CASCADE, related_name="responses")
    responder = models.ForeignKey(
        "accounts.SystemUser", on_delete=models.PROTECT)
    body = models.TextField(max_length=1000)
