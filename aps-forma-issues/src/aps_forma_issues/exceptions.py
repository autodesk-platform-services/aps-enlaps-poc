"""Exceptions raised by this library."""


class FormaIssuesError(RuntimeError):
    """Base class for every error raised by this library.
    """


class StorageUploadError(FormaIssuesError):
    """Raised when uploading image bytes to Data Management storage fails."""


class ItemCreationError(FormaIssuesError):
    """Raised when creating a Data Management Item, or setting its
    description, fails.
    """


class AttachmentError(FormaIssuesError):
    """Raised when linking an Item to an Issue via the Relationships
    API fails.
    """


class IssueCreationError(FormaIssuesError):
    """Raised when creating an Issue fails."""
