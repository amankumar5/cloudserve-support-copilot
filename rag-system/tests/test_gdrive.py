import pytest
from app.services.gdrive import GoogleDriveService


def test_gdrive_sandbox_listing():
    service = GoogleDriveService()
    files = service.list_files()
    assert isinstance(files, list)
    assert len(files) > 0
    first = files[0]
    assert "file_id" in first
    assert "file_name" in first
    assert "mime_type" in first
