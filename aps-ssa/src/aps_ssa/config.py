"""Runtime configuration for the SSA client."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SsaConfig:
    client_id: str
    client_secret: str
    service_account_id: str
    key_id: str
    private_key_path: str

    base_url: str = "https://developer.api.autodesk.com"
    scopes: str = "data:read data:write data:create account:write account:read"
    request_timeout_seconds: int = 15

    @classmethod
    def from_env(cls) -> "SsaConfig":
        return cls(
            client_id=_require("APS_CLIENT_ID"),
            client_secret=_require("APS_CLIENT_SECRET"),
            service_account_id=_require("APS_SERVICE_ACCOUNT_ID"),
            key_id=_require("APS_SSA_KEY_ID"),
            private_key_path=_require("APS_SSA_PRIVATE_KEY_PATH"),
            base_url=os.environ.get(
                "APS_BASE_URL", "https://developer.api.autodesk.com"
            ),
            scopes=os.environ.get(
                "APS_SCOPES",
                "data:read data:write data:create account:write account:read",
            ),
            request_timeout_seconds=int(
                os.environ.get("APS_REQUEST_TIMEOUT_SECONDS", "15")
            ),
        )


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
