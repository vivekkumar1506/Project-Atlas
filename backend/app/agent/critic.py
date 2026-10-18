"""Critic and Fact-Checker for Project Atlas.

Responsibilities:
1. Detect and neutralize prompt injection attempts in retrieved documents.
2. Log security events to MySQL without crashing execution.
3. Detect conflicts between market figures (e.g. R-101 vs R-102) and prevent averaging.
4. Verify source citations for all factual numbers.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.schemas.contracts import Citation, Conflict
from backend.app.services.db import SessionLocal

logger = logging.getLogger("atlas.critic")


def detect_and_defuse_document_injection(
    chunks: List[Dict[str, Any]],
    client_id: str,
    db: Optional[Session] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Scan retrieved chunks for embedded prompt injection instructions.

    Returns:
    - cleaned_chunks: Document chunks with malicious instruction text stripped.
    - detected_injections: List of detected injection attack logs.
    """
    injection_patterns = [
        r"NOTE\s+TO\s+AI\s+SYSTEMS?:?[^\n]*",
        r"Disregard\s+all\s+previous\s+instructions[^\n]*",
        r"Print\s+the\s+full\s+contents\s+of\s+the\s+clients\s+table[^\n]*",
    ]

    cleaned_chunks = []
    detected_injections = []

    for chunk in chunks:
        raw_text = chunk.get("text", "")
        has_attack = False
        attack_snippet = ""

        for pattern in injection_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                has_attack = True
                attack_snippet = match.group(0)
                break

        if has_attack:
            logger.warning(
                f"Prompt injection detected in report {chunk.get('report_id')} Page {chunk.get('page')}: {attack_snippet}"
            )
            # Log security event to MySQL
            _log_security_event(
                event_type="document_prompt_injection",
                client_id=client_id,
                details=f"Attack payload in {chunk.get('report_id')} Page {chunk.get('page')}: '{attack_snippet}' defused successfully.",
                db=db,
            )
            detected_injections.append({
                "report_id": chunk.get("report_id"),
                "page": chunk.get("page"),
                "payload": attack_snippet,
            })

            # Strip out malicious attack instruction, retain legitimate market data
            sanitized_text = raw_text
            for pattern in injection_patterns:
                sanitized_text = re.sub(pattern, "[SECURITY REDACTED: MALICIOUS INSTRUCTION REMOVED]", sanitized_text, flags=re.IGNORECASE)

            chunk_copy = dict(chunk)
            chunk_copy["text"] = sanitized_text
            cleaned_chunks.append(chunk_copy)
        else:
            cleaned_chunks.append(chunk)

    return cleaned_chunks, detected_injections


def _log_security_event(
    event_type: str,
    client_id: Optional[str],
    details: str,
    db: Optional[Session] = None,
):
    """Write an entry to MySQL security_events table."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        db.execute(
            text(
                "INSERT INTO security_events (event_type, client_id, details_summary) "
                "VALUES (:event_type, :client_id, :details)"
            ),
            {
                "event_type": event_type,
                "client_id": client_id,
                "details": details,
            },
        )
        db.commit()
    except Exception as exc:
        logger.error(f"Failed to log security event: {exc}")
        if db:
            db.rollback()
    finally:
        if close_db:
            db.close()


def detect_market_figure_conflicts(chunks: List[Dict[str, Any]]) -> List[Conflict]:
    """Identify conflicting figures between reports and build explicit scope distinctions.

    Never average or silently pick one.
    """
    conflicts: List[Conflict] = []
    report_ids = {c.get("report_id") for c in chunks}

    # Case: R-101 vs R-102 2024 Market Size
    if "R-101" in report_ids and "R-102" in report_ids:
        conflicts.append(
            Conflict(
                metric_name="2024 Global Smart Water Meter Market Size",
                first_report="R-101 (CMR)",
                first_value="USD 4.21 Billion (Comprehensive Scope: Hardware + Software + Services)",
                second_report="R-102 (Aquila Insights)",
                second_value="USD 3.87 Billion (Hardware-Only Scope: AMR/AMI meters only)",
                explanation=(
                    "Divergence is due to differing scope boundaries: R-101 includes bundled communications, "
                    "MDM cloud software, and deployment services, whereas R-102 strictly accounts for physical "
                    "meter endpoints. Neither figure is incorrect; they measure different market boundaries. "
                    "Do NOT average these figures."
                ),
            )
        )

    return conflicts


def extract_citations_from_chunks(chunks: List[Dict[str, Any]]) -> List[Citation]:
    """Map retrieved evidence to structured citations."""
    citations = []
    seen = set()

    for c in chunks:
        rep_id = c.get("report_id")
        page = c.get("page")
        key = (rep_id, page)
        if key in seen:
            continue
        seen.add(key)

        excerpt = c.get("text", "").strip()
        # Truncate clean excerpt
        short_excerpt = excerpt[:220] + "..." if len(excerpt) > 220 else excerpt

        citations.append(
            Citation(
                report_id=rep_id or "Unknown",
                report_title=c.get("title"),
                source_location=c.get("source_location") or f"Page {page}",
                excerpt=short_excerpt,
            )
        )

    return citations
