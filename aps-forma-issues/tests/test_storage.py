import json
import re

import responses

from aps_forma_issues.exceptions import StorageUploadError
from aps_forma_issues.storage import _dm_project_id, upload_image_bytes


class FakeAuth:
    def get_token(self) -> str:
        return "fake-token"


def _storage_create_url(config):
    # Data Management API needs the hub-scoped ("b."-prefixed) project
    # id — see _dm_project_id and storage.py's module docstring for why
    # this differs from the bare id used elsewhere (issues.py, etc.).
    return f"{config.base_url}/data/v1/projects/{_dm_project_id(config.project_id)}/storage"


def test_dm_project_id_adds_prefix_when_missing():
    assert _dm_project_id("abc-123") == "b.abc-123"


def test_dm_project_id_leaves_already_prefixed_id_untouched():
    assert _dm_project_id("b.abc-123") == "b.abc-123"
    assert _dm_project_id("a.abc-123") == "a.abc-123"


def _oss_url_pattern(config, bucket):
    return re.compile(
        rf"{re.escape(config.base_url)}/oss/v2/buckets/{re.escape(bucket)}"
        rf"/objects/[^/]+/signeds3upload"
    )


@responses.activate
def test_upload_image_bytes_success(config):
    storage_urn = "urn:adsk.objects:os.object:wip.dm.prod/real-object.jpg"

    responses.add(
        responses.POST,
        _storage_create_url(config),
        json={"data": {"id": storage_urn}},
        status=201,
    )

    def signed_url_callback(request):
        return (200, {}, '{"uploadKey": "key-1", "urls": ["https://upload.example/put"]}')

    def put_callback(request):
        assert request.body == b"fake-image-bytes"
        return (200, {}, "")

    def complete_callback(request):
        return (200, {}, '{"objectId": "unused-by-this-flow"}')

    responses.add_callback(
        responses.GET,
        _oss_url_pattern(config, "wip.dm.prod"),
        callback=signed_url_callback,
        content_type="application/json",
    )
    responses.add_callback(
        responses.PUT, "https://upload.example/put", callback=put_callback
    )
    responses.add_callback(
        responses.POST,
        _oss_url_pattern(config, "wip.dm.prod"),
        callback=complete_callback,
        content_type="application/json",
    )

    urn = upload_image_bytes(config, FakeAuth(), b"fake-image-bytes", filename="photo.jpg")

    assert urn == storage_urn
    # The storage-creation call should reference the configured folder,
    # not any bucket we own.
    create_body = json.loads(responses.calls[0].request.body)
    assert create_body["data"]["relationships"]["target"]["data"]["id"] == config.upload_folder_id
    assert create_body["data"]["attributes"]["name"] == "photo.jpg"


@responses.activate
def test_upload_image_bytes_failure_on_storage_creation(config):
    responses.add(
        responses.POST,
        _storage_create_url(config),
        json={"error": "forbidden"},
        status=403,
    )

    try:
        upload_image_bytes(config, FakeAuth(), b"data", filename="photo.jpg")
        assert False, "expected StorageUploadError"
    except StorageUploadError:
        pass


@responses.activate
def test_upload_image_bytes_failure_on_signed_url(config):
    storage_urn = "urn:adsk.objects:os.object:wip.dm.prod/real-object.jpg"
    responses.add(
        responses.POST,
        _storage_create_url(config),
        json={"data": {"id": storage_urn}},
        status=201,
    )
    responses.add(
        responses.GET,
        _oss_url_pattern(config, "wip.dm.prod"),
        json={"error": "denied"},
        status=403,
    )

    try:
        upload_image_bytes(config, FakeAuth(), b"data", filename="photo.jpg")
        assert False, "expected StorageUploadError"
    except StorageUploadError:
        pass


def test_upload_image_bytes_rejects_unexpected_storage_urn_shape(config, monkeypatch):
    import aps_forma_issues.storage as storage_module

    monkeypatch.setattr(
        storage_module, "_create_project_storage", lambda *a, **k: "not-a-valid-urn"
    )

    try:
        upload_image_bytes(config, FakeAuth(), b"data", filename="photo.jpg")
        assert False, "expected StorageUploadError"
    except StorageUploadError:
        pass
