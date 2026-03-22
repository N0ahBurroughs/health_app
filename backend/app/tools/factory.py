from __future__ import annotations

from sqlalchemy.orm import Session

from .tool_registry import ToolRegistry
from .db_tools import get_recent_metrics, get_baselines
from .scoring_tools import compute_recovery, readiness_score, baseline_delta_calc
from .llm_tools import generate_coaching_summary
from .memory_tools import search_memory, write_memory
from ..observability import logger


def build_tool_registry(db: Session) -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        "get_recent_metrics",
        lambda user_id, days=7: get_recent_metrics(db, user_id, days),
        {"name": "get_recent_metrics", "input": {"user_id": "str", "days": "int"}, "output": "list[HealthMetric]"},
    )
    registry.register(
        "get_baselines",
        lambda user_id: get_baselines(db, user_id),
        {"name": "get_baselines", "input": {"user_id": "str"}, "output": "Baselines"},
    )
    registry.register(
        "compute_recovery",
        lambda metrics, baselines: compute_recovery(metrics, baselines),
        {"name": "compute_recovery", "input": {"metrics": "HealthMetrics", "baselines": "Baselines"}, "output": "Recovery"},
    )
    registry.register(
        "readiness_score",
        lambda metrics, baselines: readiness_score(metrics, baselines),
        {"name": "readiness_score", "input": {"metrics": "HealthMetrics", "baselines": "Baselines"}, "output": "Readiness"},
    )
    registry.register(
        "baseline_delta_calc",
        lambda metrics, baselines: baseline_delta_calc(metrics, baselines),
        {"name": "baseline_delta_calc", "input": {"metrics": "HealthMetrics", "baselines": "Baselines"}, "output": "Deltas"},
    )
    registry.register(
        "summarize_trends",
        lambda user_id: {
            "summary": f"Recent trends for {user_id} show steady recovery.",
            "recommendations": ["Maintain consistency", "Avoid late caffeine"],
        },
        {"name": "summarize_trends", "input": {"user_id": "str"}, "output": "Summary"},
    )
    registry.register(
        "training_reco",
        lambda user_id, metrics: {
            "summary": f"Training recommendation for {user_id}: moderate intensity.",
            "recommendations": ["30-45 minutes zone 2", "Mobility work"],
        },
        {"name": "training_reco", "input": {"user_id": "str", "metrics": "HealthMetrics"}, "output": "Training"},
    )
    registry.register(
        "anomaly_scan",
        lambda metrics, baselines: {
            "anomaly": metrics.resting_heart_rate > baselines["resting_hr_baseline"] * 1.2,
            "reason": "Resting HR elevated",
            "severity": "med",
        },
        {"name": "anomaly_scan", "input": {"metrics": "HealthMetrics", "baselines": "Baselines"}, "output": "Anomaly"},
    )
    registry.register(
        "search_memory",
        lambda user_id, query, top_k=5: search_memory(db, user_id, query, top_k),
        {"name": "search_memory", "input": {"user_id": "str", "query": "str", "top_k": "int"}, "output": "list[MemoryChunk]"},
    )
    registry.register(
        "write_memory",
        lambda user_id, memory_type, content, metadata: write_memory(db, user_id, memory_type, content, metadata),
        {"name": "write_memory", "input": {"user_id": "str", "memory_type": "str", "content": "str", "metadata": "dict"}, "output": "MemoryChunk"},
    )
    registry.register(
        "generate_coaching_summary",
        lambda metrics, recovery, baselines: generate_coaching_summary(metrics, recovery, baselines),
        {"name": "generate_coaching_summary", "input": {"metrics": "HealthMetrics", "recovery": "Recovery", "baselines": "Baselines"}, "output": "CoachingSummary"},
    )
    registry.register(
        "log_agent_event",
        lambda run_id, user_id, event_type, payload: logger.log_event(db, run_id, user_id, event_type, payload),
        {"name": "log_agent_event", "input": {"run_id": "str", "user_id": "str", "event_type": "str", "payload": "dict"}, "output": "None"},
    )
    registry.register(
        "create_alert",
        lambda user_id, message: logger.log_event(db, "system", user_id, "alert", {"message": message}),
        {"name": "create_alert", "input": {"user_id": "str", "message": "str"}, "output": "None"},
    )

    return registry
