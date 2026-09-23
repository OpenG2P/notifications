# ruff: noqa: E402

from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .core.factory import NotificationFactory


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        NotificationFactory()
        NotificationFactory.get_notifier()
