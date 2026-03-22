from __future__ import annotations

from .. import schemas
from .base import BaseAgent


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "Stitches agent outputs into a final user-facing insight."

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        outputs = self.context.memory.get("agent_outputs", {})
        summaries = [output.summary for output in outputs.values() if output.summary]
        recommendations: list[str] = []
        for output in outputs.values():
            recommendations.extend(output.recommendations)

        summary = " ".join(summaries) if summaries else "Health insights generated."

        return schemas.AgentOutput(
            summary=summary,
            recommendations=recommendations[:5],
            actions=["publish_insight"],
            confidence=0.68,
            citations=["internal:planner_v1"],
        )
