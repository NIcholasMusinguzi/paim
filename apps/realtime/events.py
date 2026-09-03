import logging
from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish(group: str, event_type: str, payload: dict) -> None:
    """Fire-and-forget. Never raises into the caller: a dead socket layer
    must not roll back a declaration."""
    try:
        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            group,
            {
                "type": "domain_event",
                "payload": {"type": event_type, "at": now_iso(), **payload},
            },
        )
    except Exception:
        logger.exception("realtime publish failed", extra={"group": group, "event": event_type})
