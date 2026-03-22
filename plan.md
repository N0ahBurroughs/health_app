# Implementation Roadmap

## Phase 1: MVP Multi-Agent Core
**Goal**: Stand up orchestration with basic agents and shared tools.
- Add `agents/`, `tools/`, `orchestration/` modules in FastAPI.
- Implement `HealthAnalysisAgent`, `CoachAgent`, `TrainingOptimizerAgent`, `AnomalyDetectionAgent`, `PlannerAgent`.
- Add API endpoints:
  - `POST /api/agent/run`
  - `POST /api/workflows/daily-check`
  - `POST /api/workflows/training-reco`
  - `POST /api/workflows/anomaly-alert`
- Add `agents.md` and `skill.md`.

## Phase 2: Memory + MCP + Observability
**Goal**: Persist agent memory and expose tools over MCP.
- Add pgvector-backed `memory_chunks` and `agent_runs`.
- Implement memory write/search tools.
- Add MCP router:
  - `GET /mcp/tools`
  - `POST /mcp/tool/call`
- Log prompt/response payloads and latency metrics.

## Phase 3: Advanced Safety + Evaluation
**Goal**: Guardrails, automated evaluation, and feedback loops.
- Prompt injection filtering and output guardrails.
- Add output quality checks (schema adherence, fallback rate).
- Integrate user feedback tags for agent improvement.

## Phase 4: Stretch Capabilities
**Goal**: Autonomous loops, self-improving prompts, and simulations.
- Add autonomous agent loop for daily plan refinement.
- Experiment with self-improving prompts with A/B testing.
- Add simulation endpoints for what-if training scenarios.

## Milestones
- MVP orchestration working end-to-end
- Memory + MCP integration verified
- Safety + evaluation metrics logged
- Simulation endpoints (stretch)
