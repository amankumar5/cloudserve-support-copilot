import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logging import logger


class MetadataDB:
    """
    SQLite Metadata Store for tracking document versions, hashes, and ingestion job statuses.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.METADATA_DB_PATH
        self._init_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    file_id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    gdrive_url TEXT,
                    modified_time TEXT,
                    md5_checksum TEXT,
                    pages_count INTEGER DEFAULT 0,
                    elements_count INTEGER DEFAULT 0,
                    chunks_count INTEGER DEFAULT 0,
                    ingested_at TEXT NOT NULL,
                    status TEXT DEFAULT 'indexed'
                )
            """)

            # Ingestion Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress_percentage REAL DEFAULT 0.0,
                    files_total INTEGER DEFAULT 0,
                    files_processed INTEGER DEFAULT 0,
                    files_failed INTEGER DEFAULT 0,
                    errors_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def upsert_document(self, doc_info: Dict[str, Any]):
        """Save or update document record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documents (file_id, file_name, mime_type, gdrive_url, modified_time, md5_checksum, pages_count, elements_count, chunks_count, ingested_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    file_name=excluded.file_name,
                    mime_type=excluded.mime_type,
                    gdrive_url=excluded.gdrive_url,
                    modified_time=excluded.modified_time,
                    md5_checksum=excluded.md5_checksum,
                    pages_count=excluded.pages_count,
                    elements_count=excluded.elements_count,
                    chunks_count=excluded.chunks_count,
                    ingested_at=excluded.ingested_at,
                    status=excluded.status
            """, (
                doc_info["file_id"],
                doc_info["file_name"],
                doc_info["mime_type"],
                doc_info.get("gdrive_url"),
                doc_info.get("modified_time"),
                doc_info.get("md5_checksum"),
                doc_info.get("pages_count", 0),
                doc_info.get("elements_count", 0),
                doc_info.get("chunks_count", 0),
                doc_info.get("ingested_at", datetime.utcnow().isoformat() + "Z"),
                doc_info.get("status", "indexed")
            ))
            conn.commit()

    def get_document(self, file_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, file_name, mime_type, gdrive_url, modified_time, md5_checksum, pages_count, elements_count, chunks_count, ingested_at, status FROM documents WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "file_id": row[0],
                "file_name": row[1],
                "mime_type": row[2],
                "gdrive_url": row[3],
                "modified_time": row[4],
                "md5_checksum": row[5],
                "pages_count": row[6],
                "elements_count": row[7],
                "chunks_count": row[8],
                "ingested_at": row[9],
                "status": row[10]
            }

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, file_name, mime_type, gdrive_url, modified_time, md5_checksum, pages_count, elements_count, chunks_count, ingested_at, status FROM documents")
            rows = cursor.fetchall()
            return [{
                "file_id": row[0],
                "file_name": row[1],
                "mime_type": row[2],
                "gdrive_url": row[3],
                "modified_time": row[4],
                "md5_checksum": row[5],
                "pages_count": row[6],
                "elements_count": row[7],
                "chunks_count": row[8],
                "ingested_at": row[9],
                "status": row[10]
            } for row in rows]

    def delete_document(self, file_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE file_id = ?", (file_id,))
            conn.commit()

    # Job tracking methods
    def create_job(self, job_id: str, files_total: int) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + "Z"
        job = {
            "job_id": job_id,
            "status": "processing",
            "progress_percentage": 0.0,
            "files_total": files_total,
            "files_processed": 0,
            "files_failed": 0,
            "errors": [],
            "created_at": now,
            "updated_at": now
        }
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ingestion_jobs (job_id, status, progress_percentage, files_total, files_processed, files_failed, errors_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, "processing", 0.0, files_total, 0, 0, json.dumps([]), now, now))
            conn.commit()
        return job

    def update_job(self, job_id: str, files_processed: int, files_failed: int, errors: List[str], status: Optional[str] = None):
        now = datetime.utcnow().isoformat() + "Z"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT files_total FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return
            files_total = row[0]
            progress = (files_processed / files_total * 100.0) if files_total > 0 else 100.0
            if not status:
                status = "completed" if (files_processed + files_failed) >= files_total else "processing"

            cursor.execute("""
                UPDATE ingestion_jobs SET
                    status=?,
                    progress_percentage=?,
                    files_processed=?,
                    files_failed=?,
                    errors_json=?,
                    updated_at=?
                WHERE job_id=?
            """, (status, progress, files_processed, files_failed, json.dumps(errors), now, job_id))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT job_id, status, progress_percentage, files_total, files_processed, files_failed, errors_json, created_at, updated_at FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "job_id": row[0],
                "status": row[1],
                "progress_percentage": row[2],
                "files_total": row[3],
                "files_processed": row[4],
                "files_failed": row[5],
                "errors": json.loads(row[6]) if row[6] else [],
                "created_at": row[7],
                "updated_at": row[8]
            }


metadata_db = MetadataDB()
