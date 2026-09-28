from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from openg2p_fastapi_common.context import component_registry, config_registry
from openg2p_notification.app import Initializer
from openg2p_notification.core.factory import NotificationFactory
from openg2p_notification.core.models import (
    NotificationRequest,
    NotificationResponseStatus,
    Recipient,
)
from openg2p_notification.providers import NovuNotifier
from openg2p_notification.utils import (
    ids,
    notification_id,
    registrant_id,
    resolve_workflow_id,
    workflow_enabled,
)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    component_registry.clear()
    config_registry.set(None)
    monkeypatch.setenv("NOTIFICATION_ENABLED", "true")
    monkeypatch.setenv("NOTIFICATION_PROVIDER", "novu")
    monkeypatch.setenv("NOTIFICATION_PROVIDER_API_KEY", "test-key")
    monkeypatch.setenv("NOTIFICATION_PROVIDER_URL", "http://novu.test")
    monkeypatch.delenv("NOTIFICATION_WORKFLOWS", raising=False)
    yield
    component_registry.clear()
    config_registry.set(None)


def _processed():
    return SimpleNamespace(
        result=SimpleNamespace(status=SimpleNamespace(value="processed"))
    )


def _patch_client(response):
    novu = MagicMock()
    novu.trigger.return_value = response
    novu.trigger_bulk.return_value = response
    novu.__enter__.return_value = novu
    novu.__exit__.return_value = False
    return patch("openg2p_notification.providers.novu.Novu", return_value=novu), novu


def test_factory_registers_novu_from_config():
    Initializer()
    assert isinstance(NotificationFactory.get_notifier(), NovuNotifier)


def test_get_notifier_without_initializer():
    assert isinstance(NotificationFactory.get_notifier(), NovuNotifier)


