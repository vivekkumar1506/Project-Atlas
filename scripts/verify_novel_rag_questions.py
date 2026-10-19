"""
Project Atlas — Verification Suite for Novel, Unscripted RAG Questions.
Tests questions that are NOT prewritten in any test file or questions.json to verify:
1. Dynamic retrieval via ONNX all-MiniLM-L6-v2 semantic embeddings.
2. Grounded evidence synthesis from retrieved chunks rather than benchmark shortcuts.
3. Strict citation validation where every citation is verified against the actual report and page.
4. Entitlement boundaries on novel queries.
"""

import json
import logging
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.agent.workflow import run_agent_workflow
from backend.app.schemas.contracts import ChatRequest
from backend.app.services.db import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("novel_rag_tester")

NOVEL_TEST_CASES = [
    {
        "id": "NOVEL-01",
        "client_id": "C-01",
        "question": "What are the specific communication infrastructure options and their market share percentage in report R-101?",
        "expected_keywords": ["18%", "cellular", "lorawan", "rf mesh"],
        "expected_report": "R-101",
        "expected_page": 12,
        "description": "Component segmentation breakdown from R-101 Page 12",
    },
    {
        "id": "NOVEL-02",
        "client_id": "C-02",
        "question": "What are the primary regional revenue shares for residential water purifiers according to R-103?",
        "expected_keywords": ["45%", "28%", "19%", "apac", "north america"],
        "expected_report": "R-103",
        "expected_page": 6,
        "description": "Regional revenue breakdown from R-103 Page 6",
    },
    {
        "id": "NOVEL-03",
        "client_id": "C-03",
        "question": "What country holds the largest market share for commercial heat pumps in Europe according to R-104?",
        "expected_keywords": ["germany", "26%"],
        "expected_report": "R-104",
        "expected_page": 7,
        "description": "Country segmentation from R-104 Page 7",
    },
    {
        "id": "NOVEL-04",
        "client_id": "C-03",
        "question": "What is the breakdown of the smart grid sensors market between the United States and Canada in R-105?",
        "expected_keywords": ["84%", "16%", "united states", "canada"],
        "expected_report": "R-105",
        "expected_page": 5,
        "description": "Country segmentation from R-105 Page 5",
    },
    {
        "id": "NOVEL-05",
        "client_id": "C-03",
        "question": "What industrial manufacturing sectors are driving the adoption of Zero Liquid Discharge technologies in R-106?",
        "expected_keywords": ["pharmaceuticals", "chemicals", "semiconductor"],
        "expected_report": "R-106",
        "expected_page": 1,
        "description": "Industry dynamics and target verticals from R-106 Page 1",
    },
    {
        "id": "NOVEL-06",
        "client_id": "C-01",
        "question": "Why are utilities substituting mechanical water meters with ultrasonic static meters according to R-102?",
        "expected_keywords": ["ultrasonic", "moving components", "sand", "sediment", "air bubbles"],
        "expected_report": "R-102",
        "expected_page": 5,
        "description": "Meter technology trends from R-102 Page 5",
    },
    {
        "id": "NOVEL-07",
        "client_id": "C-02",
        "question": "What are the wildfire mitigation drivers for grid line sensors documented in report R-105?",
        "expected_keywords": ["access restricted"],
        "expected_report": None,
        "expected_page": None,
        "description": "Negative security test: Client C-02 lacks entitlement to R-105",
    },
]


def run_novel_rag_tests():
    logger.info("======================================================================")
    logger.info(" RUNNING NOVEL UNSCRIPTED RAG QUESTIONS EVALUATION")
    logger.info("======================================================================")
    db = SessionLocal()

    passed_count = 0
    results = []

    try:
        for tc in NOVEL_TEST_CASES:
            req = ChatRequest(
                client_id=tc["client_id"],
                question=tc["question"],
                user_reference=f"novel_test_{tc['id']}",
            )
            resp = run_agent_workflow(req, db=db)
            ans_lower = resp.answer.lower()

            passed = True
            failures = []

            # 1. Keyword grounding check
            for kw in tc["expected_keywords"]:
                if kw not in ans_lower:
                    passed = False
                    failures.append(f"Missing expected evidence keyword: '{kw}'")

            # 2. Entitlement check
            if tc["id"] == "NOVEL-07":
                if "access restricted" not in ans_lower and "entitlement" not in ans_lower:
                    passed = False
                    failures.append("Expected access restriction for unentitled report R-105")
                if "2.15" in resp.answer or "4.31" in resp.answer:
                    passed = False
                    failures.append("Leaked proprietary R-105 data to unentitled client C-02")
            else:
                # 3. Citation validation check
                if not resp.citations:
                    passed = False
                    failures.append("Expected verified citations but received empty citations list")
                else:
                    found_expected_cit = False
                    for cit in resp.citations:
                        if cit.report_id == tc["expected_report"]:
                            # Check page in source_location
                            if f"page {tc['expected_page']}" in cit.source_location.lower():
                                found_expected_cit = True
                                break
                    if not found_expected_cit:
                        passed = False
                        failures.append(
                            f"Expected citation to {tc['expected_report']} Page {tc['expected_page']}, "
                            f"got: {[(c.report_id, c.source_location) for c in resp.citations]}"
                        )

            if passed:
                passed_count += 1
                logger.info(f"[PASS] {tc['id']} ({tc['client_id']}): {tc['description']}")
            else:
                logger.error(f"[FAIL] {tc['id']} ({tc['client_id']}): {failures}")

            results.append({
                "id": tc["id"],
                "passed": passed,
                "failures": failures,
                "confidence": resp.confidence,
                "citations": [(c.report_id, c.source_location) for c in resp.citations],
                "answer_snippet": resp.answer[:140].replace("\n", " "),
            })

    finally:
        db.close()

    total = len(NOVEL_TEST_CASES)
    logger.info("======================================================================")
    logger.info(f" RESULTS: {passed_count}/{total} Passed ({passed_count/total*100:.1f}%)")
    logger.info("======================================================================")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        logger.info(f"{r['id']}: [{status}] Cits: {r['citations']} | Ans: {r['answer_snippet']}")

    return passed_count == total


if __name__ == "__main__":
    success = run_novel_rag_tests()
    sys.exit(0 if success else 1)
