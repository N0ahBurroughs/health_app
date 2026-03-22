from __future__ import annotations

import time
import uuid
from sqlalchemy.orm import Session

from ..models import AgentEvent, AgentRun


def start_run(user_id: str, agent_name: str) -> tuple[str, float]:
    run_id = str(uuid.uuid4())
    start = time.time()
    return run_id, start


def end_run(db: Session, run_id: str, user_id: str, agent_name: str, prompt: str, output: dict, start: float):
    latency_ms = int((time.time() - start) * 1000)
    record = AgentRun(
        run_id=run_id,
        user_id=user_id,
        agent_name=agent_name,
        prompt=prompt,
        output=output,
        latency_ms=latency_ms,
    )
    db.add(record)
    db.commit()


def log_event(db: Session, run_id: str, user_id: str, event_type: str, payload: dict):
    record = AgentEvent(
        run_id=run_id,
        user_id=user_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(record)
    db.commit()
