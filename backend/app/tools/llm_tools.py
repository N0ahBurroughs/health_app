from __future__ import annotations

from ..google_flash_service import GoogleFlashClient, HealthMetrics, Baselines, Recovery


def generate_coaching_summary(metrics, recovery, baselines):
    try:
        client = GoogleFlashClient()
        output = client.generate_health_summary(
            metrics=HealthMetrics(
                heart_rate=metrics.heart_rate,
                hrv=metrics.hrv,
                sleep_hours=metrics.sleep_hours,
                resting_heart_rate=metrics.resting_heart_rate,
            ),
            recovery=Recovery(score=recovery["score"], status=recovery["status"]),
            baselines=Baselines(
                hrv_baseline=baselines["hrv_baseline"],
                resting_hr_baseline=baselines["resting_hr_baseline"],
                sleep_target_hours=baselines["sleep_baseline"],
            ),
        )
        return {
            "summary": output.summary,
            "recommendations": output.recommendations,
            "workout_intensity_suggestion": output.workout_intensity_suggestion,
        }
    except Exception:
        return {
            "summary": "Light recovery day recommended based on recent trends.",
            "recommendations": ["Prioritize sleep", "Keep hydration steady"],
            "workout_intensity_suggestion": "low",
        }
