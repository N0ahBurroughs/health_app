from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import HealthInsight, HealthMetric
from .schemas import HealthMetricsIn, HealthInsightsCreate


def create_health_metric(db: Session, payload: HealthMetricsIn) -> HealthMetric:
    record = HealthMetric(
        user_id=payload.user_id,
        timestamp=payload.timestamp,
        heart_rate=payload.heart_rate,
        hrv=payload.hrv,
        sleep_hours=payload.sleep_hours,
        resting_heart_rate=payload.resting_heart_rate,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_latest_metric(db: Session, user_id: str) -> HealthMetric | None:
    return (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user_id)
        .order_by(desc(HealthMetric.timestamp))
        .first()
    )


def get_latest_insight(db: Session, user_id: str) -> HealthInsight | None:
    return (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == user_id)
        .order_by(desc(HealthInsight.timestamp))
        .first()
    )


def get_insight_for_day(db: Session, user_id: str, day: datetime) -> HealthInsight | None:
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == user_id)
        .filter(HealthInsight.timestamp >= start)
        .filter(HealthInsight.timestamp < end)
        .order_by(desc(HealthInsight.timestamp))
        .first()
    )


def create_health_insight(db: Session, payload: HealthInsightsCreate) -> HealthInsight:
    record = HealthInsight(
        user_id=payload.user_id,
        timestamp=payload.timestamp,
        summary=payload.summary,
        recommendations=payload.recommendations,
        workout_intensity_suggestion=payload.workout_intensity_suggestion,
        recovery_score=payload.recovery_score,
        recovery_status=payload.recovery_status,
        deltas=payload.deltas,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
