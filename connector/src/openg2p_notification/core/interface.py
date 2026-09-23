from collections.abc import Sequence
from typing import Any, Optional

from openg2p_fastapi_common.service import BaseService

from .models import NotificationRequest, NotificationResponse, Recipient


class NotificationInterface(BaseService):
    def send(
        self,
        event: str,
        entity_id: str,
        payload: Any,
        recipient: Recipient,
        notification_id: Optional[str] = None,
    ) -> NotificationResponse:
        raise NotImplementedError

    def send_bulk(
        self,
        requests: Sequence[NotificationRequest],
    ) -> list[NotificationResponse]:
        return [
            self.send(
                item.event,
                item.entity_id,
                item.payload,
                item.recipient,
                item.notification_id,
            )
            for item in requests
        ]
