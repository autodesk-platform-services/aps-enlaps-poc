"""Runtime configuration for the Forma Issues client.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FormaIssuesConfig:
    """Configuration for `FormaIssuesClient`.

    Attributes:
        project_id (str): Target Forma/ACC project ID.
        upload_folder_id (str): Docs folder that uploaded images are
            placed in.
        base_url (str, optional): Base URL for API calls.
        request_timeout_seconds (int, optional): Timeout applied to
            every HTTP request made by this library.
    """

    project_id: str
    upload_folder_id: str

    base_url: str = "https://developer.api.autodesk.com"
    request_timeout_seconds: int = 15

    @classmethod
    def from_env(cls) -> FormaIssuesConfig:
        """Builds a config from environment variables.

        Reads `ACC_PROJECT_ID`, `ACC_UPLOAD_FOLDER_ID`, and optionally
        `ACC_BASE_URL` / `REQUEST_TIMEOUT_SECONDS`.

        Returns:
            FormaIssuesConfig: The resulting config.

        Raises:
            RuntimeError: If a required environment variable is missing.
        """
        return cls(
            project_id=_require("ACC_PROJECT_ID"),
            upload_folder_id=_require("ACC_UPLOAD_FOLDER_ID"),
            base_url=os.environ.get(
                "ACC_BASE_URL", "https://developer.api.autodesk.com"
            ),
            request_timeout_seconds=int(
                os.environ.get("REQUEST_TIMEOUT_SECONDS", "15")
            ),
        )


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
