from rest_framework import serializers

from apps.accounts.models import Role
from apps.market.models import Buyer


class BuyerAdminSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Buyer
        fields = ["id", "name", "licence_no", "user", "user_phone", "verified_at"]

    def validate_user(self, user):
        if user.role != Role.BUYER:
            raise serializers.ValidationError("The linked account must have the buyer role.")
        return user

    def validate(self, attrs):
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user and Buyer.objects.filter(user=user).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"user": "This account is already linked to another buyer."})
        return attrs
