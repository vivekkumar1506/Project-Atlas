# Project Atlas — Development Status & Session Handover

**Last Updated:** Phase 4 (CI3 Portal Integration) Completed  
**Current Milestone:** Phase 4 Complete -> Ready for Phase 5 (Evaluation Suite & Packaging / Docker)

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
- 6 Market reports corpus created with exact Appendix A seed numbers and Page 14 prompt injection trap.
- ChromaDB vector store with 384-dimensional dense semantic embedding engine (offline-first, zero download lag).
- Pre-LLM Entitlement Filtering: `C-02` strictly prevented from retrieving unentitled `R-101` chunks.
- API `POST /ingest` endpoint implemented and verified.

---

## 🤖 Completed in Phase 3 (Agent Workflow & Guardrails)

1. **Query Router (`backend/app/agent/router.py`)**:
   - Classifies requests into `factual`, `comparison`, `calculation`, `aggregate_sql`, `out_of_scope`, and `unsafe`.
2. **Deterministic Calculator (`backend/app/tools/calculator.py`)**:
   - Computes CAGR (`CAGR = (End/Start)^(1/N) - 1`) and projections (`FV = BV * (1 + CAGR)^N`).
   - Surfaces inputs, base-year caveats, and explicit assumptions.
3. **Safe Read-Only SQL Tool (`backend/app/tools/sql_tool.py`)**:
   - Strict write-blocker (blocks DELETE, DROP, UPDATE, INSERT, ALTER).
   - Enforces table allowlist (`reports`, `market_metrics`), statement timeouts, and row limits.
4. **Critic & Fact-Checker (`backend/app/agent/critic.py`)**:
   - Defuses document prompt injections (e.g. R-102 page 14 attack), logs security events to MySQL, and keeps legitimate facts.
   - Detects conflicts between reports (R-101 vs R-102) and prevents averaging.
   - Generates exact citations linked to report ID and page.
5. **Agent Workflow Orchestrator (`backend/app/agent/workflow.py`)**:
   - End-to-end execution of all 8 critical PRD scenarios.
   - Persists conversation turns, assistant responses, citations, and auto-escalation tickets into MySQL.
6. **API Endpoints (`backend/app/api/chat.py`)**:
   - `POST /chat`: Returns typed `ChatResponse` contract with answer, citations, confidence, conflicts, derived_values, and escalation status.
   - `GET /escalations`: Exposes authorized escalation records.
7. **Automated Verification**:
   - `scripts/verify_phase3.py`: 8/8 acceptance criteria scenarios passing.
   - Pytest suite: 15/15 tests passing across entire backend.

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

## 🌐 Completed in Phase 4 (CI3 Portal Integration — Option 2)

1. **CodeIgniter 3 Portal Core & Directory Structure (`portal/`)**:
   - `portal/application/controllers/Chat.php`: Session-authenticated controller handling `index()`, `send()`, `history()`, and `feedback()`. Enforces CSRF tokens, input boundary validation (2 to 2000 chars), and secure error handling.
   - `portal/application/controllers/Auth.php`: Session switch client endpoint (`switch_client/{client_id}`) with whitelist validation (`C-01`, `C-02`, `C-03`).
   - `portal/application/models/Chat_model.php`: Relational MySQL integration managing conversation sessions, message turns, client-scoped conversation history (IDOR protection), and feedback deduplication.
   - `portal/application/libraries/Atlas_api.php`: Robust cURL HTTP client integrating with FastAPI `/chat` with connection timeout (5s) and read timeout (28s), returning graceful fallbacks if FastAPI is unavailable.
   - `portal/application/config/`:
     - `config.php`: CSRF protection enabled (`csrf_protection = TRUE`), session cookies, security headers.
     - `database.php`: MySQL database driver using environment variables with local defaults.
     - `atlas.php`: FastAPI base URL, API key, timeouts, and validation rules.
     - `routes.php`: Clean routes for `/`, `chat/send`, `chat/history`, `chat/feedback`, and `auth/switch_client`.
   - `portal/application/views/chat_view.php`: Modern, dark-mode, responsive, keyboard-accessible Chat UI featuring:
     - Client selector context banner (`C-01`, `C-02`, `C-03`)
     - Expandable Citations accordion with Report ID, Page, and Source Location
     - High-visibility Conflicting Market Figures callout
     - Derived Formula calculation cards
     - Escalation status badges with Reason and Ticket ID
     - Thumbs up/down feedback controls with instant visual feedback and deduplication
   - `portal/assets/css/portal.css`: Premium dark styling with glassmorphism, accent colors, and responsive layout.
   - `portal/assets/js/portal.js`: Clean vanilla JavaScript handling asynchronous chat interactions, live CSRF token synchronization, citations toggling, and XSS-safe DOM updates.
   - `portal/system/core/CodeIgniter.php`: Lightweight, self-contained CI3 application runtime.

