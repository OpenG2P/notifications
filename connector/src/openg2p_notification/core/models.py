import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationResponseStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class Recipient(BaseModel):
    recipient_id: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None


class NotificationRequest(BaseModel):
    event: str
    entity_id: str
    recipient: Recipient
    payload: dict[str, Any] = Field(default_factory=dict)
    notification_id: Optional[str] = None


class NotificationResponse(BaseModel):
    notification_id: str
    response: Optional[str] = None
    status: NotificationResponseStatus
