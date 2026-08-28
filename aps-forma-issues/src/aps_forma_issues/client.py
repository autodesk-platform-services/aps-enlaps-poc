"""High-level facade — the primary entry point for this library."""

from __future__ import annotations

from pathlib import Path

import requests

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
