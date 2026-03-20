from datetime import datetime, timezone
import os

from fastapi import Depends, FastAPI, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import Base, engine, get_db
from .auth import hash_password, verify_password
from .google_flash_service import Baselines, GoogleFlashClient, HealthMetrics, Recovery
from .personalization import compute_baselines, compute_deltas
from .recovery import calculate_recovery_score
from .token_auth import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_access_token,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Health API")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"))
templates = Jinja2Templates(directory="/Users/noahburroughs/Desktop/AI POC/health_app/backend/app/templates")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if _get_session_user(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Log in",
            "action": "/login",
            "button_label": "Log in",
            "switch_url": "/signup",
            "switch_label": "Create an account",
            "error": None,
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, username)
    try:
        password_ok = user is not None and verify_password(password, user.password_hash)
    except ValueError:
        password_ok = False

    if not password_ok:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Log in",
                "action": "/login",
                "button_label": "Log in",
                "switch_url": "/signup",
                "switch_label": "Create an account",
                "error": "Invalid username or password.",
            },
            status_code=400,
        )

    request.session["user"] = {"id": user.id, "username": user.username}
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/api/token", response_model=schemas.TokenResponse)
def api_token(payload: schemas.TokenRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token()
    crud.create_refresh_token(
        db,
        user_id=user.username,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_token_expires_at(),
    )
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(os.getenv("JWT_EXP_MINUTES", "30")) * 60,
    )


@app.post("/api/token/refresh", response_model=schemas.TokenResponse)
def api_refresh_token(payload: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    record = crud.get_refresh_token(db, token_hash)
    if record is None or record.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if record.expires_at <= _utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    crud.revoke_refresh_token(db, token_hash)
    new_refresh = create_refresh_token()
    crud.create_refresh_token(
        db,
        user_id=record.user_id,
        token_hash=hash_refresh_token(new_refresh),
        expires_at=refresh_token_expires_at(),
    )
    access_token = create_access_token(record.user_id)
    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=int(os.getenv("JWT_EXP_MINUTES", "30")) * 60,
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Create account",
            "action": "/signup",
            "button_label": "Sign up",
            "switch_url": "/login",
            "switch_label": "Back to login",
            "error": None,
        },
    )


@app.post("/signup", response_class=HTMLResponse)
def signup_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    password_error = _validate_password(password)
    if password_error:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Create account",
                "action": "/signup",
                "button_label": "Sign up",
                "switch_url": "/login",
                "switch_label": "Back to login",
                "error": password_error,
            },
            status_code=400,
        )

    existing = crud.get_user_by_username(db, username)
    if existing:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Create account",
                "action": "/signup",
                "button_label": "Sign up",
                "switch_url": "/login",
                "switch_label": "Back to login",
                "error": "Username already exists.",
            },
            status_code=400,
        )

    password_hash = hash_password(password)

    user = crud.create_user(db, schemas.UserCreate(username=username, password=password), password_hash)
    request.session["user"] = {"id": user.id, "username": user.username}
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = _require_user(request)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "username": user["username"], "is_admin": user["username"] == ADMIN_USERNAME},
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request)
    if user["username"] != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Forbidden")
    users = crud.list_users(db)
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "users": users},
    )


@app.post("/admin/delete/{username}")
def admin_delete_user(username: str, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request)
    if user["username"] != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Forbidden")
    if username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    crud.delete_user_and_data(db, username)
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/create-user")
def admin_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    if user["username"] != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Forbidden")

    if crud.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="User already exists")

    password_error = _validate_password(password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    password_hash = hash_password(password)
    crud.create_user(db, schemas.UserCreate(username=username, password=password), password_hash)
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/reset-password/{username}")
def admin_reset_password(
    username: str,
    request: Request,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    if user["username"] != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Forbidden")

    password_error = _validate_password(new_password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    record = crud.get_user_by_username(db, username)
    if record is None:
        raise HTTPException(status_code=404, detail="User not found")

    record.password_hash = hash_password(new_password)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/api/health-summary", response_model=schemas.HealthMetricsOut)
def api_health_summary(request: Request, db: Session = Depends(get_db)):
    user = _require_api_user(request)
    record = crud.get_latest_metric(db, user["username"])
    if record is None:
        raise HTTPException(status_code=404, detail="No health data found for user")

    baselines = compute_baselines(db, user["username"])
    hrv_baseline = baselines.hrv_baseline if baselines else (record.hrv or 1.0)
    rhr_baseline = baselines.resting_hr_baseline if baselines else (record.resting_heart_rate or 1.0)

    recovery = calculate_recovery_score(
        hrv=record.hrv,
        hrv_baseline=hrv_baseline or 1.0,
        sleep_hours=record.sleep_hours,
        resting_hr=record.resting_heart_rate,
        resting_hr_baseline=rhr_baseline or 1.0,
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


@app.get("/api/health-insights", response_model=schemas.HealthInsightsOut)
def api_health_insights(request: Request, force: bool = False, db: Session = Depends(get_db)):
    user = _require_api_user(request)
    if not force:
        cached = crud.get_insight_for_day(db, user["username"], _utc_now())
        if cached is not None:
            return _insight_to_schema(cached)

    record = crud.get_latest_metric(db, user["username"])
    if record is None:
        raise HTTPException(status_code=404, detail="No health data found for user")

    baselines = compute_baselines(db, user["username"])
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


@app.get("/api/health-trends")
def api_health_trends(request: Request, db: Session = Depends(get_db)):
    user = _require_api_user(request)
    records = crud.get_recent_metrics(db, user["username"], limit=7)
    if not records:
        return JSONResponse(
            {
                "heart_rate": [],
                "hrv": [],
                "sleep_hours": [],
                "resting_heart_rate": [],
            }
        )
    return JSONResponse(
        {
            "heart_rate": [r.heart_rate for r in records],
            "hrv": [r.hrv for r in records],
            "sleep_hours": [r.sleep_hours for r in records],
            "resting_heart_rate": [r.resting_heart_rate for r in records],
        }
    )


@app.post("/api/health-data", status_code=201)
def api_health_data(payload: schemas.HealthMetricsWebIn, request: Request, db: Session = Depends(get_db)):
    user = _require_api_user(request)
    record = crud.create_health_metric(
        db,
        schemas.HealthMetricsIn(
            user_id=user["username"],
            timestamp=payload.timestamp,
            heart_rate=payload.heart_rate,
            hrv=payload.hrv,
            sleep_hours=payload.sleep_hours,
            resting_heart_rate=payload.resting_heart_rate,
        ),
    )
    return {"id": record.id}


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


def _validate_password(password: str) -> str | None:
    if len(password) < 6:
        return "Password must be at least 6 characters."
    if len(password.encode("utf-8")) > 72:
        return "Password must be 72 bytes or fewer."
    return None


def _get_session_user(request: Request) -> dict | None:
    return request.session.get("user")


def _get_token_user(request: Request) -> dict | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    subject = verify_access_token(token)
    if not subject:
        return None
    return {"username": subject}


def _require_user(request: Request) -> dict:
    user = _get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def _require_api_user(request: Request) -> dict:
    user = _get_token_user(request) or _get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


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
def get_health_insights(user_id: str, force: bool = False, db: Session = Depends(get_db)):
    if not force:
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
def post_health_insights(payload: schemas.HealthInsightsIn, force: bool = False, db: Session = Depends(get_db)):
    day = _normalize_day(payload.timestamp)
    if not force:
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
