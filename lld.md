# Low-Level Design (LLD) Document
## Technical Implementation Specifications — CloudServe Support Automation System

- **Document Version**: 2.0
- **Target Stack**: Python 3.11+ / FastAPI / Angular 18+ / TypeScript / SQLite / ChromaDB

---

## 1. Domain Data Models & Schemas

### 1.1 Python Pydantic Schemas (`app/models/`)

#### Document Element Schema (`app/models/document.py`)
```python
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ElementType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    DIAGRAM = "diagram"
    IMAGE = "image"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    FOOTNOTE = "footnote"

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class DocumentElement(BaseModel):
    element_id: str
    element_type: ElementType
    page_number: int
    section_title: Optional[str] = None
    content_text: str
    structured_data: Optional[Dict[str, Any]] = None  # Markdown table matrix or diagram graph
    image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    parent_id: Optional[str] = None
```

#### Chunk & Metadata Schema (`app/models/chunk.py`)
```python
class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    file_id: str
    file_name: str
    page_number: int
    section: Optional[str] = None
    element_type: ElementType
    parent_element_id: Optional[str] = None
    gdrive_url: Optional[str] = None
    image_path: Optional[str] = None

class Chunk(BaseModel):
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
```

---

### 1.2 TypeScript Frontend Interfaces (`src/app/core/models/`)

```typescript
export type ChannelType = 'email' | 'chat' | 'api_docs' | 'forum';
export type ElementType = 'text' | 'heading' | 'table' | 'diagram' | 'image';

export interface SourceCitation {
  document_id: string;
  document_name: string;
  page_number: number;
  section?: string;
  element_type: ElementType;
  snippet: string;
  gdrive_url?: string;
  relevance_score?: number;
}

export interface QueryRequest {
  question: string;
  chat_history?: { role: string; content: string }[];
  top_k?: number;
  filter_document_id?: string;
}

export interface QueryResponse {
  question: string;
  answer: string;
  sources: SourceCitation[];
  retrieval_time_ms: number;
  generation_time_ms: number;
  query_intent?: string;
}

export interface Ticket {
  ticket_id: string;
  channel: ChannelType;
  customer_name: string;
  customer_tier: 'Standard' | 'Business' | 'Enterprise';
  subject: string;
  body: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  ai_draft?: QueryResponse;
  status: 'pending_review' | 'approved' | 'escalated';
}
```

---

## 2. Relational & Vector Database Schema (Supabase PostgreSQL + `pgvector`)

```sql
-- 1. Ingested Document Metadata Table
CREATE TABLE IF NOT EXISTS public.documents (
    file_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    gdrive_url TEXT,
    modified_time TEXT,
    md5_checksum TEXT,
    pages_count INTEGER DEFAULT 0,
    elements_count INTEGER DEFAULT 0,
    chunks_count INTEGER DEFAULT 0,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'indexed'
);

-- 2. Document Vector Chunks Table (with pgvector HNSW index)
CREATE TABLE IF NOT EXISTS public.document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES public.documents(file_id) ON DELETE CASCADE,
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    section TEXT,
    element_type TEXT NOT NULL,
    content TEXT NOT NULL,
    parent_element_id TEXT,
    gdrive_url TEXT,
    image_path TEXT,
    embedding vector(384), -- 384 dimensions for all-MiniLM-L6-v2 embeddings
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW Vector Index for ultra-fast Cosine Distance Search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON public.document_chunks USING hnsw (embedding vector_cosine_ops);

-- 3. Asynchronous Ingestion Job Tracker Table
CREATE TABLE IF NOT EXISTS public.ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL, -- 'processing', 'completed', 'completed_with_errors', 'failed'
    progress_percentage REAL DEFAULT 0.0,
    files_total INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    errors_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Customer Support Ticket Queue Table
CREATE TABLE IF NOT EXISTS public.tickets (
    ticket_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL, -- 'email', 'chat', 'api_docs', 'forum'
    customer_name TEXT NOT NULL,
    customer_tier TEXT DEFAULT 'Standard',
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    urgency TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending_review', -- 'pending_review', 'approved', 'escalated'
    ai_draft JSONB,
    confidence_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Agent Decision & Governance Audit Log Table
CREATE TABLE IF NOT EXISTS public.decision_logs (
    log_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    ticket_id TEXT NOT NULL,
    intent TEXT,
    confidence_score REAL,
    guardrail_passed BOOLEAN,
    guardrail_reason TEXT,
    action_taken TEXT NOT NULL, -- 'auto_replied', 'copilot_approved', 'escalated_tier2'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```


---

## 3. Mathematical & Algorithmic Formulations

### 3.1 Cosine Similarity Vector Score
Given query embedding vector $\vec{q}$ and chunk embedding vector $\vec{c}$:

$$\text{Similarity}(\vec{q}, \vec{c}) = \frac{\vec{q} \cdot \vec{c}}{\|\vec{q}\| \|\vec{c}\|} = \frac{\sum_{i=1}^{n} q_i c_i}{\sqrt{\sum_{i=1}^{n} q_i^2} \sqrt{\sum_{i=1}^{n} c_i^2}}$$

### 3.2 BM25 Okapi Scoring Formula
Given query tokens $Q = \{q_1, q_2, \dots, q_n\}$ and document chunk $D$:

$$\text{Score}_{BM25}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

where $k_1 = 1.5$, $b = 0.75$, $|D|$ is chunk length, and $\text{avgdl}$ is average chunk length across corpus.

### 3.3 Reciprocal Rank Fusion (RRF)
Combines dense vector rank $r_{\text{vec}}(d)$ and sparse BM25 rank $r_{\text{bm25}}(d)$ for chunk $d$:

$$\text{RRF\_Score}(d) = \alpha \cdot \frac{1}{k + r_{\text{vec}}(d)} + (1 - \alpha) \cdot \frac{1}{k + r_{\text{bm25}}(d)}$$

where $\alpha = 0.5$ and $k = 60$.

---

## 4. REST API Endpoint Specifications

| Endpoint | Method | Input Payload | Output Response | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | `HealthResponse` | Returns system status, vector store type, and active LLM provider. |
| `/drive/connect` | `POST` | `DriveConnectRequest` | `DriveConnectResponse` | Connects to Google Drive API or initializes sandbox mode. |
| `/drive/sync` | `POST` | `DriveSyncRequest` | `DriveSyncResponse` | Triggers async ingestion sync job. |
| `/drive/documents`| `GET` | None | `DriveDocumentsResponse` | Returns list of synced documents and metadata. |
| `/documents/{id}` | `DELETE` | `document_id` path | `{"status": "deleted"}` | Deletes document record, metadata, and vectors. |
| `/query` | `POST` | `QueryRequest` | `QueryResponse` | Executes hybrid search, reranking, grounded answer generation, and citations. |
