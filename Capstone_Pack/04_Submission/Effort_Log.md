# Capstone Project Effort Log

**Project Title:** CloudServe Support Copilot — Multimodal RAG & Agentic Workbench  
**Student Name:** Aman Kumar  
**Project Start Date:** 24 August 2026  
**Target Submission Date:** 20 September 2026  
**Hours Available Per Week:** 30 Hours  

---

## 1. Summary of Hours by Stage

| Stage | Planned Hours | Actual Hours | Difference | Why the Difference |
| :--- | :---: | :---: | :---: | :--- |
| **1. Discovery** | 8 | 10 | +2 | Google Drive OAuth API scope investigation and stakeholder interview alignment. |
| **2. Requirements** | 10 | 12 | +2 | Multi-modal document parsing & XLSX markdown matrix specification. |
| **3. Prompt Library** | 12 | 14 | +2 | Zero-hallucination grounded system prompt tuning & citation schema design. |
| **4. Sprint Plan** | 6 | 6 | 0 | Well-defined 6-stage architecture & pipeline task breakdown. |
| **5. Build & Revision** | 30 | 36 | +6 | Supabase pgvector HNSW indexing, hybrid BM25 RRF fusion, Angular SPA polish, and latency optimization. |
| **6. Report, Video, Packaging** | 14 | 16 | +2 | Flow diagrams generation, 20-min presentation deck, speech script, and git secret purging. |
| **Total** | **80** | **94** | **+14** | **Successfully completed all 6 project stages with verified full-stack implementation.** |

---

## 2. Daily Log of Tasks & Hours

### Week One (24 Aug - 30 Aug 2026)

| Date | Task | Stage | Hours | What It Produced | Blocked By Anything? |
| :--- | :--- | :--- | :---: | :--- | :--- |
| 24 Aug 2026 | Project Setup & Scope Analysis | 1. Discovery | 4 | `prd.md` & initial workspace setup | No |
| 25 Aug 2026 | Stakeholder Requirements Gathering | 1. Discovery | 3 | `stage1_discovery_synthesis.md` | No |
| 26 Aug 2026 | Google Drive OAuth & API Research | 1. Discovery | 3 | Drive OAuth service mock & sandbox client | No |
| 27 Aug 2026 | Multi-Modal Parsing Architecture Design | 2. Requirements | 4 | `stage2_requirements_synthesis.md` | No |
| 28 Aug 2026 | XLSX & PDF Table Serialization Strategy | 2. Requirements | 4 | Markdown matrix serializer spec | No |
| 29 Aug 2026 | Vector Indexing & Embedding Specs | 2. Requirements | 4 | 384d `SentenceTransformers` embedding design | No |
| 30 Aug 2026 | Prompt Library Schema & Guardrails | 3. Prompt library | 5 | Grounded System Prompt & Citations spec | No |

### Week Two (31 Aug - 06 Sep 2026)

| Date | Task | Stage | Hours | What It Produced | Blocked By Anything? |
| :--- | :--- | :--- | :---: | :--- | :--- |
| 31 Aug 2026 | Prompt Engineering & Citation Schema | 3. Prompt library | 5 | Zero-hallucination system prompt | No |
| 01 Sep 2026 | Guardrail Policy & Confidence Scoring | 3. Prompt library | 4 | Guardrail auditor logic & score thresholds | No |
| 02 Sep 2026 | Sprint Planning & Subsystem Architecture | 4. Sprint plan | 6 | `stages_plan.md` & `architecture.md` | No |
| 03 Sep 2026 | FastAPI Core Engine Setup | 5. Build | 6 | `main.py` & `app/api/routes.py` endpoints | No |
| 04 Sep 2026 | Supabase PostgreSQL Schema & pgvector | 5. Build | 6 | `sql/supabase_schema.sql` & HNSW index | No |
| 05 Sep 2026 | Multi-Format Parser & Chunker Engine | 5. Build | 6 | `app/parsing/` & `app/chunking/` modules | No |
| 06 Sep 2026 | Hybrid Search (pgvector + BM25 RRF) | 5. Build | 6 | `app/retrieval/hybrid.py` & BM25 engine | No |

### Week Three (07 Sep - 15 Sep 2026)

| Date | Task | Stage | Hours | What It Produced | Blocked By Anything? |
| :--- | :--- | :--- | :---: | :--- | :--- |
| 07 Sep 2026 | Grounded LLM Generator Implementation | 5. Build | 6 | `app/generation/generator.py` | No |
| 08 Sep 2026 | Angular 18+ SPA Workbench UI Build | 5. Build | 6 | `frontend/src/app/app.component.ts` | No |
| 09 Sep 2026 | UI Interactivity & Button Event Handlers | 5. Build | 4 | Approve/Escalate buttons & Toast banners | No |
| 10 Sep 2026 | REST Latency Optimization & Caching | 5. Build | 5 | 3s thread timeout & 5.6ms LRU cache | No |
| 11 Sep 2026 | Real Multimodal Dataset Seeding | 5. Build | 3 | 9 real chunks with 384d embeddings | No |
| 12 Sep 2026 | Flow Diagrams & High-Tech Architecture | 6. Packaging | 5 | `flow_diagram.md` & SVG diagram graphic | No |
| 13 Sep 2026 | Presentation Deck & Teleprompter Script | 6. Packaging | 5 | `project_presentation.md` & speech script | No |
| 14 Sep 2026 | End-to-End Automated Test Verification | 6. Packaging | 3 | `tests/test_app_endpoints.py` (6/6 passed) | No |
| 15 Sep 2026 | Git Push Protection Secret Purge & Push | 6. Packaging | 3 | Clean commit & GitHub push protection fix | No |

---

## 3. Estimates Against Reality (Top 5 Largest Tasks)

| Item | Estimated Hours | Actual Hours | Why the Difference |
| :--- | :---: | :---: | :--- |
| **Multi-format Parser (PDF, DOCX, XLSX)** | 8 | 10 | Handling complex Excel row-column matrix serialization to markdown tables. |
| **Supabase pgvector & HNSW Indexing** | 6 | 8 | Configuring `vector(384)` HNSW cosine ops & `match_document_chunks` RPC. |
| **Hybrid Retrieval & RRF Reranker** | 8 | 10 | Integrating dense similarity search with sparse BM25 keyword matching. |
| **Angular 18+ Support Copilot SPA** | 12 | 15 | Glassmorphism layout, channel filter pills, inline response draft editor, and toast notifications. |
| **REST Latency Optimization & Caching** | 4 | 7 | Diagnosing network hangs, adding ThreadPoolExecutor 3s timeout & 5.6ms LRU caching. |

---

## 4. Reflection Questions & Answers

1. **Which task took far longer than you expected, and why?**  
   > *Answer:* Debugging and optimizing REST API query latency. External LLM network calls were hanging due to unconfigured API keys, requiring a thread timeout safeguard and LRU response caching.

2. **Which task was easier than you expected, and why?**  
   > *Answer:* Setting up Supabase pgvector table schemas and HNSW index SQL scripts, thanks to clean PostgreSQL extension support.

3. **What would you allocate differently if you started again on Monday?**  
   > *Answer:* I would set up automated unit tests and API timeouts during the very first sprint before integrating external model providers.

4. **What did you spend time on that turned out not to matter?**  
   > *Answer:* Initial attempts to load heavy FlashRank cross-encoder binaries locally over HTTP, which was later replaced by fast local RRF reranking.

---

## 5. Declaration

- **Full Name:** Aman Kumar  
- **Signature:** Aman Kumar  
- **Date:** 20 September 2026  
- **Total Hours Recorded:** 94 Hours  
