from apps.accounts.admin_serializers import SystemUserAdminSerializer
from apps.accounts.models import SystemUser
from apps.accounts.permissions import IsNationalAdmin
from apps.core.viewsets import AdminModelViewSet


class SystemUserViewSet(AdminModelViewSet):
    """No hard delete: a user is referenced by PROTECT from farmers they
    registered, declarations they graded, awards they recorded and so on —
    deactivate (is_active=False) is the real-world operation, not erasing
    the audit trail. PUT is also off; updates are always partial."""

    queryset = SystemUser.objects.order_by("full_name")
    serializer_class = SystemUserAdminSerializer
    permission_classes = [IsNationalAdmin]
    http_method_names = ["get", "post", "patch", "head", "options"]
