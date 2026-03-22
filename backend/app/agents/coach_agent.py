from __future__ import annotations

from .. import schemas
from .base import BaseAgent


class CoachAgent(BaseAgent):
    name = "coach"
    description = "Generates daily coaching guidance and behavior suggestions."

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        baselines = agent_input.baselines
        if baselines is None:
            baselines = self._tool("get_baselines")(agent_input.user_id)

        recovery = self._tool("compute_recovery")(agent_input.metrics, baselines)
        coaching = self._tool("generate_coaching_summary")(agent_input.metrics, recovery, baselines)
        recommendations = coaching.get("recommendations", [])
        summary = coaching.get("summary", "Coaching guidance based on recent trends.")

        return schemas.AgentOutput(
            summary=summary,
            recommendations=recommendations,
            actions=["send_coaching_message"],
            confidence=0.66,
            citations=["internal:trend_summary_v1"],
        )
