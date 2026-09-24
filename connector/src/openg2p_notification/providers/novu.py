import logging
from collections.abc import Sequence
from typing import Any

from novu_py import Novu

from ..config import Settings
from ..core.factory import NotificationFactory
from ..core.interface import NotificationInterface
from ..core.models import (
    NotificationRequest,
    NotificationResponse,
    NotificationResponseStatus,
    Recipient,
)
from ..utils.events import ids

_logger = logging.getLogger("novu_notifier_impl")
_BULK_LIMIT = 100


class NovuNotifier(NotificationInterface):
    def _client(self) -> Novu:
        config = Settings.get_config()
        if not config.provider_api_key:
            raise ValueError("NOTIFICATION_PROVIDER_API_KEY is not set")
        return Novu(
            secret_key=config.provider_api_key,
            server_url=config.provider_url,
            timeout_ms=config.provider_timeout_ms,
        )

    def _to_subscriber(self, recipient: Recipient) -> dict[str, Any]:
        if not recipient.recipient_id:
            raise ValueError("recipient_id is required")
        to: dict[str, Any] = {"subscriber_id": recipient.recipient_id}
        if recipient.recipient_email:
            to["email"] = recipient.recipient_email
        if recipient.recipient_phone:
            to["phone"] = recipient.recipient_phone
        if recipient.recipient_name:
            to["first_name"] = recipient.recipient_name
        return to

    def _trigger_body(
        self,
        notification_id: str,
        payload: Any,
        workflow_id: str,
        recipient: Recipient,
    ) -> dict[str, Any]:
        if not workflow_id:
            raise ValueError("workflow_id is required")
        body: dict[str, Any] = {
            "workflow_id": workflow_id,
            "to": self._to_subscriber(recipient),
            "payload": payload or {},
        }
        if notification_id:
            body["transaction_id"] = notification_id
        return body

    def _map_result(self, notification_id: str, result: Any) -> NotificationResponse:
        status_value = getattr(getattr(result, "status", None), "value", None) or getattr(
            result, "status", None
        )
        ok = str(status_value or "").lower() == "processed"
        return NotificationResponse(
            notification_id=notification_id,
            response=str(result) if result is not None else None,
            status=NotificationResponseStatus.SUCCESS if ok else NotificationResponseStatus.FAILURE,
        )

    def _skipped(self, notification_id: str) -> NotificationResponse:
        return NotificationResponse(
            notification_id=notification_id,
            response="skipped",
            status=NotificationResponseStatus.SUCCESS,
        )

    def send(
        self,
        event: str,
        entity_id: str,
        payload: Any,
        recipient: Recipient,
        notification_id: str | None = None,
    ) -> NotificationResponse:
        workflow_id, nid = ids(event, entity_id, notification_id)
        if not workflow_id:
            _logger.info("Skipping event %s; not in NOTIFICATION_WORKFLOWS", event)
            return self._skipped(nid)
        body = self._trigger_body(nid, payload, workflow_id, recipient)
        _logger.info(
            "Sending event %s workflow %s to recipient_id=%s notification_id=%s",
            event,
            workflow_id,
            recipient.recipient_id,
            nid,
        )
        with self._client() as novu:
            novu_response = novu.trigger(trigger_event_request_dto=body)
        return self._map_result(nid, novu_response.result)

    def send_bulk(
        self,
        requests: Sequence[NotificationRequest],
    ) -> list[NotificationResponse]:
        if not requests:
            return []
        if len(requests) > _BULK_LIMIT:
            raise ValueError(f"send_bulk supports at most {_BULK_LIMIT} events per call")
        results: list[NotificationResponse | None] = [None] * len(requests)
        resolved: list[tuple[int, str, dict[str, Any]]] = []
        for index, item in enumerate(requests):
            workflow_id, nid = ids(item.event, item.entity_id, item.notification_id)
            if not workflow_id:
                results[index] = self._skipped(nid)
                continue
            resolved.append((index, nid, self._trigger_body(nid, item.payload, workflow_id, item.recipient)))
        if resolved:
            with self._client() as novu:
                novu_response = novu.trigger_bulk(
                    bulk_trigger_event_dto={"events": [body for _, _, body in resolved]}
                )
            rows = novu_response.result if isinstance(novu_response.result, list) else []
            for i, (index, nid, _) in enumerate(resolved):
                results[index] = self._map_result(nid, rows[i] if i < len(rows) else None)
        return results


NotificationFactory.register("novu", NovuNotifier)
