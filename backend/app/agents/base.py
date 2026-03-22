from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .. import schemas


ToolFn = Callable[..., Any]


@dataclass(frozen=True)
class AgentContext:
    tools: dict[str, ToolFn]
    memory: dict[str, Any]


class BaseAgent:
    name = "base"
    description = "Base agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    def run(self, agent_input: schemas.AgentInput) -> schemas.AgentOutput:
        raise NotImplementedError

    def _tool(self, name: str) -> ToolFn:
        if name not in self.context.tools:
            raise KeyError(f"Tool not registered: {name}")
        return self.context.tools[name]
