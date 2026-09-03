from django.db import models

from apps.core.models import TimeStampedModel


class SyncOperation(TimeStampedModel):
    """Records the outcome of every offline op_id we have ever seen, so a
    replayed batch is a no-op (IMPLEMENTATION_REACT.md section 8.2 / base
    spec section 9: "op_id is the idempotency key. Replaying a batch MUST
    be a no-op.")."""

    op_id = models.CharField(max_length=64, unique=True)
    device_id = models.CharField(max_length=64)
    op_type = models.CharField(max_length=32)
    submitted_by = models.ForeignKey("accounts.SystemUser", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=[("applied", "Applied"), ("rejected", "Rejected")])
    reason = models.CharField(max_length=32, blank=True)
    result = models.JSONField(default=dict)
