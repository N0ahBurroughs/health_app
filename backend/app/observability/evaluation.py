from __future__ import annotations


def evaluate_output(output: dict) -> dict:
    # Lightweight evaluation metrics for learning.
    has_summary = bool(output.get("summary"))
    has_recommendations = isinstance(output.get("recommendations"), list)
    return {
        "has_summary": has_summary,
        "has_recommendations": has_recommendations,
        "schema_ok": has_summary and has_recommendations,
    }
