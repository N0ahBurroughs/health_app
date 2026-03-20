from __future__ import annotations

import os
from dataclasses import dataclass
import json
from typing import Any, Dict, List

import requests


@dataclass(frozen=True)
class HealthMetrics:
    heart_rate: float
    hrv: float
    sleep_hours: float
    resting_heart_rate: float


@dataclass(frozen=True)
class Baselines:
    hrv_baseline: float
    resting_hr_baseline: float
    sleep_target_hours: float = 8.0


@dataclass(frozen=True)
class Recovery:
    score: float
    status: str


@dataclass(frozen=True)
class FlashOutput:
    summary: str
    recommendations: List[str]
    workout_intensity_suggestion: str


class GoogleFlashClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_FLASH_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_FLASH_API_KEY env var")

        # Default to Gemini Flash endpoint; can be overridden by env or init.
        self.base_url = (
            base_url
            or os.getenv("GOOGLE_FLASH_BASE_URL")
            or "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        )

    def generate_health_summary(
        self,
        metrics: HealthMetrics,
        recovery: Recovery,
        baselines: Baselines,
    ) -> FlashOutput:
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": _build_prompt(metrics, recovery, baselines)
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }

        headers = {
            "X-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return _parse_output(data)


def _build_prompt(metrics: HealthMetrics, recovery: Recovery, baselines: Baselines) -> str:
    return (
        "You are a health coach. Return ONLY valid JSON with keys: "
        "summary (string), recommendations (array of strings), "
        "workout_intensity_suggestion (string).\n\n"
        "User data:\n"
        f"- Heart rate: {metrics.heart_rate}\n"
        f"- HRV: {metrics.hrv}\n"
        f"- Sleep hours: {metrics.sleep_hours}\n"
        f"- Resting heart rate: {metrics.resting_heart_rate}\n"
        f"- Recovery score: {recovery.score} ({recovery.status})\n"
        f"- HRV baseline: {baselines.hrv_baseline}\n"
        f"- Resting HR baseline: {baselines.resting_hr_baseline}\n"
        f"- Sleep target hours: {baselines.sleep_target_hours}\n"
    )


def _parse_output(data: Dict[str, Any]) -> FlashOutput:
    # Gemini responses are wrapped in candidates/parts.
    text = ""
    try:
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")
    except Exception:
        text = ""

    # Expect the model to return JSON; fall back to empty structure on failure.
    summary = ""
    recommendations: List[str] = []
    workout = ""
    if text:
        try:
            parsed = json.loads(text)
            summary = str(parsed.get("summary", ""))
            recommendations = parsed.get("recommendations", [])
            workout = str(parsed.get("workout_intensity_suggestion", ""))
        except Exception:
            summary = ""
            recommendations = []
            workout = ""

    if not isinstance(recommendations, list):
        recommendations = [str(recommendations)]

    return FlashOutput(
        summary=str(summary),
        recommendations=[str(item) for item in recommendations],
        workout_intensity_suggestion=str(workout),
    )
