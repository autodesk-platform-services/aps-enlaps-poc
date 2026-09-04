"""Landing page + the issues dashboard."""

from __future__ import annotations

import mimetypes

import requests
from aps_forma_issues import FormaIssuesClient, FormaIssuesConfig, FormaIssuesError
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .issues_service import fetch_dashboard_issues
from .token_provider import SessionTokenProvider

main_bp = Blueprint("main", __name__)


def _build_client() -> FormaIssuesClient:
    config = FormaIssuesConfig(
        project_id=current_app.config["ACC_PROJECT_ID"],
        # Never used: this sample only lists/reads issues, it never
        # uploads — FormaIssuesConfig just requires a value in the shape.
        upload_folder_id="unused",
        base_url=current_app.config["ACC_BASE_URL"],
        request_timeout_seconds=current_app.config["REQUEST_TIMEOUT_SECONDS"],
    )
    return FormaIssuesClient(config, SessionTokenProvider())


@main_bp.route("/")
def index():
    """Landing/login page, or straight to the dashboard if already signed in."""
    if not session.get("access_token"):
        return render_template("landing.html")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
def dashboard():
    """Renders the issues table. All issues are embedded as JSON in the
    page so the detail modal's prev/next navigation works client-side,
    without a round trip per click.
    """
    if not session.get("access_token"):
        return redirect(url_for("main.index"))

    client = _build_client()

    error = None
    issues: list[dict] = []
    try:
        issues = fetch_dashboard_issues(
            client,
            session["access_token"],
            current_app.config["ACC_BASE_URL"],
            current_app.config["ACC_PROJECT_ID"],
        )
    except FormaIssuesError as exc:
        error = str(exc)

    return render_template(
        "dashboard.html",
        issues=issues,
        user_name=session.get("user_name"),
        error=error,
    )


@main_bp.route("/api/issues/<issue_id>/attachments")
def issue_attachments(issue_id: str):
    """Lazily resolves one issue's thumbnails, for the detail modal.

    Not embedded in the dashboard's initial payload on purpose: the
    signed download URLs this returns expire in ~2 minutes (see
    `aps_forma_issues.storage.get_download_url`), and most issues never
    get their modal opened — fetching per-issue, on demand, avoids both
    problems at once.
    """
    if not session.get("access_token"):
        return jsonify({"error": "Not signed in."}), 401

    client = _build_client()
    try:
        attachments = client.list_issue_attachments(issue_id)
    except FormaIssuesError as exc:
        return jsonify({"error": str(exc)}), 502

    images = [
        {
            "name": attachment.get("displayName") or attachment.get("fileName"),
            # Proxied through our own /api/attachments/image (see below)
            # rather than handing the browser Autodesk's raw signed S3
            # URL directly — that URL expires in ~2 minutes and comes
            # back as application/octet-stream, which isn't a safe bet
            # for an <img> tag across browsers.
            "url": url_for(
                "main.attachment_image",
                urn=attachment["storageUrn"],
                name=attachment.get("displayName") or attachment.get("fileName") or "",
            ),
        }
        for attachment in attachments
    ]
    return jsonify({"images": images})


@main_bp.route("/api/attachments/image")
def attachment_image():
    """Streams one attachment's image bytes, with a real image
    Content-Type — see `issue_attachments` for why this proxies rather
    than exposing Autodesk's signed URL straight to the browser.
    """
    if not session.get("access_token"):
        return jsonify({"error": "Not signed in."}), 401

    storage_urn = request.args.get("urn")
    if not storage_urn:
        return jsonify({"error": "Missing urn."}), 400

    client = _build_client()
    try:
        download_url = client.get_attachment_download_url(storage_urn)
    except FormaIssuesError as exc:
        return jsonify({"error": str(exc)}), 502

    upstream = requests.get(download_url, timeout=15)
    if upstream.status_code != 200:
        return jsonify({"error": "Could not fetch image."}), 502

    content_type = mimetypes.guess_type(request.args.get("name", ""))[0] or "image/jpeg"
    return Response(upstream.content, mimetype=content_type)
