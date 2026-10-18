"""Report Ingestion Pipeline for Project Atlas."""
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import text

from backend.app.rag.vector_store import get_reports_collection
from backend.app.services.db import SessionLocal

logger = logging.getLogger("atlas.ingestion")


def parse_report_file(file_path: Path) -> Dict[str, Any]:
    """Parse Markdown report file into metadata and paginated chunks."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    metadata = {
        "report_id": file_path.stem.split("_")[0],
        "title": file_path.stem.replace("_", " "),
        "sector": "Utilities",
        "region": "Global",
        "year": 2024,
        "access_policy": "paid",
    }

    # Extract metadata from header
    for line in lines[:20]:
        if line.startswith("# "):
            metadata["title"] = line.replace("# ", "").strip()
        elif "**Report ID:**" in line:
            metadata["report_id"] = line.split("**Report ID:**")[-1].strip()
        elif "**Sector:**" in line:
            metadata["sector"] = line.split("**Sector:**")[-1].strip()
        elif "**Region:**" in line:
            metadata["region"] = line.split("**Region:**")[-1].strip()
        elif "**Access Policy:**" in line:
            metadata["access_policy"] = line.split("**Access Policy:**")[-1].strip()
        elif "**Published Date:**" in line:
            date_str = line.split("**Published Date:**")[-1].strip()
            match = re.search(r"\b(202\d)\b", date_str)
            if match:
                metadata["year"] = int(match.group(1))

    # Split by Page markers <!-- Page X -->
    page_splits = re.split(r"<!--\s*Page\s*(\d+)\s*-->", content)

    chunks: List[Dict[str, Any]] = []

    if len(page_splits) > 1:
        # First element before Page 1 (header)
        preamble = page_splits[0].strip()
        if preamble:
            chunks.append({
                "page": 1,
                "section": "Overview",
                "text": preamble,
            })

        for i in range(1, len(page_splits), 2):
            page_num = int(page_splits[i])
            page_content = page_splits[i + 1].strip()

            # Split page by sections (## headings) if page has multiple sections
            section_splits = re.split(r"(##\s+[^\n]+)", page_content)
            if len(section_splits) > 1:
                current_section = f"Page {page_num}"
                for s_part in section_splits:
                    s_part = s_part.strip()
                    if not s_part:
                        continue
                    if s_part.startswith("## "):
                        current_section = s_part.replace("## ", "").strip()
                    else:
                        chunks.append({
                            "page": page_num,
                            "section": current_section,
                            "text": s_part,
                        })
            else:
                chunks.append({
                    "page": page_num,
                    "section": f"Page {page_num}",
                    "text": page_content,
                })
    else:
        # Fallback split by sections
        chunks.append({
            "page": 1,
            "section": "Full Document",
            "text": content.strip(),
        })

    return {
        "metadata": metadata,
        "chunks": chunks,
    }


def ingest_report(file_path: Path) -> Dict[str, Any]:
    """Ingest a single report file into vector DB and update MySQL tracking."""
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    start_time = datetime.now(timezone.utc)
    parsed = parse_report_file(file_path)
    meta = parsed["metadata"]
    chunks = parsed["chunks"]

    report_id = meta["report_id"]
    collection = get_reports_collection()

    # Log ingestion run in MySQL
    db = SessionLocal()
    try:
        db.execute(
            text(
                "INSERT INTO ingestion_runs (run_id, report_id, status, chunks_count, started_at) "
                "VALUES (:run_id, :report_id, 'running', :chunks_count, :started_at)"
            ),
            {
                "run_id": run_id,
                "report_id": report_id,
                "chunks_count": len(chunks),
                "started_at": start_time,
            },
        )
        db.commit()

        # Delete existing chunks for this report in ChromaDB to prevent duplication
        try:
            existing = collection.get(where={"report_id": report_id})
            if existing and existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception as exc:
            logger.debug(f"Chroma delete check: {exc}")

        # Prepare records for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{report_id}_p{chunk['page']}_{idx}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append({
                "report_id": report_id,
                "title": meta["title"],
                "sector": meta["sector"],
                "region": meta["region"],
                "year": meta["year"],
                "page": chunk["page"],
                "source_location": f"Page {chunk['page']}, Section: {chunk['section']}",
                "access_policy": meta["access_policy"],
            })

        # Add to collection
        if ids:
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

        # Update MySQL reports status and ingestion_run
        db.execute(
            text(
                "UPDATE reports SET ingestion_status = 'ingested' WHERE report_id = :report_id"
            ),
            {"report_id": report_id},
        )
        db.execute(
            text(
                "UPDATE ingestion_runs SET status = 'completed', completed_at = :completed_at "
                "WHERE run_id = :run_id"
            ),
            {"run_id": run_id, "completed_at": datetime.now(timezone.utc)},
        )
        db.commit()

        logger.info(f"Report {report_id} successfully ingested ({len(chunks)} chunks).")
        return {
            "report_id": report_id,
            "status": "success",
            "chunks_count": len(chunks),
            "run_id": run_id,
        }
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to ingest report {report_id}: {exc}")
        try:
            db.execute(
                text(
                    "UPDATE ingestion_runs SET status = 'failed', error_message = :err, completed_at = :now "
                    "WHERE run_id = :run_id"
                ),
                {"run_id": run_id, "err": str(exc)[:255], "now": datetime.now(timezone.utc)},
            )
            db.commit()
        except Exception:
            pass
        return {
            "report_id": report_id,
            "status": "failed",
            "error": str(exc),
            "run_id": run_id,
        }
    finally:
        db.close()


def ingest_all_reports(reports_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Ingest all reports from the specified directory."""
    if reports_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        reports_dir = base_dir / "reports"

    results = []
    report_files = sorted(list(reports_dir.glob("*.md")) + list(reports_dir.glob("*.txt")))
    logger.info(f"Found {len(report_files)} report files to ingest in {reports_dir}")

    for file_path in report_files:
        res = ingest_report(file_path)
        results.append(res)

    return results
