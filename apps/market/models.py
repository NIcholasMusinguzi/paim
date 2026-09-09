from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class LotStatus(models.TextChoices):
    OPEN = "open"
    CLOSED = "closed"
    AWARDED = "awarded"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class Grade(models.TextChoices):
    G1 = "grade_1"
    G2 = "grade_2"
    UNGRADED = "ungraded"
    REJECT = "reject"


class Lot(TimeStampedModel):
    parish = models.ForeignKey(
        "geo.Parish", on_delete=models.PROTECT, related_name="lots")
    season = models.ForeignKey("farmers.Season", on_delete=models.PROTECT)
    crop = models.ForeignKey("farmers.Crop", on_delete=models.PROTECT)
    min_bags = models.PositiveIntegerField()
    status = models.CharField(
        max_length=12, choices=LotStatus.choices, default=LotStatus.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    awarded_bid = models.OneToOneField(
        "Bid", null=True, blank=True, on_delete=models.SET_NULL, related_name="awarded_lot")


class Declaration(TimeStampedModel):
    farmer = models.ForeignKey(
        "farmers.Farmer", on_delete=models.PROTECT, related_name="declarations")
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT,
                            related_name="declarations")
    bags = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(200)])
    moisture_pct = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True)
    grade = models.CharField(
        max_length=10, choices=Grade.choices, default=Grade.UNGRADED)
    graded_by = models.ForeignKey(
        "accounts.SystemUser", null=True, blank=True, on_delete=models.PROTECT)
    graded_at = models.DateTimeField(null=True, blank=True)
    declared_via = models.CharField(max_length=16, default="web")


class Buyer(TimeStampedModel):
    name = models.CharField(max_length=120)
    licence_no = models.CharField(max_length=48, unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        "accounts.SystemUser", null=True, on_delete=models.PROTECT)
    user = models.OneToOneField(
        "accounts.SystemUser", on_delete=models.PROTECT, related_name="buyer_profile")


class Bid(TimeStampedModel):
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="bids")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT)
    price_per_kg = models.PositiveIntegerField()
    terms = models.CharField(max_length=160)
    submitted_at = models.DateTimeField(auto_now_add=True)
    sealed_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["lot", "buyer"], name="one_bid_per_buyer_lot")]


class AwardRecord(TimeStampedModel):
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT)
    bid = models.ForeignKey(Bid, on_delete=models.PROTECT)
    recorded_by = models.ForeignKey(
        "accounts.SystemUser", on_delete=models.PROTECT)
    committee_minute_ref = models.CharField(max_length=120)


class Settlement(TimeStampedModel):
    declaration = models.OneToOneField(Declaration, on_delete=models.PROTECT)
    bid = models.ForeignKey(Bid, on_delete=models.PROTECT)
    gross_amount = models.PositiveIntegerField()
    commission = models.PositiveIntegerField()
    net_amount = models.PositiveIntegerField()
    mm_reference = models.CharField(max_length=64, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)


class MarketPrice(TimeStampedModel):
    class Category(models.TextChoices):
        PRODUCE = "produce", "Produce"
        INPUT = "input", "Farm input"

    item_name = models.CharField(max_length=120)
    category = models.CharField(max_length=12, choices=Category.choices)
    price = models.PositiveIntegerField()
    unit = models.CharField(max_length=32)
    market = models.CharField(max_length=120, blank=True)
    price_date = models.DateField()
    source = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-price_date", "category", "item_name"]
        indexes = [models.Index(fields=["price_date", "category"])]