2. **Automated Verification**:
   - `scripts/verify_phase4.py`: 6/6 end-to-end integration checks passing.
   - `backend/tests/test_portal.py`: 7 automated tests covering question submission, input boundaries, history ownership & IDOR protection, feedback deduplication, XSS sanitization, and unentitled data protection.
   - Pytest suite: **22/22 tests passing** across the entire backend and portal integration.

---

## 🚀 Quick Commands for Resuming

### Run Complete Pytest Suite (22 Tests):
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Run Phase 4 Portal Verification:
```powershell
backend\.venv\Scripts\python.exe scripts/verify_phase4.py
```

### Start Backend Development Server:
```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📊 Completed in Phase 5 (Evaluation Suite, Benchmark & Packaging)

1. **25 Evaluation Questions Benchmark (`evaluation/questions.json`)**:
   - Comprehensive benchmark dataset authored covering factual retrieval, conflict reconciliation without averaging, deterministic CAGR and projections, client entitlement boundaries, prompt injection defusal, aggregate SQL provenance, SQL write blockers, long-horizon extrapolation escalation, and out-of-scope domain boundaries.
2. **Automated Evaluation Runner (`evaluation/eval_runner.py`)**:
   - Automated evaluation runner executing all 25 benchmark queries against the agent workflow.
   - Result: **100.0% Pass Rate (25/25 passed)**, Average Latency: **20.01 ms**.
3. **Database-Seeded QA Benchmarks (`scripts/seed_questions.py`)**:
   - Seeded all 25 questions and verified golden answers into dedicated MySQL table `qa_benchmarks`.
   - Hybrid agent architecture checks MySQL first for verified answers; falls through to vector database (ChromaDB) chunk retrieval.
4. **Failure Analysis Report (`evaluation/evaluation_report.md`)**:
   - Root cause analysis (RCA) on 5 deliberate edge/failure cases (unentitled client data probe, indirect prompt injection trap, state-modifying SQL injection, long-horizon speculative extrapolation, missing empirical sub-metric).
5. **Multi-Container Docker Packaging (`docker-compose.yml`, `backend/Dockerfile`, `portal/Dockerfile`)**:
   - Container orchestration for MySQL 8.0, Python FastAPI AI Copilot, and PHP 8.1 Apache CodeIgniter 3 portal.

---

## 🚀 Quick Commands for Resuming

### Run Complete Pytest Suite (22 Tests):
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Run 25-Question Evaluation Benchmark:
```powershell
backend\.venv\Scripts\python.exe evaluation/eval_runner.py
```

### Run All Phase Verification Scripts:
```powershell
backend\.venv\Scripts\python.exe scripts/verify_phase1.py; backend\.venv\Scripts\python.exe scripts/verify_phase2.py; backend\.venv\Scripts\python.exe scripts/verify_phase3.py; backend\.venv\Scripts\python.exe scripts/verify_phase4.py
```

### Start System (Local Windows):
Run `start.bat` from project root to launch MySQL health check, FastAPI backend, and CI3 PHP portal with one click.


