# Project Atlas — AI Market Research Report Copilot

Project Atlas is an enterprise-grade AI Copilot designed for market research analysts and corporate clients. It integrates with an existing PHP CodeIgniter 3 portal and provides trusted, cited, entitlement-enforced market research answers with automated escalation and deterministic calculations.

---

## 🏗️ Architecture Overview

```
                                  +-----------------------------+
                                  |   Corporate Client (Portal) |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  | PHP + CodeIgniter 3 Portal  |
                                  | Session, UI, CSRF / XSS Esc |
                                  +--------------+--------------+
                                                 | (REST + API Key)
                                                 v
                                  +-----------------------------+
                                  |      FastAPI AI Service     |
                                  | Auth, Entitlements, Route   |
                                  +--------------+--------------+
                                                 |
                        +------------------------+------------------------+
                        |                                                 |
                        v                                                 v
           +--------------------------+                      +--------------------------+
           |     MySQL Database       |                      |     Vector Database      |
           | Entitlements, Metrics,   |                      | Report Chunks, Embeddings|
           | Conversations, Tickets   |                      | Metadata Filters         |
           +--------------------------+                      +--------------------------+
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- MySQL 8.0+ (running locally or in Docker)
- Git

### 1. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
copy .env.example .env
```
Ensure your MySQL credentials (`MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`) are configured.

### 2. Install Dependencies
```bash
# Using uv (fastest)
uv venv backend/.venv
uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe

# Or standard pip
python -m venv backend/.venv
backend\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. One-Click Prototype Launcher (`start.bat` & `stop.bat`)
To start all prototype services (FastAPI AI Backend + CodeIgniter 3 Portal) simultaneously:
```cmd
start.bat
```
- **Automatic Environment Verification:** Verifies `.env` exists (creates from `.env.example` if missing), checks Python virtual environment, and verifies dependencies.
- **Port Detection & Duplicate Prevention:** Detects configured ports (`8000` and `8080`), probes active sockets, and skips launching duplicate servers if already running.
- **Separate Visible Consoles:** Opens FastAPI backend on port 8000 and CodeIgniter 3 portal on port 8080 in separate titled terminal windows so runtime errors remain visible.
- **Local Access URLs:**
  - CodeIgniter 3 Portal UI: [http://localhost:8080/](http://localhost:8080/)
  - FastAPI AI Backend Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Health Check Endpoint: [http://localhost:8000/health](http://localhost:8000/health)

To stop all background services gracefully at any time:
```cmd
stop.bat
```

### 4. Manual Startup (Alternative)
```cmd
:: Terminal 1 - Backend API
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

:: Terminal 2 - CodeIgniter 3 Portal
cd portal
php -S 0.0.0.0:8080
```
- Authenticated client sessions can be switched dynamically between `C-01` (Northwind Utilities), `C-02` (Blue Delta Infra), and `C-03` (Gamma Analytics) using the header dropdown.

### 5. Run Automated Tests & Verifications (Windows CMD)
```cmd
:: Run Full Automated Test Suite (22 Tests)
backend\.venv\Scripts\python.exe -m pytest backend/tests -v

:: Run Phase-Specific Verifications
backend\.venv\Scripts\python.exe scripts/verify_phase1.py
backend\.venv\Scripts\python.exe scripts/verify_phase2.py
backend\.venv\Scripts\python.exe scripts/verify_phase3.py
backend\.venv\Scripts\python.exe scripts/verify_phase4.py
```

---

## 📋 Project Structure

```
project-atlas/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app lifecycle & routes
│   │   ├── config.py            # Pydantic Settings & environment variables
│   │   ├── api/                 # API route handlers (/health, /chat, etc.)
│   │   ├── agent/               # LangGraph/Workflow, router, critic
│   │   ├── rag/                 # Report ingestion, chunking, embeddings
│   │   ├── tools/               # Deterministic calculator & safe SQL tool
│   │   ├── security/            # Service auth & entitlement verification
│   │   └── services/            # MySQL connection & session management
│   ├── tests/                   # Automated pytest suite
│   └── requirements.txt
├── database/
│   └── schema.sql               # MySQL DDL and baseline seed data
├── portal/                      # CodeIgniter 3 integration portal
├── reports/                     # Market research reports (PDF/HTML/MD)
├── evaluation/                  # Evaluation question suite & reports
├── .env.example                 # Safe environment variables template
├── .env                         # Local secrets (git ignored)
└── README.md
```

---

## 🛡️ Security & Privacy
- **Zero Secret Leaks**: Credentials reside in `.env` and are never committed to git.
- **Pre-LLM Entitlement Filtering**: Restrict report chunks in retrieval layer before LLM sees data.
- **Deterministic Math**: Financial computations (CAGR, forecasts) run through Python calculators, never raw LLM mental math.
- **SQL Guardrails**: Read-only parameterized execution only; DDL/DML injection attempts blocked.

---

## 🧪 Phase 5 — AI Evaluation, Security & Packaging

### Run Phase 5 Complete Verification Suite:
```powershell
backend\.venv\Scripts\python.exe scripts/verify_phase5.py
```
- **25 Benchmark Questions:** 100% Pass Rate (25/25), Average Latency: ~15-20 ms.
- **Security Testing:** Verifies entitlement isolation (C-02 restricted from R-101), direct/indirect prompt injection defusal, and SQL write blockers (`DELETE`, `DROP`, `UPDATE`, `INSERT`, `ALTER`).
- **Failure Analysis:** Regression validation of 5 analyzed edge cases.
- **Deployment Verification:** Validates Docker Compose, Dockerfiles, environment isolation, and health checks.

### Run All 22 Pytest Tests:
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

---

## 🐳 Production Deployment (Docker Compose) vs Local Prototype

### 1. Local Prototype (Quick Development & Demo)
- Run `start.bat` to launch local Python FastAPI and PHP built-in server with visible terminals.
- Stop gracefully with `stop.bat`.
- Uses active local MySQL instance.

### 2. Production Deployment (Docker Compose)
- Multi-container topology defined in [`docker-compose.yml`](docker-compose.yml):
  - **`mysql`**: MySQL 8.0 with automated schema initialization from `database/schema.sql` and healthcheck.
  - **`backend`**: Python 3.11 container with FastAPI service running on port `8000`.
  - **`portal`**: PHP 8.1 Apache container with `mod_rewrite`, `mysqli`, and `curl` on port `8080`.
  - **Isolated Bridge Network**: `atlas_network` with named persistent volumes for MySQL and ChromaDB.

To spin up the entire production stack:
```bash
docker compose up --build -d
```
To verify container health:
```bash
docker compose ps
```
To tear down:
```bash
docker compose down
```
