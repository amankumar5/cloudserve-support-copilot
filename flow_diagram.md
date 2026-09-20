# Multimodal RAG & Support Copilot — Complete System Flow Diagrams

This document presents the complete end-to-end architecture, data processing pipelines, query execution flows, governance states, and database relationships for the **Multimodal RAG System & Support Copilot Workbench**.

![Support Copilot High-Tech System Architecture Diagram](/Users/aman/.gemini/antigravity-ide/brain/f03bd148-2a13-4297-b898-80847fd2e0da/system_flow_diagram_1789758333259.jpg)

---

## 1. High-Level End-to-End Architecture Flow

The following diagram illustrates the complete workflow from raw document ingestion in Google Drive to Tier 1 agent triage and decision logging in Supabase PostgreSQL.

```mermaid
graph TD
    subgraph Storage_Layer["1. Knowledge Source & Document Ingestion"]
        GDrive["📁 Google Drive KB (PDF, DOCX, XLSX, PNG)"] --> Loader["⚙️ Multi-Format Document Loader"]
        Loader --> Parser["🔍 Structure-Aware Parser & OCR"]
        Parser --> Chunker["✂️ Semantic & Table Chunker"]
        Chunker --> Embedder["🧠 Sentence-Transformers (384d Dense Embeddings)"]
        Embedder --> Supabase_Vector["🗄️ Supabase PostgreSQL (pgvector + HNSW)"]
    end

    subgraph Frontend_Layer["2. Angular 18+ Support Copilot SPA"]
        AgentUI["💻 Support Copilot Workbench (http://localhost:4200)"]
        TriageQueue["📋 Inbound Ticket Queue (Email, Chat, Forum)"]
        DraftEditor["✏️ Interactive Response Draft Editor"]
        ActionBtns["⚡ Approve / Escalate Actions"]
        AnalyticsDash["📊 SLA & FCR Performance Dashboard"]
        
        AgentUI --> TriageQueue
        AgentUI --> DraftEditor
        AgentUI --> ActionBtns
        AgentUI --> AnalyticsDash
    end

    subgraph Backend_Layer["3. FastAPI Core Engine (Python 8000)"]
        API_Route["🌐 FastAPI REST Router (/query, /tickets, /metrics)"]
        Intent_Class["🎯 Intent Classifier"]
        Hybrid_Retriever["🔎 Hybrid Search (Dense Vector + BM25 Sparse)"]
        RRF_Reranker["⚖️ Reciprocal Rank Fusion & Reranker"]
        LLM_Gen["🤖 Gemini 2.5 Flash Generator (Grounded Prompting)"]
        Guardrails["🛡️ Guardrail Auditor (PII / Billing / Confidence)"]

        API_Route --> Intent_Class
        Intent_Class --> Hybrid_Retriever
        Hybrid_Retriever --> Supabase_Vector
        Supabase_Vector --> RRF_Reranker
        RRF_Reranker --> LLM_Gen
        LLM_Gen --> Guardrails
        Guardrails --> API_Route
    end

    subgraph Audit_Layer["4. Governance & Audit Persistence"]
        DecisionLogs["📜 Supabase decision_logs Table"]
        TicketState["🎟️ Supabase tickets Table"]
        Guardrails --> DecisionLogs
        ActionBtns --> TicketState
        ActionBtns --> DecisionLogs
    end
```

---

## 2. Detailed Knowledge Base Ingestion Flow

This sequence shows how raw multi-modal files (PDFs, Tables, DOCX, Images) are fetched from Google Drive, processed, embedded, and stored in vector indices.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Support Admin / Cron
    participant API as FastAPI Server (/drive/sync)
    participant GDrive as Google Drive API
    participant Parser as Multi-Format Parser
    participant Embedder as SentenceTransformers (all-MiniLM-L6-v2)
    participant DB as Supabase PostgreSQL

    Admin->>API: Trigger KB Sync (POST /drive/sync)
    API->>DB: Log job in `ingestion_jobs` (status = running)
    API->>GDrive: List & Download Files (PDF, DOCX, XLSX, Images)
    GDrive-->API: Binary Stream & Metadata
    
    loop For Each Document
        API->>Parser: Parse Content & Structure
        alt Is PDF / DOCX
            Parser-->API: Extract Text Paragraphs & Structural Headers
        else Is XLSX Table
            Parser-->API: Serialize Rows/Columns into Markdown Tables
        else Is Image / Diagram
            Parser-->API: Extract OCR Text & Visual Captions
        end

        API->>API: Split into Overlapping Chunks (500 tokens, 50 overlap)
        API->>Embedder: Generate 384-dimensional Vectors
        Embedder-->API: Dense Floating Point Arrays
        API->>DB: Insert into `documents` & `document_chunks`
        DB-->API: Return Chunk IDs & HNSW Index Confirmation
    end

    API->>DB: Update `ingestion_jobs` (status = completed)
    API-->Admin: 200 OK (Sync Completed)
