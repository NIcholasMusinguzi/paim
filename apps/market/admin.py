from django.contrib import admin

from .models import AwardRecord, Bid, Buyer, Declaration, Lot, Settlement
from .models import AwardRecord, Bid, Buyer, Declaration, Lot, MarketPrice, Settlement


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("lot", "buyer", "price_per_kg",
                    "terms", "submitted_at", "sealed_until")
    list_filter = ("lot__status", "submitted_at")
    search_fields = ("buyer__name", "lot__crop__name", "lot__parish__name")
    readonly_fields = ("submitted_at", "created_at", "updated_at")


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ("price_date", "item_name", "category",
                    "price", "unit", "market", "source")
    list_filter = ("price_date", "category", "market")
    search_fields = ("item_name", "market", "source")


admin.site.register([AwardRecord, Buyer, Declaration, Lot, Settlement])
