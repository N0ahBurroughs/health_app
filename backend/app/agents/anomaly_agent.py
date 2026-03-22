from __future__ import annotations

from .. import schemas
from .base import BaseAgent


class AnomalyDetectionAgent(BaseAgent):
    name = "anomaly_detection"
    description = "Detects abnormal patterns in HR/HRV/sleep."

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        baselines = agent_input.baselines
        if baselines is None:
            baselines = self._tool("get_baselines")(agent_input.user_id)

        anomalies = self._tool("anomaly_scan")(agent_input.metrics, baselines)

        summary = "No anomalies detected."
        actions = []
        recommendations = []
        if anomalies["anomaly"]:
            summary = f"Potential anomaly detected: {anomalies['reason']}."
            recommendations = [
                "Take a lighter day and prioritize recovery.",
                "Monitor symptoms and consider rest.",
            ]
            actions = ["create_alert"]

        return schemas.AgentOutput(
            summary=summary,
            recommendations=recommendations,
            actions=actions,
            confidence=0.7 if anomalies["anomaly"] else 0.55,
            citations=["internal:anomaly_scan_v1"],
        )
