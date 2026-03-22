from __future__ import annotations

from .analysis_agent import HealthAnalysisAgent
from .coach_agent import CoachAgent
from .training_agent import TrainingOptimizerAgent
from .anomaly_agent import AnomalyDetectionAgent
from .planner_agent import PlannerAgent


AGENT_CLASSES = {
    HealthAnalysisAgent.name: HealthAnalysisAgent,
    CoachAgent.name: CoachAgent,
    TrainingOptimizerAgent.name: TrainingOptimizerAgent,
    AnomalyDetectionAgent.name: AnomalyDetectionAgent,
    PlannerAgent.name: PlannerAgent,
}
