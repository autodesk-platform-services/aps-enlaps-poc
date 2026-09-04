"""Create Issues via the Forma Issues API (`Construction.Issues`)."""

from __future__ import annotations

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import IssueCreationError, IssueFetchError
from .models import IssueInput

ISSUES_PATH = "/construction/issues/v1/projects/{project_id}/issues"
ISSUE_PATH = "/construction/issues/v1/projects/{project_id}/issues/{issue_id}"
ISSUE_TYPES_PATH = "/construction/issues/v1/projects/{project_id}/issue-types"


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


def list_issues(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    limit: int = 100,
    offset: int = 0,
    session: requests.Session | None = None,
) -> dict:
    """Lists Issues in the target project, newest page first.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        limit (int, optional): Max results per page (API-capped at 200).
        offset (int, optional): Pagination offset.
        session (requests.Session, optional): Session to reuse.

    Returns:
        dict: `{"pagination": {"limit", "offset", "totalResults", "next"},
        "results": [...]}`.

    Raises:
        IssueFetchError: If the request fails.
    """
    session = session or requests.Session()
    url = config.base_url + ISSUES_PATH.format(project_id=config.project_id)
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    params = {"limit": limit, "offset": offset}
    resp = session.get(
        url, params=params, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code != 200:
        raise IssueFetchError(f"Listing issues failed: {resp.status_code} {resp.text}")
    return resp.json()


def get_issue(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    issue_id: str,
    session: requests.Session | None = None,
) -> dict:
    """Fetches a single Issue by ID.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        issue_id (str): ID of the issue to fetch.
        session (requests.Session, optional): Session to reuse.

    Returns:
        dict: Parsed issue.

    Raises:
        IssueFetchError: If the request fails.
    """
    session = session or requests.Session()
    url = config.base_url + ISSUE_PATH.format(
        project_id=config.project_id, issue_id=issue_id
    )
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    resp = session.get(url, headers=headers, timeout=config.request_timeout_seconds)
    if resp.status_code != 200:
        raise IssueFetchError(f"Fetching issue failed: {resp.status_code} {resp.text}")
    return resp.json()


def get_issue_types(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    include_subtypes: bool = True,
    session: requests.Session | None = None,
) -> dict:
    """Lists Issue types configured on the target project.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        include_subtypes (bool, optional): Whether to include each
            type's subtypes inline. Defaults to `True`.
        session (requests.Session, optional): Session to reuse.

    Returns:
        dict: `{"pagination": {...}, "results": [{"id", "title",
        "subtypes": [{"id", "issueTypeId", "title", ...}], ...}]}`.

    Raises:
        IssueFetchError: If the request fails.
    """
    session = session or requests.Session()
    url = config.base_url + ISSUE_TYPES_PATH.format(project_id=config.project_id)
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    params = {"include": "subtypes"} if include_subtypes else {}
    resp = session.get(
        url, params=params, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code != 200:
        raise IssueFetchError(
            f"Fetching issue types failed: {resp.status_code} {resp.text}"
        )
    return resp.json()
