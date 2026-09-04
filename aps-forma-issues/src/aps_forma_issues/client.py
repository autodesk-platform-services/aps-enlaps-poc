"""High-level facade — the primary entry point for this library."""

from __future__ import annotations

from pathlib import Path

import requests

from . import attachments as _attachments
from . import issues as _issues
from . import items as _items
from . import relationships as _relationships
from . import storage as _storage
from .auth import TokenProvider
from .config import FormaIssuesConfig
from .models import IssueInput, IssueResult


class FormaIssuesClient:
    """Creates Forma Issues and attaches images to them.

    Authentication is a separate concern — pass in anything satisfying
    `TokenProvider`. `aps_ssa.SsaAuth` is the recommended, tested choice,
    but any object with a `get_token` method works, including a thin
    wrapper around a three-legged OAuth token you already have (see
    `auth.py`).
    """

    def __init__(
        self,
        config: FormaIssuesConfig,
        auth: TokenProvider,
        session: requests.Session | None = None,
    ):
        """Creates a new instance of the client.

        Args:
            config (FormaIssuesConfig): Target project config.
            auth (TokenProvider): Auth client used to sign requests.
            session (requests.Session, optional): Session to reuse
                across calls. A new one is created if omitted.
        """
        self._config = config
        self._auth = auth
        self._session = session or requests.Session()

    def create_issue(self, issue: IssueInput) -> dict:
        """Creates an Issue.

        Args:
            issue (IssueInput): Fields for the new issue.

        Returns:
            dict: Parsed response for the created issue.

        Raises:
            IssueCreationError: If creation fails.
        """
        return _issues.create_issue(
            self._config, self._auth, issue, session=self._session
        )

    def list_issues(self, limit: int = 100, offset: int = 0) -> dict:
        """Lists Issues in the target project, newest page first.

        Args:
            limit (int, optional): Max results per page (API-capped at 200).
            offset (int, optional): Pagination offset.

        Returns:
            dict: `{"pagination": {...}, "results": [...]}`.

        Raises:
            IssueFetchError: If the request fails.
        """
        return _issues.list_issues(
            self._config, self._auth, limit=limit, offset=offset, session=self._session
        )

    def get_issue(self, issue_id: str) -> dict:
        """Fetches a single Issue by ID.

        Args:
            issue_id (str): ID of the issue to fetch.

        Returns:
            dict: Parsed issue.

        Raises:
            IssueFetchError: If the request fails.
        """
        return _issues.get_issue(self._config, self._auth, issue_id, session=self._session)

    def get_issue_types(self, include_subtypes: bool = True) -> dict:
        """Lists Issue types configured on the target project.

        Args:
            include_subtypes (bool, optional): Whether to include each
                type's subtypes inline. Defaults to `True`.

        Returns:
            dict: `{"pagination": {...}, "results": [...]}`.

        Raises:
            IssueFetchError: If the request fails.
        """
        return _issues.get_issue_types(
            self._config, self._auth, include_subtypes=include_subtypes, session=self._session
        )

    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """Uploads image bytes to project-scoped Data Management storage.

        Args:
            image_bytes (bytes): Raw image bytes.
            filename (str): Name to associate with the uploaded object.

        Returns:
            str: The resulting storage URN.

        Raises:
            StorageUploadError: If the upload fails.
        """
        return _storage.upload_image_bytes(
            self._config, self._auth, image_bytes, filename=filename, session=self._session
        )

    def upload_image_file(self, path: str | Path) -> str:
        """Uploads an image file to project-scoped Data Management storage.

        Args:
            path (str | Path): Path to the image file.

        Returns:
            str: The resulting storage URN.

        Raises:
            StorageUploadError: If the upload fails.
        """
        return _storage.upload_image_file(
            self._config, self._auth, path, session=self._session
        )

    def attach_image_to_issue(
        self,
        issue_id: str,
        image_bytes: bytes,
        filename: str,
        description: str | None = None,
    ) -> dict:
        """Uploads an image into the configured folder and links it to
        an Issue, so it renders as an attachment thumbnail.

        Args:
            issue_id (str): ID of the issue to attach to.
            image_bytes (bytes): Raw image bytes.
            filename (str): Desired file name.
            description (str, optional): Description to set on the
                uploaded item — visible when browsing the folder in
                Files/Docs. Defaults to a plain reference to `issue_id`.

        Returns:
            dict: `{"lineage_urn": str, "relationships": list[dict]}`.

        Raises:
            StorageUploadError: If uploading the image fails.
            ItemCreationError: If creating the item fails.
            AttachmentError: If linking the item to the issue fails.
        """
        storage_urn = self.upload_image(image_bytes, filename=filename)
        lineage_urn = _items.create_item_in_folder(
            self._config,
            self._auth,
            storage_urn,
            filename,
            self._config.upload_folder_id,
            description=description or f"Linked to Forma Issue {issue_id}",
            session=self._session,
        )
        relationships = _relationships.link_issue_to_document(
            self._config, self._auth, issue_id, lineage_urn, session=self._session
        )
        return {"lineage_urn": lineage_urn, "relationships": relationships}

    def create_issue_with_image(
        self,
        issue: IssueInput,
        image_bytes: bytes,
        filename: str = "situation.jpg",
    ) -> IssueResult:
        """Creates an Issue and attaches an image to it in one call.

        Args:
            issue (IssueInput): Fields for the new issue.
            image_bytes (bytes): Raw image bytes.
            filename (str, optional): Desired file name.

        Returns:
            IssueResult: The created issue, attachment, and a direct
            link to the uploaded image.

        Raises:
            IssueCreationError: If creating the issue fails.
            StorageUploadError: If uploading the image fails.
            ItemCreationError: If creating the item fails.
            AttachmentError: If linking the item to the issue fails.
        """
        raw_issue = self.create_issue(issue)
        issue_id = raw_issue["id"]
        display_id = raw_issue.get("displayId")
        reference = f"#{display_id}" if display_id else issue_id
        description = f"Linked to Issue {reference}: {issue.title}"

        raw_attachment = self.attach_image_to_issue(
            issue_id, image_bytes, filename, description=description
        )
        lineage_urn = raw_attachment.get("lineage_urn")
        attachment_id = None
        relationships = raw_attachment.get("relationships") or []
        if relationships:
            attachment_id = relationships[0].get("id")

        web_view_url = None
        if lineage_urn:
            web_view_url = _items.get_item_web_view_url(
                self._config, self._auth, lineage_urn, session=self._session
            )

        return IssueResult(
            issue_id=issue_id,
            attachment_id=attachment_id,
            raw_issue=raw_issue,
            raw_attachment=raw_attachment,
            web_view_url=web_view_url,
        )

    def list_issue_attachments(self, issue_id: str) -> list[dict]:
        """Lists attachments on an Issue, created via the Issues-attachments
        endpoint path (`attach_image_to_issue_via_endpoint`).

        !!!Important!!!
        Only attachments created via `attach_image_to_issue` show up here.
        is a reliable predicate for whether this call is worth making.

        Args:
            issue_id (str): ID of the issue to list attachments for.

        Returns:
            list[dict]: Each with `attachmentId`, `displayName`,
            `storageUrn`, etc.

        Raises:
            AttachmentError: If the request fails.
        """
        return _attachments.list_attachments(
            self._config, self._auth, issue_id, session=self._session
        )

    def get_attachment_download_url(self, storage_urn: str) -> str:
        """Gets a short-lived, directly-downloadable URL for an attachment.

        Args:
            storage_urn (str): An attachment's `storageUrn`, from
                `list_issue_attachments`.

        Returns:
            str: A signed S3 URL — expires in about two minutes, so
            fetch it right before use rather than caching it.

        Raises:
            StorageDownloadError: If the request fails.
        """
        return _storage.get_download_url(
            self._config, self._auth, storage_urn, session=self._session
        )

    def attach_image_to_issue_via_endpoint(
        self,
        issue_id: str,
        image_bytes: bytes,
        filename: str,
    ) -> dict:
        """Alternative to `attach_image_to_issue`: attaches an image
        using the Issues API's own attachments endpoint instead of
        creating an item in `config.upload_folder_id`.

        No Docs folder permission is required for this path, unlike
        `attach_image_to_issue` — the tradeoff is that Autodesk places
        the image in its own auto-created, unbrowsable folder rather
        than one you chose. See `attachments.py`.

        Args:
            issue_id (str): ID of the issue to attach to.
            image_bytes (bytes): Raw image bytes.
            filename (str): Desired file name.

        Returns:
            dict: Parsed response, e.g. `{"attachments": [{"attachmentId":
            ..., "lineageUrn": ..., ...}]}`.

        Raises:
            StorageUploadError: If uploading the image fails.
            AttachmentError: If the attach request fails.
        """
        storage_urn = self.upload_image(image_bytes, filename=filename)
        return _attachments.attach_image_to_issue(
            self._config, self._auth, issue_id, storage_urn, filename, session=self._session
        )

    def create_issue_with_image_via_endpoint(
        self,
        issue: IssueInput,
        image_bytes: bytes,
        filename: str = "situation.jpg",
    ) -> IssueResult:
        """Alternative to `create_issue_with_image`, using
        `attach_image_to_issue_via_endpoint` for the attach step. See
        that method for the tradeoff versus the default.

        Args:
            issue (IssueInput): Fields for the new issue.
            image_bytes (bytes): Raw image bytes.
            filename (str, optional): Desired file name.

        Returns:
            IssueResult: The created issue, attachment, and a direct
            link to the uploaded image.

        Raises:
            IssueCreationError: If creating the issue fails.
            StorageUploadError: If uploading the image fails.
            AttachmentError: If the attach request fails.
        """
        raw_issue = self.create_issue(issue)
        issue_id = raw_issue["id"]

        raw_attachment = self.attach_image_to_issue_via_endpoint(
            issue_id, image_bytes, filename
        )
        attachment_id = None
        lineage_urn = None
        attachments = raw_attachment.get("attachments") or []
        if attachments:
            attachment_id = attachments[0].get("attachmentId")
            lineage_urn = attachments[0].get("lineageUrn")

        web_view_url = None
        if lineage_urn:
            web_view_url = _items.get_item_web_view_url(
                self._config, self._auth, lineage_urn, session=self._session
            )

        return IssueResult(
            issue_id=issue_id,
            attachment_id=attachment_id,
            raw_issue=raw_issue,
            raw_attachment=raw_attachment,
            web_view_url=web_view_url,
        )
