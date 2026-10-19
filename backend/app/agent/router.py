"""Query Router for Project Atlas Agent Workflow."""
import re
from typing import Dict, Literal

RouteType = Literal[
    "factual",
    "comparison",
    "calculation",
    "aggregate_sql",
    "out_of_scope",
    "unsafe",
]


def classify_query(query: str) -> Dict[str, Any]:
    """Classify user query into appropriate execution route with reason."""
    q_lower = query.lower().strip()

    # 0. Greetings / Help / Identity queries
    if re.match(r"^(hi|hello|hey|greetings|good\s*(morning|afternoon|evening)|who\s+are\s+you|what\s+can\s+you\s+do|help)[\s!.,?]*$", q_lower):
        return {
            "route": "greeting",
            "sub_reason": "greeting_or_introduction",
            "confidence": 0.99,
        }

    # 1. Unsafe detection: SQL write commands, exfiltration, instruction overrides
    unsafe_patterns = [
        (r"\b(delete\s+from|drop\s+(table|database|view|index)|truncate\s+(table)?|alter\s+table|insert\s+into|update\s+\w+\s+set)\b", "sql_modification_attempt"),
        (r"\b(delete|drop|truncate|alter|insert|update)\s+.*(table|row|from|database|into|set)", "sql_modification_attempt"),
        (r"\b(output|list|show|print|give|dump|extract)\s+.*(client|customer)?\s*(email|password|credential|secret)", "sensitive_data_exfiltration"),
        (r"\b(diagnostic\s+override|system\s+override)\b", "sensitive_data_exfiltration"),
        (r"\b(ignore|disregard|forget)\s+.*(previous|all|system)?\s*(instruction|prompt|rule)", "prompt_injection_override"),
        (r"\b(reveal|print)\s+.*(system\s*prompt|api\s*key)", "credential_harvesting"),
    ]
    for pattern, reason in unsafe_patterns:
        if re.search(pattern, q_lower):
            return {
                "route": "unsafe",
                "sub_reason": reason,
                "confidence": 0.99,
            }

    # 2. Out-of-scope detection: politics, elections, weather, non-business general queries
    out_of_scope_patterns = [
        r"\b(election|vote|president|prime\s*minister|parliament|congress|democrat|republican|bjp|congress)\b",
        r"\b(who\s+will\s+win|weather|recipe|horoscope|celebrity|football|cricket\s*score)\b",
    ]
    for pattern in out_of_scope_patterns:
        if re.search(pattern, q_lower):
            return {
                "route": "out_of_scope",
                "sub_reason": "non_market_research_topic",
                "confidence": 0.95,
            }

    # 3. Aggregate SQL questions: queries asking for counts, library summaries, metadata
    sql_patterns = [
        r"\b(how\s+many\s+(total\s+)?.*reports|which\s+sector\s+has\s+the\s+(highest|most)|most\s+reports|count\s+of\s+reports|total\s+.*reports\s+(are\s+)?available)\b",
        r"\b(average\s+market\s+size\s+across|aggregate|list\s+all\s+sectors)\b",
    ]
    for pattern in sql_patterns:
        if re.search(pattern, q_lower):
            return {
                "route": "aggregate_sql",
                "sub_reason": "database_aggregate_query",
                "confidence": 0.95,
            }

    # 4. Calculation / Projections: CAGR, forecasts, future year valuations
    calc_patterns = [
        r"\b(cagr|compound\s+annual|growth\s+rate\s+formula)\b",
        r"\b(what\s+will\s+the\s+.*market\s+be\s+worth\s+in\s+203\d|project\s+.*to\s+203\d|forecast\s+.*203\d)\b",
        r"\b(estimate\s+.*203\d|calculate)\b",
    ]
    for pattern in calc_patterns:
        if re.search(pattern, q_lower):
            return {
                "route": "calculation",
                "sub_reason": "projection_or_cagr_calculation",
                "confidence": 0.92,
            }

    # 5. Comparison & Conflicts: trust, compare, difference, conflict
    compare_patterns = [
        r"\b(compare|difference|discrepancy|which\s+report\s+should\s+i\s+trust|conflict|versus|vs\.?)\b",
    ]
    for pattern in compare_patterns:
        if re.search(pattern, q_lower):
            return {
                "route": "comparison",
                "sub_reason": "cross_report_reconciliation",
                "confidence": 0.90,
            }

    # 6. Default to Factual lookup
    return {
        "route": "factual",
        "sub_reason": "knowledge_retrieval",
        "confidence": 0.88,
    }
