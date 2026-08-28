import json

import responses

from aps_forma_issues.exceptions import IssueCreationError
from aps_forma_issues.issues import create_issue
from aps_forma_issues.models import CustomAttribute, IssueInput


class FakeAuth:
    def get_token(self) -> str:
        return "fake-token"


@responses.activate
def test_create_issue_success(config):
    responses.add(
        responses.POST,
        f"{config.base_url}/construction/issues/v1/projects/{config.project_id}/issues",
        json={"id": "issue-1"},
        status=201,
    )
    issue = IssueInput(
        title="Possible work near suspended load",
        description="desc",
        issue_subtype_id="sub-1",
        assigned_to="user-1",
        custom_attributes=[CustomAttribute("attr-1", "value-1")],
    )

    result = create_issue(config, FakeAuth(), issue)

    assert result == {"id": "issue-1"}
    sent_body = json.loads(responses.calls[0].request.body)
    assert sent_body["title"] == "Possible work near suspended load"
    assert sent_body["customAttributes"] == [
        {"attributeDefinitionId": "attr-1", "value": "value-1"}
    ]


@responses.activate
def test_create_issue_defaults_to_published_true(config):
    # CONFIRMED LIVE: published=None/null creates an issue invisible in
    # the normal Forma Build UI (a private draft) — the default must not
    # regress back to that silently.
    responses.add(
        responses.POST,
        f"{config.base_url}/construction/issues/v1/projects/{config.project_id}/issues",
        json={"id": "issue-1"},
        status=201,
    )
    issue = IssueInput(
        title="t", description="d", issue_subtype_id="s", assigned_to="u"
    )

    create_issue(config, FakeAuth(), issue)

    sent_body = json.loads(responses.calls[0].request.body)
    assert sent_body["published"] is True


@responses.activate
def test_create_issue_sends_optional_fields_and_null_assignee(config):
    responses.add(
        responses.POST,
        f"{config.base_url}/construction/issues/v1/projects/{config.project_id}/issues",
        json={"id": "issue-1"},
        status=201,
    )
    issue = IssueInput(
        title="No user",
        description="The door is missing a screw, please fix this",
        issue_subtype_id="dd25b703-f96f-43f6-93ba-5115a6e58c2a",
        assigned_to=None,
        root_cause_id="4ea3583b-4d6c-4295-b3c2-77bb3079b6bb",
        start_date="2026-08-26",
        location_details="issue location details",
        published=True,
        custom_attributes=[CustomAttribute("attr-1", "value-1")],
    )

    create_issue(config, FakeAuth(), issue)

    sent_body = json.loads(responses.calls[0].request.body)
    assert sent_body["rootCauseId"] == "4ea3583b-4d6c-4295-b3c2-77bb3079b6bb"
    assert sent_body["assignedTo"] is None
    assert sent_body["startDate"] == "2026-08-26"
    assert sent_body["locationDetails"] == "issue location details"
    assert sent_body["published"] is True
    assert sent_body["customAttributes"] == [
        {"attributeDefinitionId": "attr-1", "value": "value-1"}
    ]


@responses.activate
def test_create_issue_failure_raises(config):
    responses.add(
        responses.POST,
        f"{config.base_url}/construction/issues/v1/projects/{config.project_id}/issues",
        json={"error": "bad request"},
        status=400,
    )
    issue = IssueInput(title="t", description="d", issue_subtype_id="s", assigned_to="u")

    try:
        create_issue(config, FakeAuth(), issue)
        assert False, "expected IssueCreationError"
    except IssueCreationError:
        pass
