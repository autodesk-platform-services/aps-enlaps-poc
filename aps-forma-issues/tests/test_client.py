from aps_forma_issues import FormaIssuesClient, IssueInput
from aps_forma_issues.client import _issues, _items, _relationships, _storage


class FakeAuth:
    def get_token(self) -> str:
        return "fake-token"


def test_create_issue_with_image_orchestrates_calls(config, monkeypatch):
    calls = []

    def fake_create_issue(cfg, auth, issue, session=None):
        calls.append(("create_issue", issue.title))
        return {"id": "issue-1", "displayId": 42}

    def fake_upload(cfg, auth, data, filename=None, session=None):
        calls.append(("upload", filename, data))
        return "urn:fake-storage"

    def fake_create_item(cfg, auth, storage_urn, filename, folder_id, description=None, session=None):
        calls.append(("create_item", storage_urn, filename, folder_id, description))
        return "urn:fake-lineage"

    def fake_link(cfg, auth, issue_id, lineage_urn, session=None):
        calls.append(("link", issue_id, lineage_urn))
        return [{"id": "rel-1"}]

    def fake_web_view(cfg, auth, lineage_urn, session=None):
        calls.append(("web_view", lineage_urn))
        return "https://acc.autodesk.com/docs/files/..."

    monkeypatch.setattr(_issues, "create_issue", fake_create_issue)
    monkeypatch.setattr(_storage, "upload_image_bytes", fake_upload)
    monkeypatch.setattr(_items, "create_item_in_folder", fake_create_item)
    monkeypatch.setattr(_relationships, "link_issue_to_document", fake_link)
    monkeypatch.setattr(_items, "get_item_web_view_url", fake_web_view)

    client = FormaIssuesClient(config, FakeAuth())
    issue_input = IssueInput(
        title="Possible work near suspended load",
        description="desc",
        issue_subtype_id="sub-1",
        assigned_to="user-1",
    )

    result = client.create_issue_with_image(issue_input, image_bytes=b"data", filename="photo.jpg")

    assert result.issue_id == "issue-1"
    assert result.attachment_id == "rel-1"
    assert result.web_view_url == "https://acc.autodesk.com/docs/files/..."
    assert calls[0] == ("create_issue", "Possible work near suspended load")
    assert calls[1] == ("upload", "photo.jpg", b"data")
    # Description should reference the issue's display id, not just its raw id.
    assert calls[2] == (
        "create_item",
        "urn:fake-storage",
        "photo.jpg",
        config.upload_folder_id,
        "Linked to Issue #42: Possible work near suspended load",
    )
    assert calls[3] == ("link", "issue-1", "urn:fake-lineage")
    assert calls[4] == ("web_view", "urn:fake-lineage")


def test_create_issue_with_image_handles_missing_relationships(config, monkeypatch):
    monkeypatch.setattr(_issues, "create_issue", lambda *a, **k: {"id": "issue-1"})
    monkeypatch.setattr(_storage, "upload_image_bytes", lambda *a, **k: "urn:fake-storage")
    monkeypatch.setattr(_items, "create_item_in_folder", lambda *a, **k: "urn:fake-lineage")
    monkeypatch.setattr(_relationships, "link_issue_to_document", lambda *a, **k: [])
    monkeypatch.setattr(_items, "get_item_web_view_url", lambda *a, **k: None)

    client = FormaIssuesClient(config, FakeAuth())
    issue_input = IssueInput(
        title="t", description="d", issue_subtype_id="s", assigned_to="u"
    )

    result = client.create_issue_with_image(issue_input, image_bytes=b"data")

    assert result.issue_id == "issue-1"
    assert result.attachment_id is None
    assert result.web_view_url is None


def test_create_issue_with_image_falls_back_to_raw_id_without_display_id(config, monkeypatch):
    monkeypatch.setattr(_issues, "create_issue", lambda *a, **k: {"id": "issue-1"})
    monkeypatch.setattr(_storage, "upload_image_bytes", lambda *a, **k: "urn:fake-storage")

    captured = {}

    def fake_create_item(cfg, auth, storage_urn, filename, folder_id, description=None, session=None):
        captured["description"] = description
        return "urn:fake-lineage"

    monkeypatch.setattr(_items, "create_item_in_folder", fake_create_item)
    monkeypatch.setattr(_relationships, "link_issue_to_document", lambda *a, **k: [{"id": "rel-1"}])
    monkeypatch.setattr(_items, "get_item_web_view_url", lambda *a, **k: None)

    client = FormaIssuesClient(config, FakeAuth())
    issue_input = IssueInput(
        title="t", description="d", issue_subtype_id="s", assigned_to="u"
    )

    client.create_issue_with_image(issue_input, image_bytes=b"data")

    assert captured["description"] == "Linked to Issue issue-1: t"


def test_attach_image_to_issue_defaults_description_when_not_given(config, monkeypatch):
    monkeypatch.setattr(_storage, "upload_image_bytes", lambda *a, **k: "urn:fake-storage")

    captured = {}

    def fake_create_item(cfg, auth, storage_urn, filename, folder_id, description=None, session=None):
        captured["description"] = description
        return "urn:fake-lineage"

    monkeypatch.setattr(_items, "create_item_in_folder", fake_create_item)
    monkeypatch.setattr(_relationships, "link_issue_to_document", lambda *a, **k: [{"id": "rel-1"}])

    client = FormaIssuesClient(config, FakeAuth())
    client.attach_image_to_issue("issue-1", b"data", "photo.jpg")

    assert captured["description"] == "Linked to Forma Issue issue-1"