```

---

## 3. Copilot Query & Hybrid RAG Retrieval Flow

This diagram details the real-time query execution pipeline, combining dense vector semantic search with sparse BM25 keyword matching and LLM response generation with verifiable citations.

```mermaid
flowchart TD
    Start(["📩 User Selects Ticket / Asks Question"]) --> Intent["1. Classify Query Intent\n(Deployment, Auth, Billing, General)"]
    
    subgraph Retrieval_Stage["2. Dual-Path Retrieval Engine"]
        Intent --> Dense["2a. Supabase pgvector RPC\nmatch_document_chunks()\n(Cosine Similarity)"]
        Intent --> Sparse["2b. BM25 Keyword Search\n(Exact Term Matching)"]
    end

    Dense --> Merge["3. Reciprocal Rank Fusion (RRF)\nCombine Ranks: RRF_score = ∑ 1 / (60 + rank)"]
    Sparse --> Merge
    
    Merge --> Rerank["4. Reranking & Top-5 Selection\nFilter Top Passages with Metadata"]
    
    subgraph Generation_Stage["5. Grounded LLM Generation"]
        Rerank --> SystemPrompt["Construct Grounded Prompt:\n- Ticket Context & Customer Tier\n- Top 5 Relevant Chunks\n- Citation Formatting Rules"]
        SystemPrompt --> Gemini["Gemini 2.5 Flash Model"]
        Gemini --> Response["Generate Response Text + Source Citations"]
    end

    Response --> GuardrailCheck{"6. Guardrail & Confidence Audit"}
    GuardrailCheck -- "Score >= 0.60 & Safe" --> ReturnDraft["Output Grounded Draft + Verifiable Citations"]
    GuardrailCheck -- "Score < 0.60 or Billing Query" --> EscalateFlag["Flag for Tier 2 Escalation"]
    
    ReturnDraft --> UI["Display Draft in Angular Copilot Workbench"]
    EscalateFlag --> UI
```

---

## 4. Human-in-the-Loop (HITL) Workbench & Governance Flow

State transitions for inbound support tickets, agent actions, and governance audit logging.

```mermaid
stateDiagram-v2
    [*] --> New: Inbound Ticket Creation (Email / Chat / Forum)
    
    New --> PendingReview: Automatically Ingested into Copilot Queue
    
    state PendingReview {
        [*] --> RAGGeneration: Hybrid Vector Search & Gemini Synthesis
        RAGGeneration --> DraftReady: Render AI Draft + Citations
        
        state DraftReady {
            DraftReady --> EditingMode: Agent Clicks 'Edit Draft'
            EditingMode --> DraftReady: Agent Saves Custom Changes
        }
    }
    
    PendingReview --> Approved: Agent Clicks 'Approve & Send'
    PendingReview --> Escalated: Agent Clicks 'Escalate to Tier 2'
    
    state Approved {
        [*] --> DispatchedToCustomer: Response Sent to Customer
        [*] --> AuditLoggedApproved: Logged in decision_logs (action = approved)
    }
    
    state Escalated {
        [*] --> ContextPackageDrawer: Generate Context Package Handoff
        [*] --> AuditLoggedEscalated: Logged in decision_logs (action = escalated_tier2)
    }

    Approved --> [*]
    Escalated --> [*]
```

---

## 5. Database Schema Entity-Relationship Diagram (ERD)

The database schema hosted on **Supabase PostgreSQL** (`pgvector` enabled) powering vector indexing, ticket states, and governance audit trails.

```mermaid
erDiagram
    documents ||--o{ document_chunks : "contains (1:N)"
    documents ||--o{ ingestion_jobs : "tracked by"
    tickets ||--o{ decision_logs : "audited by (1:N)"
    
    documents {
        uuid id PK
        string gdrive_file_id
        string file_name
        string mime_type
        int total_pages
        timestamp created_at
    }

    document_chunks {
        uuid id PK
        uuid document_id FK
        text chunk_text
        int page_number
        string section_title
        vector_384 embedding "HNSW Index (vector_cosine_ops)"
        jsonb metadata
    }

    ingestion_jobs {
        uuid id PK
        string job_status
        int files_processed
        text error_message
        timestamp started_at
        timestamp completed_at
    }

    tickets {
        string ticket_id PK
        string customer_name
        string customer_tier
        string channel
        string urgency
        text subject
        text body
        string status "pending_review | approved | escalated"
        float confidence_score
        timestamp created_at
    }

    decision_logs {
        uuid id PK
        string ticket_id FK
        string agent_id
        string action "approved | edited | escalated_tier2"
        text final_response_text
        float confidence_score
        jsonb retrieved_source_ids
        timestamp timestamp
    }
```

---

## 6. System Interaction Matrix

| Component | Port / Endpoint | Primary Function | Connected Dependencies |
| :--- | :--- | :--- | :--- |
| **Angular SPA** | `http://localhost:4200` | Support Copilot Workbench UI | FastAPI Backend (`http://localhost:8000`) |
| **FastAPI Core** | `http://localhost:8000` | REST API Router & RAG Pipeline | Supabase PostgreSQL, Gemini API, SentenceTransformers |
| **Supabase PostgreSQL** | `rsvyeeepjjlehqkbmcuk.supabase.co` | Vector Search & Metadata Database | `pgvector` HNSW index, `match_document_chunks` RPC |
| **Gemini 2.5 Flash** | Cloud API | Grounded LLM Response Generation | `google-generativeai` SDK |
| **SentenceTransformers** | Local (`all-MiniLM-L6-v2`) | 384-dimensional Dense Text Embeddings | PyTorch CPU runtime |
