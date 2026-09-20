from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Health Model
class HealthResponse(BaseModel):
    status: str
    version: str
    vector_store: str
    llm_provider: str


# Google Drive Models
class DriveConnectRequest(BaseModel):
    folder_id: Optional[str] = None
    credentials_json: Optional[str] = None


class DriveConnectResponse(BaseModel):
    status: str
    message: str
    folder_id: Optional[str] = None
    auth_url: Optional[str] = None


class DriveSyncRequest(BaseModel):
    folder_id: Optional[str] = None
    force_resync: bool = False


class DriveSyncResponse(BaseModel):
    job_id: str
    status: str
    files_discovered: int
    message: str


class DriveDocumentItem(BaseModel):
    file_id: str
    file_name: str
    mime_type: str
    gdrive_url: Optional[str] = None
    modified_time: Optional[str] = None
    size_bytes: Optional[int] = None
    status: str = "indexed"


class DriveDocumentsResponse(BaseModel):
    total: int
    documents: List[DriveDocumentItem]


# Document Models
class DocumentDetailResponse(BaseModel):
    document_id: str
    file_name: str
    file_id: str
    mime_type: str
    gdrive_url: Optional[str] = None
    modified_time: Optional[str] = None
    pages_count: int
    elements_count: int
    chunks_count: int
    ingested_at: str


# Ingestion Job Models
class IngestionJobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress_percentage: float
    files_total: int
    files_processed: int
    files_failed: int
    errors: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


# Query & Citation Models
class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    section: Optional[str] = None
    element_type: str
    snippet: str
    gdrive_url: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatMessage(BaseModel):
    role: str  # user or assistant
    content: str


class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    top_k: Optional[int] = 5
    filter_document_id: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation]
    retrieval_time_ms: float
    generation_time_ms: float
    query_intent: Optional[str] = None
