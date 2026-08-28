import json
import re

import responses

from aps_forma_issues.exceptions import ItemCreationError
from aps_forma_issues.items import (
    _uniquify_filename,
    create_item_in_folder,
    get_item_web_view_url,
)


class FakeAuth:
    def get_token(self) -> str:
        return "fake-token"


def _items_collection_url(config):
    return f"{config.base_url}/data/v1/projects/b.{config.project_id}/items"


def _item_url_pattern(config):
    return re.compile(
        rf"{re.escape(config.base_url)}/data/v1/projects/"
        rf"b\.{re.escape(config.project_id)}/items/.+"
    )


@responses.activate
def test_get_item_web_view_url_success(config):
    responses.add(
        responses.GET,
        _item_url_pattern(config),
        json={"data": {"links": {"webView": {"href": "https://acc.autodesk.com/docs/files/..."}}}},
        status=200,
    )

    url = get_item_web_view_url(config, FakeAuth(), "urn:fake-lineage")

    assert url == "https://acc.autodesk.com/docs/files/..."


@responses.activate
def test_get_item_web_view_url_returns_none_on_http_error(config):
    responses.add(
        responses.GET,
        _item_url_pattern(config),
        json={"error": "forbidden"},
        status=403,
    )

    url = get_item_web_view_url(config, FakeAuth(), "urn:fake-lineage")

    assert url is None


@responses.activate
def test_get_item_web_view_url_returns_none_on_unexpected_shape(config):
    responses.add(
        responses.GET,
        _item_url_pattern(config),
        json={"data": {"links": {}}},
        status=200,
    )

    url = get_item_web_view_url(config, FakeAuth(), "urn:fake-lineage")

    assert url is None


@responses.activate
def test_create_item_in_folder_success_without_description(config):
    responses.add(
        responses.POST,
        _items_collection_url(config),
        json={"data": {"id": "urn:fake-lineage"}},
        status=201,
    )

    lineage_urn = create_item_in_folder(
        config, FakeAuth(), "urn:fake-storage", "photo.jpg", "urn:fake-folder"
    )

    assert lineage_urn == "urn:fake-lineage"
    sent_body = json.loads(responses.calls[0].request.body)
    # Filename is uniquified (see _uniquify_filename) — not sent verbatim.
    sent_name = sent_body["data"]["attributes"]["displayName"]
    assert sent_name.startswith("photo_") and sent_name.endswith(".jpg")
    assert sent_body["included"][0]["attributes"]["name"] == sent_name
    assert sent_body["data"]["relationships"]["parent"]["data"]["id"] == "urn:fake-folder"
    assert sent_body["included"][0]["relationships"]["storage"]["data"]["id"] == "urn:fake-storage"
    # No description given -> no PATCH call should have been made.
    assert len(responses.calls) == 1


def test_uniquify_filename_preserves_stem_and_extension():
    unique = _uniquify_filename("photo.jpg")

    assert unique.startswith("photo_")
    assert unique.endswith(".jpg")
    assert unique != "photo.jpg"


def test_uniquify_filename_two_calls_differ():
    assert _uniquify_filename("photo.jpg") != _uniquify_filename("photo.jpg")


@responses.activate
def test_create_item_in_folder_sets_description_via_patch(config):
    responses.add(
        responses.POST,
        _items_collection_url(config),
        json={"data": {"id": "urn:fake-lineage"}},
        status=201,
    )
    responses.add(
        responses.PATCH,
        f"{_items_collection_url(config)}/urn:fake-lineage",
        json={"data": {"id": "urn:fake-lineage"}},
        status=200,
    )

    lineage_urn = create_item_in_folder(
        config,
        FakeAuth(),
        "urn:fake-storage",
        "photo.jpg",
        "urn:fake-folder",
        description="Linked to Issue #1",
    )

    assert lineage_urn == "urn:fake-lineage"
    assert len(responses.calls) == 2
    patch_body = json.loads(responses.calls[1].request.body)
    assert (
        patch_body["data"]["attributes"]["extension"]["data"]["description"]
        == "Linked to Issue #1"
    )


@responses.activate
def test_create_item_in_folder_raises_on_creation_failure(config):
    responses.add(
        responses.POST,
        _items_collection_url(config),
        json={"error": "forbidden"},
        status=403,
    )

    try:
        create_item_in_folder(
            config, FakeAuth(), "urn:fake-storage", "photo.jpg", "urn:fake-folder"
        )
        assert False, "expected ItemCreationError"
    except ItemCreationError:
        pass


@responses.activate
def test_create_item_in_folder_raises_on_description_patch_failure(config):
    responses.add(
        responses.POST,
        _items_collection_url(config),
        json={"data": {"id": "urn:fake-lineage"}},
        status=201,
    )
    responses.add(
        responses.PATCH,
        f"{_items_collection_url(config)}/urn:fake-lineage",
        json={"error": "bad request"},
        status=400,
    )

    try:
        create_item_in_folder(
            config,
            FakeAuth(),
            "urn:fake-storage",
            "photo.jpg",
            "urn:fake-folder",
            description="Linked to Issue #1",
        )
        assert False, "expected ItemCreationError"
    except ItemCreationError:
        pass
