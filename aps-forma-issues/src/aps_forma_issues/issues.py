"""Create Issues via the Forma Issues API (`Construction.Issues`)."""

from __future__ import annotations

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import IssueCreationError
from .models import IssueInput

ISSUES_PATH = "/construction/issues/v1/projects/{project_id}/issues"


def create_issue(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    issue: IssueInput,
    session: requests.Session | None = None,
) -> dict:
    """Creates an Issue.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        issue (IssueInput): Fields for the new issue.
        session (requests.Session, optional): Session to reuse.

    Returns:
        dict: Parsed response for the created issue.

    Raises:
        IssueCreationError: If creation fails.
    """
    session = session or requests.Session()
    url = config.base_url + ISSUES_PATH.format(project_id=config.project_id)
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/json",
    }
    body = {
        "title": issue.title,
        "description": issue.description,
        "issueSubtypeId": issue.issue_subtype_id,
        "rootCauseId": issue.root_cause_id,
        "status": issue.status,
        "assignedTo": issue.assigned_to,
        "assignedToType": issue.assigned_to_type,
        "startDate": issue.start_date,
        "locationDetails": issue.location_details,
        "published": issue.published,
        "customAttributes": [
            {"attributeDefinitionId": ca.attribute_definition_id, "value": ca.value}
            for ca in issue.custom_attributes
        ],
    }
    resp = session.post(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code not in (200, 201):
        raise IssueCreationError(
            f"Issue creation failed: {resp.status_code} {resp.text}"
        )
    return resp.json()
