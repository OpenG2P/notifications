def registrant_id(internal_record_id: str) -> str:
    """Novu subscriber id for a registry person record."""
    return f"person:{internal_record_id}"
