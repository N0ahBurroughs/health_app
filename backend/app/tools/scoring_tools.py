from __future__ import annotations

from ..recovery import calculate_recovery_score


def compute_recovery(metrics, baselines):
    result = calculate_recovery_score(
        hrv=metrics.hrv,
        hrv_baseline=baselines["hrv_baseline"],
        sleep_hours=metrics.sleep_hours,
        resting_hr=metrics.resting_heart_rate,
        resting_hr_baseline=baselines["resting_hr_baseline"],
    )
    return {"score": result.score, "status": result.status}


def readiness_score(metrics, baselines):
    recovery = compute_recovery(metrics, baselines)
    score = recovery["score"]
    if score >= 75:
        readiness = "high"
    elif score >= 45:
        readiness = "moderate"
    else:
        readiness = "low"
    return {"readiness": readiness, "score": score}


def baseline_delta_calc(metrics, baselines):
    return {
        "hrv_delta": float(metrics.hrv - baselines["hrv_baseline"]),
        "sleep_delta": float(metrics.sleep_hours - baselines["sleep_baseline"]),
        "rhr_delta": float(metrics.resting_heart_rate - baselines["resting_hr_baseline"]),
    }
