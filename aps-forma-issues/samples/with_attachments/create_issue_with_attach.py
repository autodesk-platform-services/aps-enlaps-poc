"""Manually verify aps-forma-issues library using attachments to images"""

from __future__ import annotations

import base64
import os
import sys
import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

import requests  # noqa: E402 — must run after load_dotenv()

from aps_forma_issues import (  # noqa: E402
    AttachmentError,
    FormaIssuesClient,
    FormaIssuesConfig,
    IssueCreationError,
    IssueInput,
    StorageUploadError,
    SafetyRootCause,
)
from aps_ssa import AuthError, SsaAuth, SsaConfig  # noqa: E402

# A minimal valid 1x1 white-pixel PNG — used only if no image path is given.
_PLACEHOLDER_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Config error: missing required environment variable {name}", file=sys.stderr)
        raise SystemExit(1)
    return value


def _load_images() -> list[tuple[bytes, str]]:
    if len(sys.argv) > 1:
        images = []
        for arg in sys.argv[1:]:
            path = Path(arg)
            images.append((path.read_bytes(), path.name))
        return images
    print("No image paths given — using a single built-in 1x1 placeholder PNG.\n")
    return [(base64.b64decode(_PLACEHOLDER_PNG_B64), "placeholder.png")]


def main() -> int:
    images = _load_images()

    issue_subtype_id = _require_env("SAMPLE_ISSUE_SUBTYPE_ID")
    assigned_to = _require_env("SAMPLE_ASSIGNED_TO")

    try:
        ssa_config = SsaConfig.from_env()
        forma_config = FormaIssuesConfig.from_env()
    except RuntimeError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    auth = SsaAuth(ssa_config)
    client = FormaIssuesClient(forma_config, auth)

    issue = IssueInput(
        title="[aps-forma-issues-sample-with-attachments] test issue",
        description="Created by aps-forma-issues-sample-with-attachments for manual verification.",
        issue_subtype_id=issue_subtype_id,
        assigned_to=assigned_to,
        start_date=datetime.date.today().isoformat(),
        root_cause_id=SafetyRootCause.HUMAN_ERROR
    )

    print("STEP 1/3: Authenticate (aps-ssa) ...")
    try:
        auth.get_token()
    except AuthError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    print("  OK\n")

    print("STEP 2/3: Create Issue ...")
    try:
        raw_issue = client.create_issue(issue)
    except IssueCreationError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    issue_id = raw_issue["id"]
    display_id = raw_issue.get("displayId")
    print(f"  OK — issue id: {issue_id} (#{display_id}), published: {raw_issue.get('published')}\n")

    print(f"STEP 3/3: Attach {len(images)} image(s) via the Issues-attachments endpoint ...")
    for i, (image_bytes, filename) in enumerate(images, start=1):
        print(f"  [{i}/{len(images)}] uploading + attaching '{filename}' ...")
        try:
            result = client.attach_image_to_issue_via_endpoint(issue_id, image_bytes, filename)
        except (StorageUploadError, AttachmentError) as exc:
            print(f"    FAILED: {exc}", file=sys.stderr)
            return 1
        attachment = result["attachments"][0]
        print(f"    OK — attachmentId: {attachment['attachmentId']}")
    print()

    # attachmentCount is expected to match len(images) exactly — unlike
    # the default (items + Relationships API) path, this endpoint keeps
    # the issue's own attachmentCount in sync.
    headers = {"Authorization": f"Bearer {auth.get_token()}"}
    url = (
        f"{forma_config.base_url}/construction/issues/v1/projects/"
        f"{forma_config.project_id}/issues/{issue_id}"
    )
    resp = requests.get(url, headers=headers, timeout=forma_config.request_timeout_seconds)
    attachment_count = resp.json().get("attachmentCount") if resp.status_code == 200 else "?"
    print(f"attachmentCount on re-fetched issue: {attachment_count} (expected {len(images)})")

    print(
        "\nAll steps succeeded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
