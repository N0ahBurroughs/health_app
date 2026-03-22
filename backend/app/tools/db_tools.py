from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import HealthMetric
from ..personalization import compute_baselines


def get_recent_metrics(db: Session, user_id: str, days: int = 7) -> list[HealthMetric]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user_id)
        .filter(HealthMetric.timestamp >= cutoff)
        .order_by(HealthMetric.timestamp.desc())
        .all()
    )


def get_baselines(db: Session, user_id: str):
    baselines = compute_baselines(db, user_id)
    if baselines is None:
        return {
            "hrv_baseline": 50.0,
            "sleep_baseline": 7.0,
            "resting_hr_baseline": 60.0,
        }
    return {
        "hrv_baseline": baselines.hrv_baseline,
        "sleep_baseline": baselines.sleep_baseline,
        "resting_hr_baseline": baselines.resting_hr_baseline,
    }
