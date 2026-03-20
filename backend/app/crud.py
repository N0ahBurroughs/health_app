from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import HealthInsight, HealthMetric, RefreshToken, User
from .schemas import HealthMetricsIn, HealthInsightsCreate, UserCreate


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


def get_recent_metrics(db: Session, user_id: str, limit: int = 7) -> list[HealthMetric]:
    records = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user_id)
        .order_by(desc(HealthMetric.timestamp))
        .limit(limit)
        .all()
    )
    return list(reversed(records))


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


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, payload: UserCreate, password_hash: str) -> User:
    record = User(username=payload.username, password_hash=password_hash)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username.asc()).all()


def delete_user_and_data(db: Session, username: str) -> None:
    db.query(HealthInsight).filter(HealthInsight.user_id == username).delete()
    db.query(HealthMetric).filter(HealthMetric.user_id == username).delete()
    db.query(RefreshToken).filter(RefreshToken.user_id == username).delete()
    db.query(User).filter(User.username == username).delete()
    db.commit()


def create_refresh_token(db: Session, user_id: str, token_hash: str, expires_at) -> RefreshToken:
    record = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at, revoked=False)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def revoke_refresh_token(db: Session, token_hash: str) -> None:
    db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).update({"revoked": True})
    db.commit()
