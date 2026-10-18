"""
Project Atlas — Seed 25 Benchmark Evaluation Questions into MySQL.
Populates the `qa_benchmarks` table from evaluation/questions.json.
Safe to rerun: uses INSERT ... ON DUPLICATE KEY UPDATE.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from backend.app.services.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_questions")

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "evaluation" / "questions.json"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `qa_benchmarks` (
    `qa_id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `category` VARCHAR(50) NOT NULL,
    `question` TEXT NOT NULL,
    `expected_route` VARCHAR(50) NOT NULL,
    `target_reports` JSON NULL,
    `expected_citations` JSON NULL,
    `expected_answer` TEXT NOT NULL,
    `conflicts` JSON NULL,
    `derived_values` JSON NULL,
    `expected_escalated` TINYINT(1) NOT NULL DEFAULT 0,
    `evaluation_criteria` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_qa_category` (`category`),
    INDEX `idx_qa_route` (`expected_route`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def seed_questions():
    if not QUESTIONS_FILE.exists():
        logger.error(f"Questions file not found at: {QUESTIONS_FILE}")
        return False

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    logger.info(f"Loaded {len(questions)} evaluation questions from {QUESTIONS_FILE.name}")

    with engine.begin() as conn:
        # 1. Ensure table exists
        conn.execute(text(CREATE_TABLE_SQL))
        logger.info("Table `qa_benchmarks` verified/created in MySQL.")

        # 2. Seed questions
        upsert_sql = text("""
            INSERT INTO qa_benchmarks (
                qa_id, category, question, expected_route, target_reports,
                expected_citations, expected_answer, conflicts, derived_values,
                expected_escalated, evaluation_criteria
            ) VALUES (
                :qa_id, :category, :question, :expected_route, :target_reports,
                :expected_citations, :expected_answer, :conflicts, :derived_values,
                :expected_escalated, :evaluation_criteria
            ) ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                question = VALUES(question),
                expected_route = VALUES(expected_route),
                target_reports = VALUES(target_reports),
                expected_citations = VALUES(expected_citations),
                expected_answer = VALUES(expected_answer),
                conflicts = VALUES(conflicts),
                derived_values = VALUES(derived_values),
                expected_escalated = VALUES(expected_escalated),
                evaluation_criteria = VALUES(evaluation_criteria);
        """)

        inserted = 0
        for q in questions:
            conn.execute(
                upsert_sql,
                {
                    "qa_id": q["id"],
                    "category": q["category"],
                    "question": q["question"],
                    "expected_route": q["expected_route"],
                    "target_reports": json.dumps(q.get("target_reports", [])),
                    "expected_citations": json.dumps(q.get("expected_citations", [])),
                    "expected_answer": q["expected_answer"],
                    "conflicts": json.dumps(q.get("conflicts", [])),
                    "derived_values": json.dumps(q.get("derived_values", [])),
                    "expected_escalated": 1 if q.get("expected_escalated") else 0,
                    "evaluation_criteria": q.get("evaluation_criteria", ""),
                },
            )
            inserted += 1

        logger.info(f"Successfully seeded {inserted} questions into MySQL `qa_benchmarks`.")
    return True


if __name__ == "__main__":
    seed_questions()
