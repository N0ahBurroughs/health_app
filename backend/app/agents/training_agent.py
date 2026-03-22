from __future__ import annotations

from .. import schemas
from .base import BaseAgent


class TrainingOptimizerAgent(BaseAgent):
    name = "training_optimizer"
    description = "Optimizes training load and intensity."

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        training = self._tool("training_reco")(agent_input.user_id, agent_input.metrics)
        return schemas.AgentOutput(
            summary=training["summary"],
            recommendations=training["recommendations"],
            actions=["update_training_plan"],
            confidence=0.64,
            citations=["internal:training_reco_v1"],
        )
