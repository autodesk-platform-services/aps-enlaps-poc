import json

import responses

from aps_forma_issues.exceptions import AttachmentError
from aps_forma_issues.relationships import link_issue_to_document


class FakeAuth:
    def get_token(self) -> str:
        return "fake-token"


def _relationships_url(config):
    # Bare project id, unlike the Data Management endpoints in items.py/storage.py.
    return f"{config.base_url}/bim360/relationship/v2/containers/{config.project_id}/relationships"


@responses.activate
def test_link_issue_to_document_success(config):
    responses.add(
        responses.PUT,
        _relationships_url(config),
        json=[{"id": "rel-1", "entities": []}],
        status=200,
    )

    result = link_issue_to_document(config, FakeAuth(), "issue-1", "urn:fake-lineage")

    assert result == [{"id": "rel-1", "entities": []}]
    sent_body = json.loads(responses.calls[0].request.body)
    entities = sent_body[0]["entities"]
    assert {"domain": "autodesk-bim360-issue", "type": "issue", "id": "issue-1"} in entities
    assert {
        "domain": "autodesk-bim360-documentmanagement",
        "type": "documentlineage",
        "id": "urn:fake-lineage",
    } in entities


@responses.activate
def test_link_issue_to_document_raises_on_failure(config):
    responses.add(
        responses.PUT,
        _relationships_url(config),
        json={"title": "bad request"},
        status=400,
    )

    try:
        link_issue_to_document(config, FakeAuth(), "issue-1", "urn:fake-lineage")
        assert False, "expected AttachmentError"
    except AttachmentError:
        pass
