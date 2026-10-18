# Project Atlas — Development Status & Session Handover

**Last Updated:** Phase 2 (Knowledge Base, Ingestion & Access-Aware RAG) Completed  
**Current Milestone:** Phase 2 Complete -> Ready for Phase 3 (Agent Graph, Guardrails & Deterministic Calculator)

---

## 📌 Executive Summary & Goals
Project Atlas is a secure AI Market Research Report Copilot designed for market research analysts and corporate clients.
- **Frontend Portal**: Legacy PHP CodeIgniter 3 (CI3) application (Chat UI, CSRF/XSS protection, session management).
- **Backend AI Service**: Python FastAPI service with pre-LLM entitlement filtering, router, deterministic calculator, read-only SQL execution, critic/fact-checker, and automated escalation.
- **Relational Storage**: MySQL 8.0 containing 12 tables (clients, entitlements, reports, market metrics, conversations, messages, citations, feedback, escalations, security events, request metrics, ingestion runs).
- **Vector Database**: ChromaDB for chunked report embeddings with strict access filtering before passing context to LLM.
- **Evaluation Benchmark**: 25 evaluation questions suite spanning factual retrieval, conflicts, CAGR calculations, prompt injection traps, and SQL security.

---

## 🛠️ Completed in Phase 1 (Foundation)
- MySQL schema with 12 relational tables applied and verified.
- FastAPI backend with `/health` endpoint and Pydantic contracts.
- Pydantic Settings and isolated `.env` configuration.
- Automated tests passing.

---

## 📚 Completed in Phase 2 (Ingestion & Access-Aware RAG)

1. **6 Market Reports Corpus**:
   - `R-101`: Global Smart Water Meter Market 2025 (USD 4.21B hardware+software+services, 11.2% CAGR 2025-2030, 38% APAC share).
   - `R-102`: Smart Water Metering: Industry Outlook 2024 (USD 3.87B AMR/AMI hardware only, 9.8% CAGR 2024-2029, 41% APAC share, Page 14 prompt injection attack footnote preserved).
   - `R-103`: Residential Water Purifier Market 2025 (USD 9.54B in 2024, 7.4% CAGR).
   - `R-104`: European Commercial Heat Pump Market 2024 (USD 6.80B in 2024, 14.1% CAGR).
   - `R-105`: North America Smart Grid Sensors Market 2024 (USD 2.15B in 2024, 12.3% CAGR).
   - `R-106`: Global Industrial Wastewater Treatment Tech 2025 (USD 15.30B in 2024, 6.8% CAGR).

2. **ChromaDB Vector Store & Fast Embedding Engine**:
   - `backend/app/rag/vector_store.py`: Persistent ChromaDB collection `market_reports` with 384-dimensional dense semantic embedding engine.
   - Offline-first: Zero external network latency, 100% reproducible on local or Docker.
   - Total 27 paginated chunks indexed with rich metadata (`report_id`, `page`, `source_location`, `sector`, `region`, `year`, `access_policy`).

3. **Pre-LLM Entitlement Filtering Security Boundary (PRD AT-03)**:
   - `backend/app/rag/retriever.py`: Fetches active client entitlements from MySQL before querying vector database.
   - **Zero-leakage proof**: Client `C-02` (purchased `R-103` only) queries about `R-101` and retrieves strictly **ZERO** chunks from `R-101`.
   - Surfaces unentitled catalog reports for upgrade suggestions without leaking text or figures.
   - Preserves prompt injection attack text on R-102 page 14 as harmless passive data.

4. **API Ingestion Endpoint (`POST /ingest`)**:
   - Protected with `X-API-Key` service authentication.
   - Ingests single or batch reports and updates MySQL `ingestion_runs` table with chunk counts and timestamps.

5. **Automated Verification**:
   - `scripts/verify_phase2.py`: 5/5 verification steps passed.
   - Pytest suite (`test_health.py` and `test_rag.py`): 6/6 tests passing.

1. **Project Architecture & Directory Layout**:
   - Clean, modular repository layout matching PRD specifications.
   - Dedicated modules: `api`, `agent`, `rag`, `tools`, `security`, `services`, `schemas`, `tests`.

2. **Python Environment & Dependencies**:
   - Virtual environment configured in `backend/.venv` (Python 3.14/3.12 compatible via `uv`).
   - Packages installed: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `pymysql`, `cryptography`, `python-dotenv`, `pytest`, `httpx`.

3. **Configuration & Secrets Management**:
   - `.env` created with active local MySQL credentials (`project_atlas`, port 3306).
   - `.env.example` created with safe placeholders.
   - `.gitignore` configured to prevent committing `.env`, virtual environments, and temporary data.
   - `backend/app/config.py` uses `pydantic_settings.BaseSettings` with URL encoding for passwords with special characters.

4. **MySQL Database Architecture (12 Tables)**:
   - DDL defined in [`database/schema.sql`](file:///c:/Users/vivek%20kumar/Desktop/Project%20Atlas/database/schema.sql) and executed on live MySQL instance.
   - Tables created and verified:
     - `clients` (accounts & statuses)
     - `client_report_entitlements` (access control matrix)
     - `reports` (metadata & policies)
     - `market_metrics` (structured figures for read-only SQL queries)
     - `conversations` (chat session headers)
     - `messages` (multi-turn conversation flow)
     - `citations` (evidence per answer linked to reports)
     - `feedback` (thumbs up/down ratings)
     - `escalations` (analyst review tickets)
     - `security_events` (audit log for injection/unauthorized attempts)
     - `request_metrics` (latency, tokens, cost)
     - `ingestion_runs` (document processing status)
   - Baseline seed data loaded (Clients `C-01`, `C-02`, `C-03`; Reports `R-101` to `R-106`; Entitlements per AT-03).

5. **FastAPI Backend & Health Endpoint**:
   - `backend/app/main.py`: FastAPI application with CORS and startup database check.
   - `backend/app/api/health.py`: `GET /health` endpoint returning database connectivity and latency without exposing credentials.
   - `backend/app/schemas/contracts.py`: Typed contracts for Health, Chat, Citations, Conflicts, Derived Values, and Escalations.
   - `backend/app/security/auth.py`: Service API key header validation (`X-API-Key`).

6. **Automated Verification**:
   - Automated Pytest test suite: `backend/tests/test_health.py` (3/3 passed).
   - End-to-end verification script: `scripts/verify_phase1.py` passes all checks against live MySQL database.

---

## 🚀 Quick Commands for Resuming

### Run Verification Script:
```powershell
backend\.venv\Scripts\python.exe scripts/verify_phase1.py
```

### Run Pytest Suite:
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Start Backend Development Server:
```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🎯 Next Steps (Phase 2 Roadmap)
- [ ] Prepare initial 6 market research reports in `reports/` (PDF/Markdown/HTML including R-101 to R-106 and prompt injection trap in R-102).
- [ ] Implement chunking pipeline with metadata extraction (report ID, sector, year, page).
- [ ] Setup Vector Database (ChromaDB) with embeddings.
- [ ] Implement `POST /ingest` endpoint.
- [ ] Implement access-aware retriever with pre-LLM client entitlement filtering.
