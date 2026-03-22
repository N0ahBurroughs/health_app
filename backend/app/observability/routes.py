from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AgentRun, MemoryChunk


router = APIRouter(prefix="/api", tags=["observability"])


@router.get("/agent-runs")
def list_agent_runs(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(AgentRun)
        .filter(AgentRun.user_id == user_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "run_id": row.run_id,
            "user_id": row.user_id,
            "agent_name": row.agent_name,
            "prompt": row.prompt,
            "output": row.output,
            "latency_ms": row.latency_ms,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/memory")
def list_memory(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(MemoryChunk)
        .filter(MemoryChunk.user_id == user_id)
        .order_by(MemoryChunk.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "type": row.memory_type,
            "content": row.content,
            "metadata": row.metadata,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
