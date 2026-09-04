"""Attach an uploaded image directly to an Issue via the Issues API's
own attachments endpoint — an alternative to `items.py` + `relationships.py`.

**Documentation**: https://aps.autodesk.com/en/docs/acc/v1/overview/field-guide/issues/#limitations

This is the simpler of the two attach paths: no Docs folder permission
is required on the calling identity, unlike `items.create_item_in_folder`.
The tradeoff is accessibility — Autodesk auto-creates its own folder per
attachment (observed: a folder literally named `"3"`, nested under a
folder marked `hidden: True`, then a level not even readable), so
there's no way to browse to where the file landed. `IssueResult.web_view_url`
(via `items.get_item_web_view_url`) still works here — it doesn't
depend on which folder the item is in.

"""

from __future__ import annotations

import uuid

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import AttachmentError

ATTACHMENTS_PATH = "/construction/issues/v1/projects/{project_id}/attachments"
ATTACHMENT_ITEMS_PATH = "/construction/issues/v1/projects/{project_id}/attachments/{issue_id}/items"


def attach_image_to_issue(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    issue_id: str,
    storage_urn: str,
    filename: str,
    session: requests.Session | None = None,
) -> dict:
    """Attaches an already-uploaded image to an Issue.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        issue_id (str): ID of the issue to attach to.
        storage_urn (str): Storage URN returned by
            `storage.upload_image_bytes`.
        filename (str): Display name for the attachment.
        session (requests.Session, optional): Session to reuse.

    Returns:
        dict: Parsed response, e.g. `{"attachments": [{"attachmentId": ...,
        "lineageUrn": ..., ...}]}`.

    Raises:
        AttachmentError: If the attach request fails.
    """
    session = session or requests.Session()
    url = config.base_url + ATTACHMENTS_PATH.format(project_id=config.project_id)
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
    }
    body = {
        "isNew": True,
        "domainEntityId": issue_id,
        "attachments": [
            {
                "attachmentId": str(uuid.uuid4()),
                "displayName": filename,
                "fileName": filename,
                "attachmentType": "issue-attachment",
                "storageUrn": storage_urn,
            }
        ],
    }
    resp = session.post(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code not in (200, 201):
        raise AttachmentError(f"Attachment failed: {resp.status_code} {resp.text}")
    return resp.json()


def list_attachments(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    issue_id: str,
    session: requests.Session | None = None,
) -> list[dict]:
    """Lists attachments on an Issue, created via this module's attach path.

    !!!Important!!!
    Only attachments created via `attach_image_to_issue` show up here.
    is a reliable predicate for whether this call is worth making.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        issue_id (str): ID of the issue to list attachments for.
        session (requests.Session, optional): Session to reuse.

    Returns:
        list[dict]: Each with `attachmentId`, `displayName`, `fileName`,
        `storageUrn`, `fileSize`, `fileType`, etc.

    Raises:
        AttachmentError: If the request fails.
    """
    session = session or requests.Session()
    url = config.base_url + ATTACHMENT_ITEMS_PATH.format(
        project_id=config.project_id, issue_id=issue_id
    )
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    resp = session.get(url, headers=headers, timeout=config.request_timeout_seconds)
    if resp.status_code != 200:
        raise AttachmentError(
            f"Listing attachments failed: {resp.status_code} {resp.text}"
        )
    return resp.json().get("attachments", [])
