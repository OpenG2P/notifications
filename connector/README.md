# OpenG2P Notification

Python connector for **send** and **send_bulk** from OpenG2P backends (registry, staff-api, and similar). Host apps emit a **business event**; the connector maps that to the provider workflow and channels.

This package does not talk to the staff inbox. Session HMAC, list, and read stay on the Next.js BFF.

## Installation

```bash
pip install openg2p-notification
```

From this repo:

```bash
pip install -e connector/
```

In the host app `pyproject.toml`:

```toml
dependencies = [
  "openg2p-notification",
]
```

`pip install` only puts the library on the path. You still set env vars and boot the factory (next sections).

## Setup

| Env | Default | Meaning |
| --- | --- | --- |
| `NOTIFICATION_PROVIDER` | `novu` | Module name under `providers/` |
| `NOTIFICATION_PROVIDER_URL` | `http://localhost:3000` | Provider API base URL |
| `NOTIFICATION_PROVIDER_API_KEY` | _(empty)_ | Secret key (Novu dashboard **Secret Key**, not the docker `NOVU_SECRET_KEY`) |
| `NOTIFICATION_PROVIDER_TIMEOUT_MS` | `20000` | HTTP timeout |
| `NOTIFICATION_WORKFLOWS` | `{}` | JSON allow-list of event key → provider workflow / template id. `{}` sends nothing. Missing or blank keys are skipped. |

Create workflows in the Novu dashboard. List only the events this environment should send:

```bash
NOTIFICATION_WORKFLOWS={"change_request.created":"change-request-created"}
```

The event catalog (which events exist) lives in the **host app**, not in this package.

In OpenG2P apps, construct the initializer once in `main.py` (same pattern as IAM / core):

```python
from openg2p_notification.app import Initializer as NotificationInitializer

IAMInitializer()
CoreInitializer()
NotificationInitializer()
```

You can skip that and call `NotificationFactory.get_notifier()` later; it builds the provider from Settings on first use.

## Usage

```python
from openg2p_notification import NotificationFactory, Recipient, registrant_id

NotificationFactory.get_notifier().send(
    event="change_request.created",
    entity_id=cr_id,
    payload={"change_request_id": cr_id, "register_id": register_id},
    recipient=Recipient(
        recipient_id=registrant_id(internal_record_id),  # person:{id}
        recipient_email=person_email,
        recipient_phone=person_phone,
        recipient_name=person_name,  # optional
    ),
)
```

The connector sets (also available from `openg2p_notification.utils`):

- **`resolve_workflow_id(event)`** — `NOTIFICATION_WORKFLOWS[event]`, or `event` if unmapped
- **`notification_id(event, entity_id)`** — `{event}:{entity_id}` (Novu `transaction_id`)
- **`ids(event, entity_id)`** — both of the above; pass a third arg to override `notification_id`

`send()` already calls `ids()`. Host apps normally only pass `event` and `entity_id`.

- **Staff:** `recipient_id` is the Keycloak `sub`.
- **Citizen / registrant:** `registrant_id(internal_record_id)` → `person:{id}`. Use email/phone from that person record, not `created_by`.
- From an async service: `await asyncio.to_thread(...)`. Call after `session.commit()`. Catch and log.

Bulk (max 100):

```python
from openg2p_notification import NotificationRequest

notifier.send_bulk(
    [
        NotificationRequest(
            event="change_request.created",
            entity_id="1",
            recipient=Recipient(recipient_id="person:rec-1", recipient_email="ada@example.com"),
            payload={"change_request_id": "1"},
        ),
    ]
)
```

## Extension (adding provider implementation)

The factory loads `openg2p_notification.providers.{NOTIFICATION_PROVIDER}`. It does not name Novu.

1. Add `src/openg2p_notification/providers/acme.py`.
2. Implement `NotificationInterface` (`send` / `send_bulk`). Call `ids(event, entity_id)` for workflow and notification ids.
3. Register at module load.
4. Set `NOTIFICATION_PROVIDER=acme` (and that provider's URL / key).

```python
from ..core.factory import NotificationFactory
from ..core.interface import NotificationInterface
from ..core.models import NotificationResponse, Recipient
from ..utils.events import ids


class AcmeNotifier(NotificationInterface):
    def send(self, event, entity_id, payload, recipient: Recipient, notification_id=None) -> NotificationResponse:
        workflow_id, nid = ids(event, entity_id, notification_id)
        ...


NotificationFactory.register("acme", AcmeNotifier)
```

A provider that is not in this package can still call `NotificationFactory.register("acme", AcmeNotifier)` before `get_notifier()`.
