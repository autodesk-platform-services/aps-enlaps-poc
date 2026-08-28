"""Upload image bytes into a project's own Data Management storage.
**Documentation**: https://aps.autodesk.com/blog/uploading-file-acc-using-net-sdk
"""

from __future__ import annotations

import re
from pathlib import Path

import requests

from .auth import TokenProvider
from .config import FormaIssuesConfig
from .exceptions import StorageUploadError

STORAGE_PATH = "/data/v1/projects/{project_id}/storage"
OSS_OBJECT_PATH = "/oss/v2/buckets/{bucket}/objects/{object_name}/signeds3upload"

_STORAGE_URN_RE = re.compile(r"^urn:adsk\.objects:os\.object:([^/]+)/(.+)$")


def _dm_project_id(project_id: str) -> str:
    """Adds the hub-scope prefix Data Management expects (`b.` for
    ACC/BIM 360 projects, `a.` for personal hubs)
    """
    if project_id.startswith(("a.", "b.")):
        return project_id
    return f"b.{project_id}"


def upload_image_bytes(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    data: bytes,
    filename: str,
    session: requests.Session | None = None,
) -> str:
    """Uploads image bytes to project-scoped Data Management storage.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        data (bytes): Raw image bytes.
        filename (str): Name to associate with the uploaded object.
        session (requests.Session, optional): Session to reuse.

    Returns:
        str: The resulting storage URN, e.g.
        `urn:adsk.objects:os.object:{bucket}/{key}`.

    Raises:
        StorageUploadError: If any step of the upload fails.
    """
    session = session or requests.Session()
    storage_urn = _create_project_storage(config, auth, filename, session)
    bucket, object_key = _parse_storage_urn(storage_urn)
    _upload_bytes_to_oss(config, auth, bucket, object_key, data, session)
    return storage_urn


def upload_image_file(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    path: str | Path,
    session: requests.Session | None = None,
) -> str:
    """Uploads an image file to project-scoped Data Management storage.

    Args:
        config (FormaIssuesConfig): Target project config.
        auth (TokenProvider): Auth client used to sign requests.
        path (str | Path): Path to the image file.
        session (requests.Session, optional): Session to reuse.

    Returns:
        str: The resulting storage URN.

    Raises:
        StorageUploadError: If any step of the upload fails.
    """
    p = Path(path)
    return upload_image_bytes(config, auth, p.read_bytes(), filename=p.name, session=session)


def _create_project_storage(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    filename: str,
    session: requests.Session,
) -> str:
    url = config.base_url + STORAGE_PATH.format(
        project_id=_dm_project_id(config.project_id)
    )
    headers = {
        "Authorization": f"Bearer {auth.get_token()}",
        "Content-Type": "application/vnd.api+json",
    }
    body = {
        "jsonapi": {"version": "1.0"},
        "data": {
            "type": "objects",
            "attributes": {"name": filename},
            "relationships": {
                "target": {"data": {"type": "folders", "id": config.upload_folder_id}}
            },
        },
    }
    resp = session.post(
        url, json=body, headers=headers, timeout=config.request_timeout_seconds
    )
    if resp.status_code not in (200, 201):
        raise StorageUploadError(
            f"Could not create project storage: {resp.status_code} {resp.text}"
        )
    return resp.json()["data"]["id"]


def _parse_storage_urn(storage_urn: str) -> tuple[str, str]:
    match = _STORAGE_URN_RE.match(storage_urn)
    if not match:
        raise StorageUploadError(f"Unexpected storage URN shape: {storage_urn!r}")
    return match.group(1), match.group(2)


def _upload_bytes_to_oss(
    config: FormaIssuesConfig,
    auth: TokenProvider,
    bucket: str,
    object_key: str,
    data: bytes,
    session: requests.Session,
) -> None:
    base = config.base_url
    path = OSS_OBJECT_PATH.format(bucket=bucket, object_name=object_key)
    headers = {"Authorization": f"Bearer {auth.get_token()}"}

    signed = session.get(
        f"{base}{path}",
        params={"parts": 1},
        headers=headers,
        timeout=config.request_timeout_seconds,
    )
    if signed.status_code != 200:
        raise StorageUploadError(
            f"Could not get signed upload URL: {signed.status_code} {signed.text}"
        )
    signed_body = signed.json()
    upload_url = signed_body["urls"][0]
    upload_key = signed_body["uploadKey"]

    put_resp = session.put(
        upload_url, data=data, timeout=config.request_timeout_seconds
    )
    if put_resp.status_code not in (200, 201):
        raise StorageUploadError(f"Upload to storage failed: {put_resp.status_code}")

    complete = session.post(
        f"{base}{path}",
        json={"uploadKey": upload_key},
        headers={**headers, "Content-Type": "application/json"},
        timeout=config.request_timeout_seconds,
    )
    if complete.status_code != 200:
        raise StorageUploadError(
            f"Could not finalize upload: {complete.status_code} {complete.text}"
        )
