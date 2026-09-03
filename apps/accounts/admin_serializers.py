from rest_framework import serializers

from apps.accounts.models import ScopeLevel, SystemUser


class SystemUserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)

    class Meta:
        model = SystemUser
        fields = ["id", "phone", "full_name", "role", "scope_level", "scope_id", "is_active", "password"]

    def validate(self, attrs):
        scope_level = attrs.get("scope_level", getattr(self.instance, "scope_level", None))
        scope_id = attrs.get("scope_id", getattr(self.instance, "scope_id", None))
        if scope_level == ScopeLevel.NATIONAL and scope_id is not None:
            raise serializers.ValidationError({"scope_id": "National users cannot have a scope id."})
        if scope_level != ScopeLevel.NATIONAL and not scope_id:
            raise serializers.ValidationError({"scope_id": "Scoped users require a scope id (the district/subcounty/parish id)."})
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "A password is required to create an account."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        phone = validated_data.pop("phone")
        return SystemUser.objects.create_user(phone=phone, password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
