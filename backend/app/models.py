from sqlalchemy import Column, DateTime, Float, Integer, String, Index, func, JSON
from .db import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    heart_rate = Column(Float, nullable=False)
    hrv = Column(Float, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    resting_heart_rate = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("ix_health_metrics_user_time", HealthMetric.user_id, HealthMetric.timestamp.desc())


class HealthInsight(Base):
    __tablename__ = "health_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    summary = Column(String, nullable=False)
    recommendations = Column(JSON, nullable=False)
    workout_intensity_suggestion = Column(String, nullable=False)

    recovery_score = Column(Float, nullable=False)
    recovery_status = Column(String, nullable=False)

    deltas = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("ix_health_insights_user_time", HealthInsight.user_id, HealthInsight.timestamp.desc())
