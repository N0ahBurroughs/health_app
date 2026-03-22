from __future__ import annotations


def sanitize_user_text(text: str) -> str:
    # Strip obvious prompt injection patterns.
    lowered = text.lower()
    if "ignore previous instructions" in lowered:
        return text.replace("ignore previous instructions", "")
    if "system:" in lowered:
        return text.replace("system:", "")
    return text


def apply_medical_guardrail(summary: str) -> str:
    disclaimer = "This insight is not medical advice. Consult a clinician for health concerns."
    if disclaimer.lower() in summary.lower():
        return summary
    return f"{summary} {disclaimer}"
