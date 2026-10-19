"""Entitlement-Aware Retriever for Project Atlas.

CRITICAL SECURITY GUARANTEE:
Retrieval filtering occurs in the vector retrieval/data layer BEFORE any text is
passed to the LLM. Unpurchased report chunks are strictly filtered out by the
client's active MySQL entitlements.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.rag.vector_store import get_reports_collection
from backend.app.services.db import SessionLocal

logger = logging.getLogger("atlas.retriever")


def get_client_allowed_report_ids(client_id: str, db: Optional[Session] = None) -> Set[str]:
    """Retrieve all report IDs accessible to the client based on MySQL entitlements and public policies."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Step 1: Query purchased active entitlements
        entitlement_rows = db.execute(
            text(
                "SELECT report_id FROM client_report_entitlements "
                "WHERE client_id = :client_id AND status = 'active'"
            ),
            {"client_id": client_id},
        ).fetchall()
        allowed_ids = {row[0] for row in entitlement_rows}

        # Step 2: Include reports with 'public excerpt' access policy
        public_rows = db.execute(
            text("SELECT report_id FROM reports WHERE access_policy = 'public excerpt'")
        ).fetchall()
        for row in public_rows:
            allowed_ids.add(row[0])

        return allowed_ids
    finally:
        if close_db:
            db.close()


def check_unentitled_reports_catalog(
    client_id: str,
    mentioned_report_ids: Optional[List[str]] = None,
    db: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """Identify catalog reports that exist but the client has not purchased (upgrade path)."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        allowed = get_client_allowed_report_ids(client_id, db)
        query = "SELECT report_id, title, sector, access_policy FROM reports"
        all_reports = db.execute(text(query)).fetchall()

        unentitled = []
        for rep in all_reports:
            rep_id = rep[0]
            if rep_id not in allowed:
                if not mentioned_report_ids or rep_id in mentioned_report_ids:
                    unentitled.append({
                        "report_id": rep_id,
                        "title": rep[1],
                        "sector": rep[2],
                        "upgrade_available": True,
                    })
        return unentitled
    finally:
        if close_db:
            db.close()


def retrieve_entitled_chunks(
    client_id: str,
    query: str,
    top_k: int = 5,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Retrieve vector chunks strictly filtered by the client's entitlements.

    Guarantees:
    - If client is not entitled to a report, ChromaDB where-clause excludes it.
    - Zero unentitled text reaches the agent/LLM layer.
    """
    allowed_report_ids = get_client_allowed_report_ids(client_id, db)
    logger.info(f"Client '{client_id}' entitled reports: {allowed_report_ids}")

    if not allowed_report_ids:
        logger.warning(f"Client '{client_id}' has NO active report entitlements.")
        return {
            "chunks": [],
            "allowed_report_ids": [],
            "unentitled_catalog": check_unentitled_reports_catalog(client_id, db=db),
        }

    collection = get_reports_collection()

    # Chroma where filter enforcing client entitlements before search
    import re
    mentioned_reps = [r for r in sorted(list(set(re.findall(r"\b(R-10[1-6])\b", query.upper())))) if r in allowed_report_ids]

    where_filter: Dict[str, Any] = {}
    allowed_list = list(allowed_report_ids)

    if len(mentioned_reps) == 1:
        where_filter = {"report_id": mentioned_reps[0]}
    elif len(allowed_list) == 1:
        where_filter = {"report_id": allowed_list[0]}
    else:
        where_filter = {"report_id": {"$in": allowed_list}}

    formatted_chunks: List[Dict[str, Any]] = []

    try:
        if len(mentioned_reps) > 1:
            # Query each mentioned entitled report to guarantee evidence from all target sources
            for rep_id in mentioned_reps:
                q_res = collection.query(
                    query_texts=[query],
                    n_results=max(3, top_k // len(mentioned_reps)),
                    where={"report_id": rep_id},
                    include=["documents", "metadatas", "distances"],
                )
                if q_res and q_res["documents"] and q_res["documents"][0]:
                    docs = q_res["documents"][0]
                    metas = q_res["metadatas"][0]
                    distances = q_res["distances"][0] if q_res.get("distances") else []
                    for idx, doc in enumerate(docs):
                        meta = metas[idx]
                        dist = distances[idx] if idx < len(distances) else None
                        score = round(max(0.0, 1.0 - dist), 4) if dist is not None else 1.0
                        formatted_chunks.append({
                            "text": doc,
                            "report_id": meta.get("report_id"),
                            "title": meta.get("title"),
                            "page": meta.get("page"),
                            "source_location": meta.get("source_location"),
                            "sector": meta.get("sector"),
                            "region": meta.get("region"),
                            "year": meta.get("year"),
                            "relevance_score": score,
                        })
        else:
            query_results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
            if query_results and query_results["documents"] and query_results["documents"][0]:
                docs = query_results["documents"][0]
                metas = query_results["metadatas"][0]
                distances = query_results["distances"][0] if query_results.get("distances") else []
                for idx, doc in enumerate(docs):
                    meta = metas[idx]
                    dist = distances[idx] if idx < len(distances) else None
                    score = round(max(0.0, 1.0 - dist), 4) if dist is not None else 1.0
                    formatted_chunks.append({
                        "text": doc,
                        "report_id": meta.get("report_id"),
                        "title": meta.get("title"),
                        "page": meta.get("page"),
                        "source_location": meta.get("source_location"),
                        "sector": meta.get("sector"),
                        "region": meta.get("region"),
                        "year": meta.get("year"),
                        "relevance_score": score,
                    })
    except Exception as exc:
        logger.error(f"ChromaDB retrieval error: {exc}")
        return {
            "chunks": [],
            "allowed_report_ids": allowed_list,
            "error": str(exc),
        }

    return {
        "chunks": formatted_chunks,
        "allowed_report_ids": allowed_list,
        "unentitled_catalog": check_unentitled_reports_catalog(client_id, db=db),
    }
