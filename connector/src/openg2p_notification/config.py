import json
from typing import Any

from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic import field_validator
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="notification_",
        env_file=".env",
        extra="allow",
    )

    enabled: bool = True
    provider: str = "novu"
    provider_url: str = "http://localhost:3000"
    provider_api_key: str = ""
    provider_timeout_ms: int = 20_000
    workflows: dict[str, str] = {}

    @field_validator("workflows", mode="before")
    @classmethod
    def _parse_workflows(cls, value: Any) -> dict[str, str]:
        if value is None or value == "":
            return {}
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict):
            raise ValueError("NOTIFICATION_WORKFLOWS must be a JSON object")
        return {str(key).strip(): str(item).strip() for key, item in value.items() if str(key).strip()}
