import importlib
import re

from openg2p_fastapi_common.service import BaseService

from .interface import NotificationInterface
from ..config import Settings

_PROVIDER_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class NotificationFactory(BaseService):
    _providers: dict[str, type[NotificationInterface]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type[NotificationInterface]) -> None:
        cls._providers[name.strip().lower()] = provider_cls

    @classmethod
    def get_notifier(cls) -> NotificationInterface:
        existing = NotificationInterface.get_component()
        if existing is not None:
            return existing
        return cls._build()

    @classmethod
    def _build(cls) -> NotificationInterface:
        name = (Settings.get_config().provider or "").strip().lower()
        if not _PROVIDER_NAME.match(name):
            raise ValueError(f"Unknown notification provider {name!r}")
        if name not in cls._providers:
            try:
                importlib.import_module(f"openg2p_notification.providers.{name}")
            except ModuleNotFoundError as exc:
                raise ValueError(f"Unknown notification provider {name!r}") from exc
        provider_cls = cls._providers.get(name)
        if provider_cls is None:
            raise ValueError(f"Unknown notification provider {name!r}")
        return provider_cls()
