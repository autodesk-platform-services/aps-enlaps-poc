import pytest

from aps_forma_issues.config import FormaIssuesConfig


@pytest.fixture
def config() -> FormaIssuesConfig:
    return FormaIssuesConfig(
        project_id="proj-123",
        upload_folder_id="folder-abc",
        base_url="https://fake.local",
        request_timeout_seconds=5,
    )