def test_unknown_provider(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_PROVIDER", "not-a-provider")
    config_registry.set(None)
    with pytest.raises(ValueError, match="Unknown notification provider"):
        NotificationFactory.get_notifier()


def test_registrant_id():
    assert registrant_id("abc-123") == "person:abc-123"


def test_notification_id():
    assert notification_id("change_request.created", "cr-1") == "change_request.created:cr-1"
    with pytest.raises(ValueError, match="event"):
        notification_id("", "cr-1")
    with pytest.raises(ValueError, match="entity_id"):
        notification_id("change_request.created", "")


def test_ids_skips_unmapped_event():
    assert ids("change_request.created", "cr-1") == (
        None,
        "change_request.created:cr-1",
    )


def test_ids_override_and_map(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    assert ids("change_request.created", "cr-1") == (
        "change-request-created",
        "change_request.created:cr-1",
    )
    assert ids("change_request.created", "cr-1", "custom-id") == (
        "change-request-created",
        "custom-id",
    )


def test_resolve_workflow_id_map(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    assert resolve_workflow_id("change_request.created") == "change-request-created"
    assert resolve_workflow_id("cr.approved") is None
    assert workflow_enabled("change_request.created") is True
    assert workflow_enabled("cr.approved") is False


def test_resolve_workflow_id_empty_map_and_blank_value(monkeypatch):
    assert resolve_workflow_id("change_request.created") is None
    assert workflow_enabled("change_request.created") is False
    monkeypatch.setenv("NOTIFICATION_WORKFLOWS", '{"change_request.created": "  "}')
    config_registry.set(None)
    assert resolve_workflow_id("change_request.created") is None
    assert workflow_enabled("change_request.created") is False


def test_send_skips_unmapped_event():
    ctx, novu = _patch_client(_processed())
    with ctx:
        result = NovuNotifier().send(
            "change_request.created",
            "cr-1",
            {"change_request_id": "cr-1"},
            Recipient(
                recipient_id="person:rec-1",
                recipient_email="ada@example.com",
                recipient_phone="+10000000000",
                recipient_name="Ada",
            ),
        )
    novu.trigger.assert_not_called()
    assert result.response == "skipped"
    assert result.status is NotificationResponseStatus.SUCCESS
    assert result.notification_id == "change_request.created:cr-1"


def test_send_skips_when_notifications_disabled(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_ENABLED", "false")
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    ctx, novu = _patch_client(_processed())
    with ctx:
        result = NovuNotifier().send(
            "change_request.created",
            "cr-1",
            {"change_request_id": "cr-1"},
            Recipient(recipient_id="person:rec-1", recipient_email="ada@example.com"),
        )
    novu.trigger.assert_not_called()
    assert result.response == "skipped"
    assert workflow_enabled("change_request.created") is False


def test_send_maps_and_builds_notification_id(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    ctx, novu = _patch_client(_processed())
    with ctx:
        result = NovuNotifier().send(
            "change_request.created",
            "cr-1",
            {"change_request_id": "cr-1"},
            Recipient(
                recipient_id="person:rec-1",
                recipient_email="ada@example.com",
                recipient_phone="+10000000000",
                recipient_name="Ada",
            ),
        )
    body = novu.trigger.call_args.kwargs["trigger_event_request_dto"]
    assert body["workflow_id"] == "change-request-created"
    assert body["to"]["subscriber_id"] == "person:rec-1"
    assert body["to"]["email"] == "ada@example.com"
    assert body["to"]["phone"] == "+10000000000"
    assert body["transaction_id"] == "change_request.created:cr-1"
    assert result.status is NotificationResponseStatus.SUCCESS
    assert result.notification_id == "change_request.created:cr-1"


def test_send_maps_event_to_workflow(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "cr-created-novu"}',
    )
    config_registry.set(None)
    ctx, novu = _patch_client(_processed())
    with ctx:
        NovuNotifier().send(
            "change_request.created",
            "cr-1",
            {},
            Recipient(recipient_id="person:rec-1"),
        )
    body = novu.trigger.call_args.kwargs["trigger_event_request_dto"]
    assert body["workflow_id"] == "cr-created-novu"
    assert body["transaction_id"] == "change_request.created:cr-1"


def test_send_rejects_empty_recipient_id(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    ctx, _novu = _patch_client(_processed())
    with ctx:
        with pytest.raises(ValueError, match="recipient_id"):
            NovuNotifier().send(
                "change_request.created",
                "cr-1",
                {},
                Recipient(recipient_id="", recipient_email="ada@example.com"),
            )


def test_send_bulk_sends_only_mapped_events(monkeypatch):
    monkeypatch.setenv(
        "NOTIFICATION_WORKFLOWS",
        '{"change_request.created": "change-request-created"}',
    )
    config_registry.set(None)
    ctx, novu = _patch_client(
        SimpleNamespace(
            result=[
                SimpleNamespace(status=SimpleNamespace(value="processed")),
                SimpleNamespace(status=SimpleNamespace(value="processed")),
            ]
        )
    )
    with ctx:
        results = NovuNotifier().send_bulk(
            [
                NotificationRequest(
                    event="change_request.created",
                    entity_id="1",
                    recipient=Recipient(recipient_id="person:1"),
                ),
                NotificationRequest(
                    event="change_request.approved",
                    entity_id="2",
                    recipient=Recipient(recipient_id="person:2"),
                ),
            ]
        )
    events = novu.trigger_bulk.call_args.kwargs["bulk_trigger_event_dto"]["events"]
    assert [item["to"]["subscriber_id"] for item in events] == ["person:1"]
    assert [item["workflow_id"] for item in events] == ["change-request-created"]
    assert [item.notification_id for item in results] == [
        "change_request.created:1",
        "change_request.approved:2",
    ]
    assert results[0].status is NotificationResponseStatus.SUCCESS
    assert results[1].response == "skipped"


def test_send_bulk_limit():
    ctx, _novu = _patch_client(SimpleNamespace(result=[]))
    with ctx:
        requests = [
            NotificationRequest(
                event="x",
                entity_id=str(i),
                recipient=Recipient(recipient_id=str(i)),
            )
            for i in range(101)
        ]
        with pytest.raises(ValueError, match="100"):
            NovuNotifier().send_bulk(requests)


def test_missing_api_key(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_WORKFLOWS", '{"x": "x"}')
    monkeypatch.delenv("NOTIFICATION_PROVIDER_API_KEY", raising=False)
    config_registry.set(None)
    with pytest.raises(ValueError, match="NOTIFICATION_PROVIDER_API_KEY"):
        NovuNotifier().send(
            "x",
            "1",
            {},
            Recipient(recipient_id="person:1"),
        )
