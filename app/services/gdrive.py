import os
import io
import hashlib
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


class GoogleDriveService:
    """
    Google Drive Service for folder exploration, metadata synchronization, and file downloading.
    Includes fallback sandbox mode for offline testing and development when OAuth is not configured.
    """

    def __init__(self, folder_id: Optional[str] = None):
        self.folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        self.credentials_path = settings.GOOGLE_CREDENTIALS_PATH
        self.token_path = settings.GOOGLE_TOKEN_PATH
        self.service = None
        self.is_connected = False
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Drive API service if credentials exist."""
        if not os.path.exists(self.token_path) and not os.path.exists(self.credentials_path):
            logger.info("Google Drive OAuth credentials not found. Using local Sandbox Drive Mode.")
            self.is_connected = False
            return

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request

            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, ["https://www.googleapis.com/auth/drive.readonly"])

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    logger.info("Drive credentials require re-authentication.")
                    self.is_connected = False
                    return

            self.service = build("drive", "v3", credentials=creds)
            self.is_connected = True
            logger.info("Successfully connected to Google Drive API.")
        except Exception as e:
            logger.warning(f"Failed to connect to Google Drive API: {e}. Falling back to Sandbox mode.")
            self.is_connected = False

    def list_files(self, folder_id: Optional[str] = None, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        List files in specified folder recursively.
        Returns list of metadata dicts.
        """
        target_folder = folder_id or self.folder_id

        if not self.is_connected or not self.service:
            logger.info("Listing files from local sample data sandbox.")
            return self._list_sandbox_files()

        results = []
        try:
            query = f"'{target_folder}' in parents and trashed = false" if target_folder else "trashed = false"
            response = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink, md5Checksum)",
                pageSize=100
            ).execute()

            files = response.get("files", [])
            for f in files:
                mime_type = f.get("mimeType")
                if mime_type == "application/vnd.google-apps.folder" and recursive:
                    # Recursive sub-folder discovery
                    sub_files = self.list_files(folder_id=f.get("id"), recursive=True)
                    results.extend(sub_files)
                elif mime_type in SUPPORTED_MIME_TYPES:
                    results.append({
                        "file_id": f.get("id"),
                        "file_name": f.get("name"),
                        "mime_type": mime_type,
                        "gdrive_url": f.get("webViewLink", f"https://drive.google.com/file/d/{f.get('id')}/view"),
                        "modified_time": f.get("modifiedTime"),
                        "size_bytes": int(f.get("size", 0)) if f.get("size") else None,
                        "md5_checksum": f.get("md5Checksum"),
                    })
        except Exception as e:
            logger.error(f"Error listing files from Google Drive: {e}")
            return self._list_sandbox_files()

        return results

    def download_file(self, file_id: str, destination_path: str) -> str:
        """
        Download file from Google Drive to local destination_path.
        """
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        if not self.is_connected or not self.service:
            # Check sandbox file
            sandbox_path = os.path.join(settings.DATA_DIR, "sample_docs", file_id)
            if os.path.exists(sandbox_path):
                import shutil
                shutil.copy(sandbox_path, destination_path)
                return destination_path
            # If not in sandbox, return destination_path if exists or raise
            if os.path.exists(destination_path):
                return destination_path
            raise FileNotFoundError(f"File {file_id} not found in Google Drive or Sandbox.")

        try:
            from googleapiclient.http import MediaIoBaseDownload
            request = self.service.files().get_media(fileId=file_id)
            with open(destination_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            logger.info(f"Downloaded file {file_id} to {destination_path}")
            return destination_path
        except Exception as e:
            logger.error(f"Failed downloading file {file_id}: {e}")
            raise e

    def _list_sandbox_files(self) -> List[Dict[str, Any]]:
        """List files in local sample_docs folder as sandbox fallback."""
        sample_dir = os.path.join(settings.DATA_DIR, "sample_docs")
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir, exist_ok=True)
            return []

        results = []
        for filename in os.listdir(sample_dir):
            filepath = os.path.join(sample_dir, filename)
            if not os.path.isfile(filepath):
                continue
            ext = os.path.splitext(filename)[1].lower()
            mime_type = "application/pdf"
            if ext == ".docx":
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif ext == ".pptx":
                mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            elif ext == ".xlsx":
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif ext in [".png", ".jpg", ".jpeg"]:
                mime_type = f"image/{ext.replace('.', '')}"

            stat = os.stat(filepath)
            with open(filepath, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()

            results.append({
                "file_id": filename,
                "file_name": filename,
                "mime_type": mime_type,
                "gdrive_url": f"file://{filepath}",
                "modified_time": str(stat.st_mtime),
                "size_bytes": stat.st_size,
                "md5_checksum": md5,
            })
        return results
