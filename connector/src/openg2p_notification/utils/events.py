from ..config import Settings


def resolve_workflow_id(event: str) -> str:
    """Map an OpenG2P event key to the provider workflow / template id.

    If ``NOTIFICATION_WORKFLOWS`` has no entry for ``event``, the event key is
    used as-is.
    """
    key = (event or "").strip()
    if not key:
        raise ValueError("event is required")
    mapped = (Settings.get_config().workflows or {}).get(key)
    if mapped is None:
        return key
    mapped = str(mapped).strip()
    if not mapped:
        raise ValueError(f"NOTIFICATION_WORKFLOWS[{key!r}] is empty")
    return mapped


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
) -> tuple[str, str]:
    """Return ``(workflow_id, notification_id)`` for a send.

    Providers call this so mapping is not owned by Novu (or any other impl).
    """
    workflow_id = resolve_workflow_id(event)
    resolved = (nid or "").strip() or notification_id(event, entity_id)
    return workflow_id, resolved
