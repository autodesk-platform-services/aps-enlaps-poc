"""Create and look up Data Management Items.

An item created here and linked to an
Issue via `relationships.py` renders as a real attachment thumbnail on
the Issue, while staying browsable normally in Files/Docs.

**Documentation**: https://aps.autodesk.com/en/docs/data/v2/tutorials/upload-file/
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import ItemCreationError
from .storage import _dm_project_id

ITEMS_PATH = "/data/v1/projects/{project_id}/items"
ITEM_PATH = "/data/v1/projects/{project_id}/items/{lineage_urn}"


def _uniquify_filename(filename: str) -> str:
    """Appends a short unique suffix to `filename`, preserving its stem
    and extension. Item names must be unique project-wide (see module
    docstring); without this, every call using the same filename after
    the first one would fail.
    """
    path = PurePosixPath(filename)
    suffix = path.suffix
    stem = path.stem or filename
    return f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"


def create_item_in_folder(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    storage_urn: str,
    filename: str,
    folder_id: str,
    description: str | None = None,
    session: requests.Session | None = None,
) -> str:
    """Creates an Item (a visible file, with its first Version)
    inside `folder_id`, backed by the bytes already at `storage_urn`

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        storage_urn (str): Storage URN returned by
            `storage.upload_image_bytes`.
        filename (str): Desired file name. The name actually used is
            this plus a short unique suffix — see `_uniquify_filename`.
        folder_id (str): Docs folder to create the item in.
        description (str, optional): Description to set on the item via
            a follow-up `PATCH`. Left unset if omitted.
        session (requests.Session, optional): Session to reuse.

    Returns:
        str: The created item's lineage URN.

    Raises:
        ItemCreationError: If creation, or setting the description, fails.
    """
    session = session or requests.Session()
    dm_project_id = _dm_project_id(config.project_id)
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/vnd.api+json",
    }
    url = config.base_url + ITEMS_PATH.format(project_id=dm_project_id)
    unique_filename = _uniquify_filename(filename)
    # JSON:API local reference id linking `relationships.tip` to the
    # `included` version below. Must be the literal string "1" — the
    # API's schema enums it to that one value, it is not a free-form
    # per-request id.
    local_version_id = "1"
    body = {
        "jsonapi": {"version": "1.0"},
        "data": {
            "type": "items",
            "attributes": {
                "displayName": unique_filename,
                "extension": {"type": "items:autodesk.bim360:File", "version": "1.0"},
            },
            "relationships": {
                "tip": {"data": {"type": "versions", "id": local_version_id}},
                "parent": {"data": {"type": "folders", "id": folder_id}},
            },
        },
        "included": [
            {
                "type": "versions",
                "id": local_version_id,
                "attributes": {
                    "name": unique_filename,
                    "extension": {
                        "type": "versions:autodesk.bim360:File",
                        "version": "1.0",
                    },
                },
                "relationships": {
                    "storage": {"data": {"type": "objects", "id": storage_urn}}
                },
            }
        ],
    }
    resp = session.post(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code not in (200, 201):
        raise ItemCreationError(f"Could not create item: {resp.status_code} {resp.text}")
    lineage_urn = resp.json()["data"]["id"]

    if description:
        _set_item_description(config, auth, lineage_urn, description, session)

    return lineage_urn


def _set_item_description(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    lineage_urn: str,
    description: str,
    session: requests.Session,
) -> None:
    dm_project_id = _dm_project_id(config.project_id)
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/vnd.api+json",
    }
    url = config.base_url + ITEM_PATH.format(
        project_id=dm_project_id, lineage_urn=lineage_urn
    )
    body = {
        "jsonapi": {"version": "1.0"},
        "data": {
            "type": "items",
            "id": lineage_urn,
            "attributes": {
                "extension": {
                    "type": "items:autodesk.bim360:File",
                    "version": "1.0",
                    "data": {"description": description},
                },
            },
        },
    }
    resp = session.patch(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code != 200:
        raise ItemCreationError(
            f"Could not set item description: {resp.status_code} {resp.text}"
        )


def get_item_web_view_url(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    lineage_urn: str,
    session: requests.Session | None = None,
) -> str | None:
    """Looks up a direct link to an item in the Files/Docs UI.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        lineage_urn (str): Lineage URN returned by `create_item_in_folder`.
        session (requests.Session, optional): Session to reuse.

    Returns:
        str | None: The web-view URL, or `None` if unavailable.
    """
    session = session or requests.Session()
    url = config.base_url + ITEM_PATH.format(
        project_id=_dm_project_id(config.project_id), lineage_urn=lineage_urn
    )
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    resp = session.get(url, headers=headers, timeout=config.request_timeout_seconds)
    if resp.status_code != 200:
        return None
    try:
        return resp.json()["data"]["links"]["webView"]["href"]
    except (KeyError, TypeError, ValueError):
        return None
