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
=======
# Project-Atlas
 origin/main
