"""Manually verify aps-forma-issues library"""

from __future__ import annotations

import base64
import os
import sys
import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from aps_forma_issues import (
    AttachmentError,
    FormaIssuesClient,
    FormaIssuesConfig,
    IssueCreationError,
    IssueInput,
    ItemCreationError,
    SafetyRootCause,
    StorageUploadError,
    CustomAttribute
)
from aps_forma_issues.items import create_item_in_folder, get_item_web_view_url 
from aps_forma_issues.relationships import link_issue_to_document 
from aps_ssa import AuthError, SsaAuth, SsaConfig 

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


def main() -> int:
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        image_bytes = image_path.read_bytes()
        filename = image_path.name
    else:
        image_bytes = base64.b64decode(_PLACEHOLDER_PNG_B64)
        filename = "placeholder.png"
        print("No image path given — using a built-in 1x1 placeholder PNG.\n")

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
        title="[aps-forma-issues-sample] test issue",
        description="Created by aps-forma-issues-sample for manual verification.",
        issue_subtype_id=issue_subtype_id,
        assigned_to=assigned_to,
        # startDate wants a bare YYYY-MM-DD. The API's own 400 error
        # shows an "example" like "1982-06-01T00:00:00.000Z", but that's
        # misleading — sending that exact shape back still 400s; only a
        # bare date (confirmed live) is accepted.
        start_date=datetime.date.today().isoformat(),
        root_cause_id=SafetyRootCause.HUMAN_ERROR
    )

    print("STEP 1/5: Authenticate (aps-ssa) ...")
    try:
        auth.get_token()
    except AuthError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    print("  OK\n")

    print("STEP 2/5: Create Issue ...")
    try:
        raw_issue = client.create_issue(issue)
    except IssueCreationError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    issue_id = raw_issue["id"]
    display_id = raw_issue.get("displayId")
    print(f"  OK — issue id: {issue_id} (#{display_id}), published: {raw_issue.get('published')}\n")

    print(f"STEP 3/5: Upload '{filename}' to project storage ...")
    try:
        storage_urn = client.upload_image(image_bytes, filename=filename)
    except StorageUploadError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"  OK — storage urn: {storage_urn}\n")

    print(f"STEP 4/5: Create an Item in the configured folder ...")
    description = f"Linked to Issue #{display_id}: {issue.title}" if display_id else None
    try:
        lineage_urn = create_item_in_folder(
            forma_config,
            auth,
            storage_urn,
            filename,
            forma_config.upload_folder_id,
            description=description,
        )
    except ItemCreationError as exc:
        print(
            f"  FAILED: {exc}\n"
            "  A 403 here usually means the service account lacks Docs "
            "folder permission on upload_folder_id",
            file=sys.stderr,
        )
        return 1
    print(f"  OK — item lineage urn: {lineage_urn}\n")

    print(f"STEP 5/5: Link the item to issue {issue_id} via the Relationships API ...")
    try:
        relationships = link_issue_to_document(forma_config, auth, issue_id, lineage_urn)
    except AttachmentError as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"  OK — relationship: {relationships}\n")

    web_view_url = get_item_web_view_url(forma_config, auth, lineage_urn)
    print(
        "All steps succeeded"
    )
    if web_view_url:
        print(f"Direct link to the uploaded file: {web_view_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
