from datetime import datetime
from pydantic import BaseModel, Field


class HealthMetricsIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    timestamp: datetime
    heart_rate: float
    hrv: float
    sleep_hours: float
    resting_heart_rate: float


class HealthMetricsPayload(BaseModel):
    heart_rate: float
    hrv: float
    sleep_hours: float
    resting_heart_rate: float


class HealthMetricsWebIn(BaseModel):
    timestamp: datetime
    heart_rate: float
    hrv: float
    sleep_hours: float
    resting_heart_rate: float


class BaselinesPayload(BaseModel):
    hrv_baseline: float
    sleep_baseline: float
    resting_hr_baseline: float


class HealthMetricsOut(BaseModel):
    user_id: str
    timestamp: datetime
    heart_rate: float
    hrv: float
    sleep_hours: float
    resting_heart_rate: float
    recovery_score: float

    class Config:
        from_attributes = True


class BaselineDeltasOut(BaseModel):
    hrv_delta: float
    sleep_delta: float
    rhr_delta: float


class HealthInsightsOut(BaseModel):
    user_id: str
    timestamp: datetime
    summary: str
    recommendations: list[str]
    workout_intensity_suggestion: str
    recovery_score: float
    recovery_status: str
    deltas: BaselineDeltasOut


class HealthInsightsIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    timestamp: datetime
    metrics: HealthMetricsPayload
    baselines: BaselinesPayload


class HealthInsightsCreate(BaseModel):
    user_id: str
    timestamp: datetime
    summary: str
    recommendations: list[str]
    workout_intensity_suggestion: str
    recovery_score: float
    recovery_status: str
    deltas: dict


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
