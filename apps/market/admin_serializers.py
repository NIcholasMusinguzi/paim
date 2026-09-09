from rest_framework import serializers

from apps.accounts.models import Role
from apps.market.models import Bid, Buyer, MarketPrice


class BidAdminSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.name", read_only=True)
    crop = serializers.CharField(source="lot.crop.name", read_only=True)
    parish = serializers.CharField(source="lot.parish.name", read_only=True)
    lot_status = serializers.CharField(source="lot.status", read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "buyer_name", "crop", "parish", "lot_status", "price_per_kg",
                  "terms", "submitted_at", "sealed_until"]


class MarketPriceAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = ["id", "item_name", "category", "price",
                  "unit", "market", "price_date", "source"]


class BuyerAdminSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Buyer
        fields = ["id", "name", "licence_no",
                  "user", "user_phone", "verified_at"]

    def validate_user(self, user):
        if user.role != Role.BUYER:
            raise serializers.ValidationError(
                "The linked account must have the buyer role.")
        return user

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user and Buyer.objects.filter(user=user).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError(
                {"user": "This account is already linked to another buyer."})
        return attrs


class BuyerAdminSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Buyer
        fields = ["id", "name", "licence_no",
                  "user", "user_phone", "verified_at"]

    def validate_user(self, user):
        if user.role != Role.BUYER:
            raise serializers.ValidationError(
                "The linked account must have the buyer role.")
        return user

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user and Buyer.objects.filter(user=user).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError(
                {"user": "This account is already linked to another buyer."})
        return attrs
