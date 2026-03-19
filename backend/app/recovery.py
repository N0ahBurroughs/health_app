from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryResult:
    score: float
    status: str


def calculate_recovery_score(
    hrv: float,
    hrv_baseline: float,
    sleep_hours: float,
    resting_hr: float,
    resting_hr_baseline: float,
) -> RecoveryResult:
    if hrv_baseline <= 0:
        raise ValueError("hrv_baseline must be > 0")
    if resting_hr_baseline <= 0:
        raise ValueError("resting_hr_baseline must be > 0")

    hrv_ratio = hrv / hrv_baseline
    sleep_ratio = sleep_hours / 8.0
    resting_hr_ratio = resting_hr / resting_hr_baseline

    hrv_score = _clamp(hrv_ratio, 0.0, 1.2) / 1.2
    sleep_score = _clamp(sleep_ratio, 0.0, 1.0)
    resting_penalty = _clamp(resting_hr_ratio - 1.0, 0.0, 0.5) / 0.5

    score = (0.5 * hrv_score) + (0.35 * sleep_score) + (0.15 * (1.0 - resting_penalty))
    score = _clamp(score, 0.0, 1.0) * 100.0

    status = _status_for_score(score)
    return RecoveryResult(score=round(score, 1), status=status)


def _status_for_score(score: float) -> str:
    if score > 70.0:
        return "green"
    if score >= 40.0:
        return "yellow"
    return "red"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(min(value, maximum), minimum)
