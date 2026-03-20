from sqlalchemy import Column, DateTime, Float, Integer, String, Index, func, JSON, UniqueConstraint, Boolean
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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


Index("ix_refresh_tokens_user", RefreshToken.user_id)
