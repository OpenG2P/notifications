from ..config import Settings


def resolve_workflow_id(event: str) -> str | None:
    """Map an OpenG2P event key to the provider workflow id.

    ``NOTIFICATION_WORKFLOWS`` is the allow-list. A missing key, a blank
    mapped value, or an empty map means the event is not sent.
    """
    key = (event or "").strip()
    if not key:
        raise ValueError("event is required")
    mapped = (Settings.get_config().workflows or {}).get(key)
    if mapped is None:
        return None
    mapped = str(mapped).strip()
    return mapped or None


def workflow_enabled(event: str) -> bool:
    """True when ``NOTIFICATION_WORKFLOWS`` has a non-empty mapping for ``event``."""
    if not (event or "").strip():
        return False
    return resolve_workflow_id(event) is not None


def notification_id(event: str, entity_id: str) -> str:
    """Idempotency / correlation id: ``{event}:{entity_id}``."""
    key = (event or "").strip()
    entity = (entity_id or "").strip()
    if not key:
        raise ValueError("event is required")
    if not entity:
        raise ValueError("entity_id is required")
    return f"{key}:{entity}"


def ids(
    event: str,
    entity_id: str,
    nid: str | None = None,
) -> tuple[str | None, str]:
    """Return ``(workflow_id, notification_id)`` for a send.

    ``workflow_id`` is None when the event is not in ``NOTIFICATION_WORKFLOWS``.
    """
    workflow_id = resolve_workflow_id(event)
    resolved = (nid or "").strip() or notification_id(event, entity_id)
    return workflow_id, resolved
