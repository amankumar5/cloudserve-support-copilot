import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from app.services.gdrive import GoogleDriveService
from app.parsing.factory import parser_factory
from app.chunking.strategy import chunker
from app.embeddings.service import embedding_service
from app.storage.chroma_store import vector_store
from app.storage.metadata_db import metadata_db
from app.retrieval.bm25 import bm25_engine
from app.core.config import settings
from app.core.logging import logger


class IngestionPipeline:
    """
    Asynchronous Document Ingestion Pipeline with change detection and hash tracking.
    """

    def __init__(self, drive_service: Optional[GoogleDriveService] = None):
        self.drive_service = drive_service or GoogleDriveService()
        self.download_dir = os.path.join(settings.DATA_DIR, "downloads")
        os.makedirs(self.download_dir, exist_ok=True)

    def start_ingestion_job(self, folder_id: Optional[str] = None, force_resync: bool = False) -> str:
        """
        Trigger an ingestion job asynchronously and return job_id.
        """
        job_id = str(uuid.uuid4())
        files = self.drive_service.list_files(folder_id=folder_id)
        metadata_db.create_job(job_id=job_id, files_total=len(files))

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._process_job_async(job_id=job_id, files=files, force_resync=force_resync))
        except RuntimeError:
            asyncio.run(self._process_job_async(job_id=job_id, files=files, force_resync=force_resync))

        return job_id

    async def _process_job_async(self, job_id: str, files: List[Dict[str, Any]], force_resync: bool):
        logger.info(f"Starting ingestion job {job_id} for {len(files)} files.")
        files_processed = 0
        files_failed = 0
        errors = []

        for f in files:
            file_id = f["file_id"]
            file_name = f["file_name"]
            mime_type = f["mime_type"]
            gdrive_url = f.get("gdrive_url", "")
            modified_time = f.get("modified_time", "")
            md5_checksum = f.get("md5_checksum", "")

            # Check if unchanged
            if not force_resync:
                existing_doc = metadata_db.get_document(file_id)
                if existing_doc and (existing_doc.get("md5_checksum") == md5_checksum or existing_doc.get("modified_time") == modified_time):
                    logger.info(f"Skipping unchanged document: {file_name}")
                    files_processed += 1
                    metadata_db.update_job(job_id, files_processed, files_failed, errors)
                    continue

            try:
                # 1. Download File
                local_path = os.path.join(self.download_dir, f"{file_id}_{file_name}")
                self.drive_service.download_file(file_id=file_id, destination_path=local_path)

                # 2. Parse Document
                parser = parser_factory.get_parser(local_path, mime_type)
                doc = parser.parse(file_path=local_path, file_id=file_id, file_name=file_name, gdrive_url=gdrive_url)

                # 3. Structure-Aware Chunking
                doc_chunks = chunker.chunk_document(doc)

                # 4. Generate Embeddings
                texts = [c.content for c in doc_chunks]
                embeddings = embedding_service.embed_texts(texts)
                for idx, emb in enumerate(embeddings):
                    doc_chunks[idx].embedding = emb

                # 5. Index into VectorStore & BM25
                if force_resync:
                    vector_store.delete_document(doc.document_id)
                    bm25_engine.delete_document(doc.document_id)

                vector_store.add_chunks(doc_chunks)
                bm25_engine.index_chunks(doc_chunks)

                # 6. Save Metadata Record
                metadata_db.upsert_document({
                    "file_id": file_id,
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "gdrive_url": gdrive_url,
                    "modified_time": modified_time,
                    "md5_checksum": md5_checksum,
                    "pages_count": len(doc.pages),
                    "elements_count": sum(len(p.elements) for p in doc.pages),
                    "chunks_count": len(doc_chunks),
                    "status": "indexed"
                })

                files_processed += 1
                logger.info(f"Ingested and indexed document {file_name} successfully ({len(doc_chunks)} chunks).")

            except Exception as e:
                err_msg = f"Failed to ingest file {file_name} ({file_id}): {str(e)}"
                logger.error(err_msg, exc_info=True)
                errors.append(err_msg)
                files_failed += 1

            metadata_db.update_job(job_id, files_processed, files_failed, errors)

        metadata_db.update_job(job_id, files_processed, files_failed, errors, status="completed" if files_failed == 0 else "completed_with_errors")
        logger.info(f"Ingestion job {job_id} finished: {files_processed} processed, {files_failed} failed.")


ingestion_pipeline = IngestionPipeline()
