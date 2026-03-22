from __future__ import annotations

from .. import schemas
from .base import BaseAgent


class HealthAnalysisAgent(BaseAgent):
    name = "health_analysis"
    description = "Computes baselines, deltas, and summarizes health state."

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        baselines = agent_input.baselines
        if baselines is None:
            baselines = self._tool("get_baselines")(agent_input.user_id)

        recovery = self._tool("compute_recovery")(agent_input.metrics, baselines)
        deltas = self._tool("baseline_delta_calc")(agent_input.metrics, baselines)

        summary = (
            f"Recovery score {recovery['score']:.1f} ({recovery['status']}). "
            f"HRV delta {deltas['hrv_delta']:.1f}, sleep delta {deltas['sleep_delta']:.1f}, "
            f"resting HR delta {deltas['rhr_delta']:.1f}."
        )

        return schemas.AgentOutput(
            summary=summary,
            recommendations=[
                "Keep consistency with sleep schedule.",
                "Hydrate and monitor stress levels.",
            ],
            actions=[
                "update_dashboard_metrics",
                "store_daily_summary",
            ],
            confidence=0.72,
            citations=["internal:recovery_score_v1"],
        )
