"""Builds dashboard/detail view models on top of `aps_forma_issues`.

`aps_forma_issues` only wraps the Construction Issues API, which reports
`assignedTo`/`ownerId` as opaque Autodesk user IDs, not names. Resolving
those to display names needs the separate Account Admin API — a lookup
that belongs here, in the app, rather than inside the library.
"""

from __future__ import annotations

import requests
from aps_forma_issues import FormaIssuesClient, SafetyRootCause

_ADMIN_USERS_PATH = "/construction/admin/v1/projects/{project_id}/users"

# Human-readable titles for the preset root causes, derived from the enum
# member names themselves (e.g. HUMAN_ERROR -> "Human Error") — avoids a
# separate hardcoded name table that could drift from root_causes.py.
_ROOT_CAUSE_TITLES = {
    member.value: member.name.replace("_", " ").title() for member in SafetyRootCause
}


def fetch_user_names(
    token: str, base_url: str, project_id: str, timeout: int = 15
) -> dict[str, str]:
    """Maps Autodesk user IDs to display names for the target project.

    Args:
        token (str): A 3-legged access token with the `account:read` scope
            — Issues-API-only scopes (`user-profile:read data:read
            data:write`) get a 403 here (confirmed live).
        base_url (str): APS API base URL.
        project_id (str): Target project ID.
        timeout (int, optional): Per-request timeout in seconds.

    Returns:
        dict[str, str]: `{autodeskId: name}` for every project member.
        Empty if the lookup fails — callers should fall back to raw IDs.
    """
    names: dict[str, str] = {}
    path = _ADMIN_USERS_PATH.format(project_id=project_id)
    headers = {"Authorization": f"Bearer {token}"}
    params: dict | None = {"limit": 200, "offset": 0}
    url = base_url + path

    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        if resp.status_code != 200:
            break
        data = resp.json()
        for user in data.get("results", []):
            names[user["autodeskId"]] = user.get("name") or user["autodeskId"]

        next_path = data.get("pagination", {}).get("next")
        url = base_url + next_path if next_path else None
        params = None  # `next` already encodes limit/offset as query params

    return names


def _root_cause_title(root_cause_id: str | None) -> str:
    if not root_cause_id:
        return "-"
    return _ROOT_CAUSE_TITLES.get(root_cause_id, root_cause_id)


def build_issue_view(
    raw_issue: dict,
    type_titles: dict[str, str],
    subtype_titles: dict[str, str],
    user_names: dict[str, str],
) -> dict:
    """Flattens one raw Issues-API issue into template-friendly fields.

    Args:
        raw_issue (dict): One entry from `FormaIssuesClient.list_issues`'s
            `results`, or the return value of `get_issue`.
        type_titles (dict[str, str]): `{issueTypeId: title}`.
        subtype_titles (dict[str, str]): `{issueSubtypeId: title}`.
        user_names (dict[str, str]): `{autodeskId: name}`, from
            `fetch_user_names`.

    Returns:
        dict: Fields matching the dashboard table / detail modal columns.
    """
    assigned_to = raw_issue.get("assignedTo")
    owner_id = raw_issue.get("ownerId")
    attachment_count = raw_issue.get("attachmentCount") or 0
    return {
        "id": raw_issue["id"],
        "display_id": raw_issue.get("displayId"),
        "title": raw_issue.get("title", ""),
        "description": raw_issue.get("description") or "-",
        "type": type_titles.get(raw_issue.get("issueTypeId"), "-"),
        "subtype": subtype_titles.get(raw_issue.get("issueSubtypeId"), "-"),
        "assigned_to": user_names.get(assigned_to, assigned_to or "Unassigned"),
        "owner": user_names.get(owner_id, owner_id or "-"),
        "root_cause": _root_cause_title(raw_issue.get("rootCauseId")),
        "location": raw_issue.get("locationDetails") or "-",
        # There's no confirmed endpoint to list attachment file details
        # (see aps-forma-issues/README.md) — attachmentCount is the best
        # available proxy for the "Document" field.
        "document": f"{attachment_count} attachment(s)" if attachment_count else "No attachments",
        # Lets the dashboard's JS decide whether it's worth calling
        # /api/issues/<id>/attachments at all — only endpoint-path
        # attachments (see attachments.list_attachments) count here.
        "attachment_count": attachment_count,
        "due_date": raw_issue.get("dueDate") or "-",
        "status": raw_issue.get("status", "-"),
    }


def fetch_dashboard_issues(
    client: FormaIssuesClient, token: str, base_url: str, project_id: str
) -> list[dict]:
    """Fetches and flattens every issue in the project for the dashboard.

    Args:
        client (FormaIssuesClient): Client to list issues/issue types with.
        token (str): Access token, reused for the Account Admin users
            lookup (a separate API `client` doesn't cover).
        base_url (str): APS API base URL.
        project_id (str): Target project ID.

    Returns:
        list[dict]: One flattened view model per issue (see
        `build_issue_view`), most-recently-created first.

    Raises:
        IssueFetchError: If listing issues or issue types fails.
    """
    issue_types = client.get_issue_types()
    type_titles: dict[str, str] = {}
    subtype_titles: dict[str, str] = {}
    for issue_type in issue_types.get("results", []):
        type_titles[issue_type["id"]] = issue_type["title"]
        for subtype in issue_type.get("subtypes", []):
            subtype_titles[subtype["id"]] = subtype["title"]

    user_names = fetch_user_names(token, base_url, project_id)

    # limit=200 is the API's own per-page cap — enough to cover this
    # PoC-scale project (53 issues) in one call. A production version
    # would follow pagination.next instead of assuming a single page.
    raw_issues = client.list_issues(limit=200).get("results", [])
    views = [
        build_issue_view(issue, type_titles, subtype_titles, user_names)
        for issue in raw_issues
    ]
    views.sort(key=lambda v: v["display_id"] or 0, reverse=True)
    return views
