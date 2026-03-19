from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import Base, engine, get_db
from .google_flash_service import Baselines, GoogleFlashClient, HealthMetrics, Recovery
from .personalization import compute_baselines, compute_deltas
from .recovery import calculate_recovery_score

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health API")


@app.post("/health-data", status_code=201)
def post_health_data(payload: schemas.HealthMetricsIn, db: Session = Depends(get_db)):
    record = crud.create_health_metric(db, payload)
    return {"id": record.id}


@app.get("/health-summary/{user_id}", response_model=schemas.HealthMetricsOut)
def get_health_summary(user_id: str, db: Session = Depends(get_db)):
    record = crud.get_latest_metric(db, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No health data found for user")

    recovery = calculate_recovery_score(
        hrv=record.hrv,
        hrv_baseline=record.hrv or 1.0,
        sleep_hours=record.sleep_hours,
        resting_hr=record.resting_heart_rate,
        resting_hr_baseline=record.resting_heart_rate or 1.0,
    )

    return schemas.HealthMetricsOut(
        user_id=record.user_id,
        timestamp=record.timestamp,
        heart_rate=record.heart_rate,
        hrv=record.hrv,
        sleep_hours=record.sleep_hours,
        resting_heart_rate=record.resting_heart_rate,
        recovery_score=recovery.score,
    )

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_day(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _insight_to_schema(record: models.HealthInsight) -> schemas.HealthInsightsOut:
    deltas = record.deltas or {}
    return schemas.HealthInsightsOut(
        user_id=record.user_id,
        timestamp=record.timestamp,
        summary=record.summary,
        recommendations=list(record.recommendations or []),
        workout_intensity_suggestion=record.workout_intensity_suggestion,
        recovery_score=record.recovery_score,
        recovery_status=record.recovery_status,
        deltas=schemas.BaselineDeltasOut(
            hrv_delta=float(deltas.get("hrv_delta", 0.0)),
            sleep_delta=float(deltas.get("sleep_delta", 0.0)),
            rhr_delta=float(deltas.get("rhr_delta", 0.0)),
        ),
    )


@app.get("/health-insights/{user_id}", response_model=schemas.HealthInsightsOut)
def get_health_insights(user_id: str, db: Session = Depends(get_db)):
    cached = crud.get_insight_for_day(db, user_id, _utc_now())
    if cached is not None:
        return _insight_to_schema(cached)

    record = crud.get_latest_metric(db, user_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No health data found for user")

    baselines = compute_baselines(db, user_id)
    if baselines is None:
        raise HTTPException(status_code=400, detail="Not enough data to compute baselines")

    deltas = compute_deltas(record, baselines)

    recovery = calculate_recovery_score(
        hrv=record.hrv,
        hrv_baseline=baselines.hrv_baseline or record.hrv or 1.0,
        sleep_hours=record.sleep_hours,
        resting_hr=record.resting_heart_rate,
        resting_hr_baseline=baselines.resting_hr_baseline or record.resting_heart_rate or 1.0,
    )

    client = GoogleFlashClient()
    flash_output = client.generate_health_summary(
        metrics=HealthMetrics(
            heart_rate=record.heart_rate,
            hrv=record.hrv,
            sleep_hours=record.sleep_hours,
            resting_heart_rate=record.resting_heart_rate,
        ),
        recovery=Recovery(score=recovery.score, status=recovery.status),
        baselines=Baselines(
            hrv_baseline=baselines.hrv_baseline,
            resting_hr_baseline=baselines.resting_hr_baseline,
            sleep_target_hours=8.0,
        ),
    )

    created = crud.create_health_insight(
        db,
        schemas.HealthInsightsCreate(
            user_id=record.user_id,
            timestamp=record.timestamp,
            summary=flash_output.summary,
            recommendations=flash_output.recommendations,
            workout_intensity_suggestion=flash_output.workout_intensity_suggestion,
            recovery_score=recovery.score,
            recovery_status=recovery.status,
            deltas={
                "hrv_delta": deltas.hrv_delta,
                "sleep_delta": deltas.sleep_delta,
                "rhr_delta": deltas.rhr_delta,
            },
        ),
    )

    return _insight_to_schema(created)


@app.post("/health-insights", response_model=schemas.HealthInsightsOut)
def post_health_insights(payload: schemas.HealthInsightsIn, db: Session = Depends(get_db)):
    day = _normalize_day(payload.timestamp)
    cached = crud.get_insight_for_day(db, payload.user_id, day)
    if cached is not None:
        return _insight_to_schema(cached)

    deltas = schemas.BaselineDeltasOut(
        hrv_delta=payload.metrics.hrv - payload.baselines.hrv_baseline,
        sleep_delta=payload.metrics.sleep_hours - payload.baselines.sleep_baseline,
        rhr_delta=payload.metrics.resting_heart_rate - payload.baselines.resting_hr_baseline,
    )

    recovery = calculate_recovery_score(
        hrv=payload.metrics.hrv,
        hrv_baseline=payload.baselines.hrv_baseline or payload.metrics.hrv or 1.0,
        sleep_hours=payload.metrics.sleep_hours,
        resting_hr=payload.metrics.resting_heart_rate,
        resting_hr_baseline=payload.baselines.resting_hr_baseline or payload.metrics.resting_heart_rate or 1.0,
    )

    client = GoogleFlashClient()
    flash_output = client.generate_health_summary(
        metrics=HealthMetrics(
            heart_rate=payload.metrics.heart_rate,
            hrv=payload.metrics.hrv,
            sleep_hours=payload.metrics.sleep_hours,
            resting_heart_rate=payload.metrics.resting_heart_rate,
        ),
        recovery=Recovery(score=recovery.score, status=recovery.status),
        baselines=Baselines(
            hrv_baseline=payload.baselines.hrv_baseline,
            resting_hr_baseline=payload.baselines.resting_hr_baseline,
            sleep_target_hours=8.0,
        ),
    )

    created = crud.create_health_insight(
        db,
        schemas.HealthInsightsCreate(
            user_id=payload.user_id,
            timestamp=payload.timestamp,
            summary=flash_output.summary,
            recommendations=flash_output.recommendations,
            workout_intensity_suggestion=flash_output.workout_intensity_suggestion,
            recovery_score=recovery.score,
            recovery_status=recovery.status,
            deltas=deltas.model_dump(),
        ),
    )

    return _insight_to_schema(created)
