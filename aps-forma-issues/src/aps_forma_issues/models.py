"""Data types for building Issues and reading back results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CustomAttribute:
    """A single custom attribute value to set on an Issue.

    Attributes:
        attribute_definition_id (str): ID of the custom attribute
            definition configured on the target project's issue subtype.
        value (str): Value to set for that attribute.
    """

    attribute_definition_id: str
    value: str


@dataclass(frozen=True)
class IssueInput:
    """Fields for creating an Issue.

    Attributes:
        title (str): Issue title.
        description (str): Issue description.
        issue_subtype_id (str): ID of the issue subtype to create under.
        assigned_to (str, optional): User ID to assign the issue to.
            Unassigned if omitted.
        assigned_to_type (str, optional): One of "user", "company", or
            "role". Defaults to "user".
        status (str, optional): Initial status. Defaults to "open".
        root_cause_id (str, optional): ID of a root cause — see
            `SafetyRootCause` for a preset list.
        start_date (str, optional): A bare `YYYY-MM-DD` date, e.g.
            `datetime.date.today().isoformat()`.
        location_details (str, optional): Free-text location description.
        published (bool, optional): Whether the issue is published.
            Defaults to `True` - meaning it is visible in UI
        custom_attributes (list[CustomAttribute], optional): Custom
            attribute values to set.
    """

    title: str
    description: str
    issue_subtype_id: str
    assigned_to: str | None = None
    assigned_to_type: str = "user"
    status: str = "open"
    root_cause_id: str | None = None
    start_date: str | None = None
    location_details: str | None = None
    published: bool | None = True
    custom_attributes: list[CustomAttribute] = field(default_factory=list)


@dataclass(frozen=True)
class IssueResult:
    """Result of `FormaIssuesClient.create_issue_with_image`.

    Attributes:
        issue_id (str): ID of the created Issue.
        attachment_id (str, optional): ID of the relationship linking
            the uploaded image to the Issue, if linking succeeded.
        raw_issue (dict): Parsed response from creating the Issue.
        raw_attachment (dict, optional): Parsed response from uploading
            and linking the image.
        web_view_url (str, optional): Direct link to the uploaded image
            in the Files/Docs UI. `None` if the best-effort lookup
            failed. There is no delete API for Issues, so this is the
            practical way to find something to delete manually later.
    """

    issue_id: str
    attachment_id: str | None
    raw_issue: dict
    raw_attachment: dict | None
    web_view_url: str | None = None
