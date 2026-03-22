from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import AgentRunRequest, AgentRunResponse, WorkflowRequest
from ..agents.base import AgentContext
from ..tools.factory import build_tool_registry
from .graph import run_task
from .. import crud
from fastapi import HTTPException, Request


router = APIRouter(prefix="/api", tags=["agents"])


def _build_context(db: Session) -> AgentContext:
    registry = build_tool_registry(db)
    return AgentContext(tools=registry.all(), memory={"db": db})

def _serialize_outputs(outputs, final):
    outputs_serialized = {}
    for key, value in outputs.items():
        if hasattr(value, "model_dump"):
            outputs_serialized[key] = value.model_dump()
        else:
            outputs_serialized[key] = value
    if hasattr(final, "model_dump"):
        final_serialized = final.model_dump()
    else:
        final_serialized = final
    return outputs_serialized, final_serialized


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent(payload: AgentRunRequest, db: Session = Depends(get_db)):
    context = _build_context(db)
    outputs, final = run_task(payload.task_type, payload.input, context)

    # Log planner output to memory.
    context.tools["write_memory"](
        payload.input.user_id,
        "agent_summary",
        final.summary,
        {"task_type": payload.task_type},
    )

    outputs_serialized, final_serialized = _serialize_outputs(outputs, final)
    return AgentRunResponse(task_type=payload.task_type, outputs=outputs_serialized, final=final_serialized)


def _session_user(request: Request) -> str:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user["username"]


def _latest_metrics_or_404(db: Session, user_id: str):
    metric = crud.get_latest_metric(db, user_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="No metrics available")
    return metric


@router.post("/workflows/daily-check", response_model=AgentRunResponse)
def daily_check(payload: WorkflowRequest, db: Session = Depends(get_db)):
    request = AgentRunRequest(
        task_type="daily_check",
        input={
            "user_id": payload.user_id,
            "timestamp": payload.timestamp,
            "metrics": payload.metrics,
        },
    )
    return run_agent(request, db)


@router.post("/workflows/training-reco", response_model=AgentRunResponse)
def training_reco(payload: WorkflowRequest, db: Session = Depends(get_db)):
    request = AgentRunRequest(
        task_type="training_reco",
        input={
            "user_id": payload.user_id,
            "timestamp": payload.timestamp,
            "metrics": payload.metrics,
        },
    )
    return run_agent(request, db)


@router.post("/workflows/anomaly-alert", response_model=AgentRunResponse)
def anomaly_alert(payload: WorkflowRequest, db: Session = Depends(get_db)):
    request = AgentRunRequest(
        task_type="anomaly_alert",
        input={
            "user_id": payload.user_id,
            "timestamp": payload.timestamp,
            "metrics": payload.metrics,
        },
    )
    return run_agent(request, db)


@router.get("/features/daily-check", response_model=AgentRunResponse)
def daily_check_feature(request: Request, db: Session = Depends(get_db)):
    user_id = _session_user(request)
    metric = _latest_metrics_or_404(db, user_id)
    payload = AgentRunRequest(
        task_type="daily_check",
        input={
            "user_id": user_id,
            "timestamp": metric.timestamp,
            "metrics": {
                "heart_rate": metric.heart_rate,
                "hrv": metric.hrv,
                "sleep_hours": metric.sleep_hours,
                "resting_heart_rate": metric.resting_heart_rate,
            },
        },
    )
    return run_agent(payload, db)


@router.get("/features/training-reco", response_model=AgentRunResponse)
def training_feature(request: Request, db: Session = Depends(get_db)):
    user_id = _session_user(request)
    metric = _latest_metrics_or_404(db, user_id)
    payload = AgentRunRequest(
        task_type="training_reco",
        input={
            "user_id": user_id,
            "timestamp": metric.timestamp,
            "metrics": {
                "heart_rate": metric.heart_rate,
                "hrv": metric.hrv,
                "sleep_hours": metric.sleep_hours,
                "resting_heart_rate": metric.resting_heart_rate,
            },
        },
    )
    return run_agent(payload, db)


@router.get("/features/anomaly-alert", response_model=AgentRunResponse)
def anomaly_feature(request: Request, db: Session = Depends(get_db)):
    user_id = _session_user(request)
    metric = _latest_metrics_or_404(db, user_id)
    payload = AgentRunRequest(
        task_type="anomaly_alert",
        input={
            "user_id": user_id,
            "timestamp": metric.timestamp,
            "metrics": {
                "heart_rate": metric.heart_rate,
                "hrv": metric.hrv,
                "sleep_hours": metric.sleep_hours,
                "resting_heart_rate": metric.resting_heart_rate,
            },
        },
    )
    return run_agent(payload, db)
