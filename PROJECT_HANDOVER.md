# 🌐 Project Atlas — Executive Handover & Current Status

**Project Location:** `c:\Users\vivek kumar\Desktop\Project Atlas`  
**Current Status:** Phase 1 to Phase 4 Completed & Verified (22/22 Pytest Tests Passing)  
**Next Milestone:** Phase 5 (25 Evaluation Questions Benchmark & Docker Compose Packaging)

---

## 📌 Architecture & Modules Summary

1. **Frontend Portal (CodeIgniter 3 — Option 2 Enterprise Architecture)**:
   - Location: `Project Atlas/portal/`
   - Features: Session-based client switching (`C-01`, `C-02`, `C-03`), CSRF token protection, server-side cURL integration to FastAPI with timeout handling, client-restricted conversation history (IDOR protection), thumbs up/down feedback deduplication, XSS-safe dynamic rendering.
   - Views: Expandable Citations accordion, Conflicting Market Figures callout, Deterministic Calculation cards, Escalation status badges.

2. **Backend AI Service (FastAPI)**:
   - Location: `Project Atlas/backend/`
   - Endpoints:
     - `GET /health` (Database connectivity & latency check)
     - `POST /ingest` (Report chunking & metadata indexing)
     - `POST /chat` (Query routing, deterministic CAGR/projection tool, read-only SQL execution, prompt injection defense, conflict detection, auto-escalation)
     - `GET /escalations` (Escalation tickets management)

3. **Relational Database (MySQL 8.0)**:
   - Database: `project_atlas`
   - 12 Tables: `clients`, `client_report_entitlements`, `reports`, `market_metrics`, `conversations`, `messages`, `citations`, `feedback`, `escalations`, `security_events`, `request_metrics`, `ingestion_runs`.

4. **Vector Database (ChromaDB)**:
   - Location: `Project Atlas/vector_store/`
   - 6 Market Research Reports (`R-101` to `R-106`) with 27 indexed chunks.
   - Pre-LLM Entitlement filtering ensures Client `C-02` never retrieves unentitled `R-101` data.

---

## ⚡ Quick Run Commands (Windows Terminal / PowerShell / CMD)

### 1-Click Launch (Starts Backend + Portal):
```cmd
start.bat
```

### 1-Click Stop (Stops All Running Services):
```cmd
stop.bat
```

### Run Complete Pytest Suite (22/22 Passing):
```powershell
cd "c:\Users\vivek kumar\Desktop\Project Atlas"
backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Run Phase 4 Portal Verification (6/6 Checks Passing):
```powershell
cd "c:\Users\vivek kumar\Desktop\Project Atlas"
backend\.venv\Scripts\python.exe scripts/verify_phase4.py
```
- Interactive API Docs: http://localhost:8000/docs
- CodeIgniter 3 Portal: http://localhost:8080/
- Health Status: http://localhost:8000/health

---

## 📦 Git Repository Status
- Working Tree: **Clean** (All Phase 3 & Phase 4 additions committed to `main`).
- Protected Secrets: `.env`, `.venv`, and `vector_store/` are properly ignored by `.gitignore`.
