# Requirements & Architecture Revision Log (Change Log)
## CloudServe Support Automation System

- **Document Version**: 2.0
- **Tracking Period**: Week 1 (Discovery) to Week 3 (Submission)

---

## 1. PRD & Scope Revision Log

| Revision ID | Date | Requirement Impacted | Original Assumption (v1.0) | Revised Requirement (v2.0) | Rationale & Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CHG-001** | 2026-09-05 | **REQ-002 (Autonomous Bot)** | Fully automated chatbot sending direct replies to all customers. | **Copilot Mode (Agent-in-the-Loop)** for Medium confidence; Auto-reply only for High confidence ($\ge 0.85$). | Discovery Interview 2 (Sofia): Agents were afraid of apologizing for automated AI mistakes. Copilot mode saves 50% time while eliminating customer trust risk. |
| **CHG-002** | 2026-09-08 | **REQ-007 (Search Strategy)** | Vector-only semantic search using ChromaDB. | **Hybrid Search**: Dense Vector (ChromaDB) + Sparse Keyword (BM25) with Reciprocal Rank Fusion (RRF). | Tech Writer Interview (Ines): Keyword search failed on exact technical terms (error codes, CLI flags) where vector similarity had low precision. |
| **CHG-003** | 2026-09-11 | **REQ-006 (Guardrails)** | Simple keyword blocklist for sensitive words. | **Structured Multi-Category Guardrail Agent** (Security, Billing, Compliance). | Tier 2 Interview (Daniel): Security password resets, contract billing disputes, and data residency require strict legal compliance and must never be automated. |
| **CHG-004** | 2026-09-14 | **REQ-UI-01 (Frontend Stack)** | Simple static HTML dashboard. | **Modern Angular 18+ SPA** with standalone components, RxJS state management, and real-time SLA timers. | Technical requirement for enterprise support copilot workspace with dual-pane review and 1-click agent actions. |
| **CHG-005** | 2026-09-17 | **REQ-ING-01 & REQ-IDX-02** | Local SQLite + ChromaDB storage. | **Supabase PostgreSQL + `pgvector` HNSW Index** across 5 unified tables (`documents`, `document_chunks`, `ingestion_jobs`, `tickets`, `decision_logs`). | Production persistence, real-time ticket queue sync, and sub-millisecond vector similarity RPC stored procedures (`match_document_chunks`). |
| **CHG-006** | 2026-09-18 | **PRD & Governance Alignment** | Basic PRD v2.0 document. | **PRD v2.1 (Production & Capstone Aligned)** incorporating all 12 Acceptance Criteria (A1-A12), 7 NFR categories, 15-field decision log schema, Emergency Kill-Switch, and Risk Register (R-01 to R-08). | Full compliance with `Capstone_Pack` Stage 2 PRD requirements, Stakeholder Interviews evidence, Evaluation Framework, and Governance specs. |

---


## 2. Architectural Modifications & Trade-Offs

### 1. Production Storage & Vector Database (Supabase PostgreSQL + `pgvector`)
- *Decision*: Upgraded to Supabase PostgreSQL with `pgvector` HNSW vector index (`vector(384)` with `vector_cosine_ops`), while retaining local SQLite/ChromaDB abstract fallback capabilities.
- *Trade-off*: Provides cloud persistence, real-time ticket queue synchronization, and sub-millisecond vector similarity queries via PostgreSQL stored procedure RPC (`match_document_chunks`).

### 2. LLM Provider Flexibility (Gemini 2.5 Flash + Fallback)
- *Decision*: Configured Gemini 2.5 Flash as primary LLM provider with deterministic synthesis fallback.
- *Trade-off*: Ensures system remains 100% runnable and passes offline validation even if internet or LLM API keys are unavailable.


---

## 3. Reflection & Key Lessons Learned

1. **Discovery First, Code Second**: Spending 3 full days analyzing stakeholder interviews and ticket data prevented building a naive chatbot that would have failed client expectations.
2. **Structure-Aware Chunking is Critical for Business Documents**: Naive fixed-size chunking broke tables in half, causing revenue queries to fail. Keeping tables intact as unified Markdown blocks solved table QA completely.
3. **Transparency Builds Trust**: Explicit AI disclosure and clickable KB citations allow agents and customers to calibrate trust accurately.
