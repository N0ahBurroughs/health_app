from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import HealthMetric


@dataclass(frozen=True)
class BaselineMetrics:
    hrv_baseline: float
    sleep_baseline: float
    resting_hr_baseline: float


@dataclass(frozen=True)
class BaselineDeltas:
    hrv_delta: float
    sleep_delta: float
    rhr_delta: float


def compute_baselines(db: Session, user_id: str, days: int = 7) -> BaselineMetrics | None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    row = (
        db.query(
            func.avg(HealthMetric.hrv),
            func.avg(HealthMetric.sleep_hours),
            func.avg(HealthMetric.resting_heart_rate),
        )
        .filter(HealthMetric.user_id == user_id)
        .filter(HealthMetric.timestamp >= cutoff)
        .first()
    )

    if not row or all(value is None for value in row):
        return None

    hrv_avg, sleep_avg, rhr_avg = row
    return BaselineMetrics(
        hrv_baseline=float(hrv_avg or 0.0),
        sleep_baseline=float(sleep_avg or 0.0),
        resting_hr_baseline=float(rhr_avg or 0.0),
    )


def compute_deltas(latest: HealthMetric, baselines: BaselineMetrics) -> BaselineDeltas:
    return BaselineDeltas(
        hrv_delta=float(latest.hrv - baselines.hrv_baseline),
        sleep_delta=float(latest.sleep_hours - baselines.sleep_baseline),
        rhr_delta=float(latest.resting_heart_rate - baselines.resting_hr_baseline),
    )
