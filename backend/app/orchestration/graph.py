from __future__ import annotations

from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END

from .. import schemas
from ..agents.base import AgentContext
from ..agents.registry import AGENT_CLASSES
from ..observability import logger
from ..observability.evaluation import evaluate_output
from ..safety.guards import apply_medical_guardrail


class OrchestrationState(TypedDict):
    task_type: str
    agent_input: schemas.AgentInput
    agent_outputs: dict[str, schemas.AgentOutput]


def _prompt_for_agent(agent_name: str, agent_input: schemas.AgentInput) -> str:
    return (
        f"Agent {agent_name} processing user {agent_input.user_id} at {agent_input.timestamp} "
        f"with metrics {agent_input.metrics.model_dump()}."
    )


def _run_agent(state: OrchestrationState, agent_name: str, context: AgentContext):
    agent_cls = AGENT_CLASSES[agent_name]
    agent = agent_cls(context)
    prompt = _prompt_for_agent(agent_name, state["agent_input"])
    db = context.memory.get("db")
    run_id = None
    start = None
    if db is not None:
        run_id, start = logger.start_run(state["agent_input"].user_id, agent_name)
    output = agent.run(state["agent_input"])
    if db is not None and run_id and start is not None:
        logger.end_run(
            db,
            run_id,
            state["agent_input"].user_id,
            agent_name,
            prompt,
            output.model_dump(),
            start,
        )
    return output


def _fallback_output() -> schemas.AgentOutput:
    return schemas.AgentOutput(
        summary="Unable to generate full insights; showing baseline recovery guidance.",
        recommendations=["Prioritize sleep and hydration."],
        actions=["publish_insight"],
        confidence=0.3,
        citations=["internal:fallback_v1"],
    )


def build_graph(context: AgentContext):
    graph = StateGraph(OrchestrationState)

    def router_node(state: OrchestrationState):
        return state

    def analysis_node(state: OrchestrationState):
        return {"agent_outputs": {"health_analysis": _run_agent(state, "health_analysis", context)}}

    def coach_node(state: OrchestrationState):
        return {"agent_outputs": {**state["agent_outputs"], "coach": _run_agent(state, "coach", context)}}

    def training_node(state: OrchestrationState):
        return {
            "agent_outputs": {**state["agent_outputs"], "training_optimizer": _run_agent(state, "training_optimizer", context)}
        }

    def anomaly_node(state: OrchestrationState):
        return {"agent_outputs": {**state["agent_outputs"], "anomaly_detection": _run_agent(state, "anomaly_detection", context)}}

    def planner_node(state: OrchestrationState):
        context.memory["agent_outputs"] = state["agent_outputs"]
        output = _run_agent(state, "planner", context)
        output.summary = apply_medical_guardrail(output.summary)
        return {"agent_outputs": {**state["agent_outputs"], "planner": output}}

    def fallback_node(state: OrchestrationState):
        return {"agent_outputs": {**state["agent_outputs"], "planner": _fallback_output()}}

    graph.add_node("analysis", analysis_node)
    graph.add_node("coach", coach_node)
    graph.add_node("training", training_node)
    graph.add_node("anomaly", anomaly_node)
    graph.add_node("planner", planner_node)
    #graph.add_node("fallback", fallback_node)
    graph.add_node("router", router_node)

    def route(state: OrchestrationState) -> Literal["analysis", "anomaly"]:
        task_type = state["task_type"]
        if task_type == "anomaly_alert":
            return "anomaly"
        return "analysis"

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route, {"analysis": "analysis", "anomaly": "anomaly"})
    graph.add_edge("analysis", "coach")
    graph.add_edge("training", "planner")
    graph.add_edge("anomaly", "coach")
    graph.add_edge("planner", END)
    #graph.add_edge("fallback", END)

    def conditional_next(state: OrchestrationState):
        if state["task_type"] == "training_reco":
            return "training"
        return "planner"

    graph.add_conditional_edges("coach", conditional_next, {"training": "training", "planner": "planner"})
    # Analysis and anomaly nodes flow into coach by default.

    return graph.compile()


def run_task(task_type: str, agent_input: schemas.AgentInput, context: AgentContext):
    state: OrchestrationState = {"task_type": task_type, "agent_input": agent_input, "agent_outputs": {}}
    graph = build_graph(context)
    try:
        result = graph.invoke(state)
        outputs = result["agent_outputs"]
        final = outputs.get("planner") or _fallback_output()
    except Exception:
        outputs = {"planner": _fallback_output()}
        final = outputs["planner"]

    evaluation = evaluate_output(final.model_dump())
    context.memory["evaluation"] = evaluation
    return outputs, final
