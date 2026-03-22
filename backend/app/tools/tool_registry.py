from __future__ import annotations

from typing import Any, Callable

ToolFn = Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFn] = {}
        self._schemas: dict[str, dict] = {}

    def register(self, name: str, fn: ToolFn, schema: dict) -> None:
        self._tools[name] = fn
        self._schemas[name] = schema

    def get(self, name: str) -> ToolFn:
        return self._tools[name]

    def list(self) -> dict[str, dict]:
        return self._schemas.copy()

    def all(self) -> dict[str, ToolFn]:
        return self._tools.copy()
