"""Link an existing Data Management Item to an Issue.

This is the "attach" step: linking an item created by `items.py` to an
Issue this way renders as a visible attachment thumbnail on the
Issue in the Forma Build UI.

**Documentation**: https://aps.autodesk.com/en/docs/acc/v1/tutorials/relationships/relationships-create

The Issue resource's own `attachmentCount`/`linkedDocuments` fields do
not reflect a link created this way — don't rely on those fields to
check whether a link exists.
"""

from __future__ import annotations

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import AttachmentError

RELATIONSHIPS_PATH = "/bim360/relationship/v2/containers/{project_id}/relationships"

_ISSUE_DOMAIN = "autodesk-bim360-issue"
_DOCUMENT_DOMAIN = "autodesk-bim360-documentmanagement"


def link_issue_to_document(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    issue_id: str,
    lineage_urn: str,
    session: requests.Session | None = None,
) -> list[dict]:
    """Links a Data Management item to an Issue.

    Uses the bare (unprefixed) project ID — this endpoint is in the
    same family as Issues, not Data Management, unlike `storage.py`.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        issue_id (str): ID of the Issue to link to.
        lineage_urn (str): Lineage URN of the item to link, as returned
            by `items.create_item_in_folder`.
        session (requests.Session, optional): Session to reuse.

    Returns:
        list[dict]: The created relationship(s), parsed from the response.

    Raises:
        AttachmentError: If the link request fails.
    """
    session = session or requests.Session()
    url = config.base_url + RELATIONSHIPS_PATH.format(project_id=config.project_id)
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
    }
    body = [
        {
            "entities": [
                {"domain": _ISSUE_DOMAIN, "type": "issue", "id": issue_id},
                {"domain": _DOCUMENT_DOMAIN, "type": "documentlineage", "id": lineage_urn},
            ]
        }
    ]
    resp = session.put(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code != 200:
        raise AttachmentError(
            f"Could not link item to issue: {resp.status_code} {resp.text}"
        )
    return resp.json()
