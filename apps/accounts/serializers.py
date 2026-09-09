from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.permissions import permissions_for


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)


class SignupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=120)
    sex = serializers.ChoiceField(choices=["F", "M"])
    village_id = serializers.IntegerField()
    language = serializers.CharField(max_length=16, default="lug")


class ScopeSerializer(serializers.Serializer):
    level = serializers.CharField()
    id = serializers.IntegerField(allow_null=True)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    role = serializers.CharField()
    scope_level = serializers.CharField()
    scope = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    @extend_schema_field(ScopeSerializer)
    def get_scope(self, user):
        return {"level": user.scope_level, "id": user.scope_id}

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_permissions(self, user):
        return permissions_for(user)


class MeUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120, required=False)
    phone = serializers.CharField(max_length=20, required=False)
