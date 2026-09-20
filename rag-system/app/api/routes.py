import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query as QueryParam
from app.models.api import (
    HealthResponse,
    DriveConnectRequest,
    DriveConnectResponse,
    DriveSyncRequest,
    DriveSyncResponse,
    DriveDocumentsResponse,
    DriveDocumentItem,
    DocumentDetailResponse,
    IngestionJobStatusResponse,
    QueryRequest,
    QueryResponse
)
from app.services.gdrive import GoogleDriveService
from app.ingestion.pipeline import ingestion_pipeline
from app.storage.metadata_db import metadata_db
from app.storage.chroma_store import vector_store
from app.retrieval.bm25 import bm25_engine
from app.retrieval.query_processor import query_processor
from app.retrieval.hybrid import hybrid_retriever
from app.reranking.reranker import reranker
from app.generation.generator import generator
from app.core.config import settings
from app.core.security import sanitize_input
from app.core.logging import logger

router = APIRouter()


# Health Check
@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        vector_store=settings.VECTOR_STORE_TYPE,
        llm_provider=settings.DEFAULT_LLM_PROVIDER
    )


# Google Drive Integration
@router.post("/drive/connect", response_model=DriveConnectResponse, tags=["Google Drive"])
def connect_drive(req: DriveConnectRequest):
    folder_id = req.folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
    drive_service = GoogleDriveService(folder_id=folder_id)

    if drive_service.is_connected:
        return DriveConnectResponse(
            status="connected",
            message="Successfully connected to Google Drive API.",
            folder_id=folder_id
        )
    else:
        return DriveConnectResponse(
            status="sandbox_mode",
            message="Google Drive API credentials not found or expired. Running in local sandbox drive mode.",
            folder_id=folder_id
        )


@router.post("/drive/sync", response_model=DriveSyncResponse, tags=["Google Drive"])
def sync_drive(req: DriveSyncRequest):
    folder_id = req.folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
    job_id = ingestion_pipeline.start_ingestion_job(folder_id=folder_id, force_resync=req.force_resync)
    job = metadata_db.get_job(job_id)

    return DriveSyncResponse(
        job_id=job_id,
        status=job["status"] if job else "processing",
        files_discovered=job["files_total"] if job else 0,
        message="Document ingestion & synchronization job started asynchronously."
    )


@router.get("/drive/documents", response_model=DriveDocumentsResponse, tags=["Google Drive"])
def list_drive_documents():
    docs = metadata_db.list_documents()
    items = [
        DriveDocumentItem(
            file_id=d["file_id"],
            file_name=d["file_name"],
            mime_type=d["mime_type"],
            gdrive_url=d.get("gdrive_url"),
            modified_time=d.get("modified_time"),
            status=d.get("status", "indexed")
        ) for d in docs
    ]
    return DriveDocumentsResponse(total=len(items), documents=items)


# Document Management
@router.get("/documents", response_model=DriveDocumentsResponse, tags=["Documents"])
def get_documents():
    return list_drive_documents()


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse, tags=["Documents"])
def get_document_by_id(document_id: str):
    doc = metadata_db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    return DocumentDetailResponse(
        document_id=doc["file_id"],
        file_name=doc["file_name"],
        file_id=doc["file_id"],
        mime_type=doc["mime_type"],
        gdrive_url=doc.get("gdrive_url"),
        modified_time=doc.get("modified_time"),
        pages_count=doc.get("pages_count", 0),
        elements_count=doc.get("elements_count", 0),
        chunks_count=doc.get("chunks_count", 0),
        ingested_at=doc.get("ingested_at", "")
    )


@router.delete("/documents/{document_id}", tags=["Documents"])
def delete_document(document_id: str):
    doc = metadata_db.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    vector_store.delete_document(document_id)
    bm25_engine.delete_document(document_id)
    metadata_db.delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}


# Ingestion Jobs
@router.post("/ingestion/start", response_model=DriveSyncResponse, tags=["Ingestion"])
def start_ingestion(req: DriveSyncRequest):
    return sync_drive(req)


@router.get("/ingestion/status/{job_id}", response_model=IngestionJobStatusResponse, tags=["Ingestion"])
def get_ingestion_status(job_id: str):
    job = metadata_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Ingestion job {job_id} not found.")

    return IngestionJobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress_percentage=job["progress_percentage"],
        files_total=job["files_total"],
        files_processed=job["files_processed"],
        files_failed=job["files_failed"],
        errors=job["errors"],
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )


# Query Endpoint
@router.post("/query", response_model=QueryResponse, tags=["RAG Query"])
def query_documents(req: QueryRequest):
    clean_question = sanitize_input(req.question)
    if not clean_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start_time = time.time()

    # 1. Intent Classification & Contextual Rewriting
    intent = query_processor.classify_intent(clean_question)
    search_query = query_processor.rewrite_query_with_history(clean_question, req.chat_history)

    # 2. Hybrid Retrieval (Dense Vector + Sparse BM25 + RRF)
    filter_dict = {"file_id": req.filter_document_id} if req.filter_document_id else None
    fused_candidates = hybrid_retriever.retrieve(
        query=search_query,
        top_k=settings.TOP_K_RETRIEVAL,
        filter_dict=filter_dict
    )

    retrieval_time_ms = round((time.time() - start_time) * 1000, 2)

    # 3. Reranking
    top_reranked = reranker.rerank(
        query=search_query,
        candidates=fused_candidates,
        top_k=req.top_k or settings.TOP_K_RERANKED
    )

    # 4. Grounded Multimodal Answer Generation
    response = generator.generate_answer(
        question=clean_question,
        retrieved_chunks=top_reranked,
        chat_history=req.chat_history,
        query_intent=intent
    )
    response.retrieval_time_ms = retrieval_time_ms

    logger.info(f"Query processed in {retrieval_time_ms + response.generation_time_ms} ms (Intent: {intent}, Sources: {len(response.sources)})")
    return response
