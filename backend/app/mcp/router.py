from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import inspect
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import MCPToolCallRequest, MCPToolCallResponse
from ..tools.factory import build_tool_registry


router = APIRouter(prefix="/mcp", tags=["mcp"])

def _serialize(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(val) for key, val in value.items()}
    try:
        mapper = sa_inspect(value)
        data = {}
        for column in mapper.mapper.column_attrs:
            data[column.key] = _serialize(getattr(value, column.key))
        return data
    except Exception:
        return {"value": str(value)}

def _filter_kwargs(fn, kwargs: dict):
    sig = inspect.signature(fn)
    accepted = set(sig.parameters.keys())
    return {key: value for key, value in kwargs.items() if key in accepted}


@router.get("/tools")
def list_tools(db: Session = Depends(get_db)):
    registry = build_tool_registry(db)
    return {"tools": registry.list()}


@router.post("/tool/call", response_model=MCPToolCallResponse)
def call_tool(payload: MCPToolCallRequest, db: Session = Depends(get_db)):
    registry = build_tool_registry(db)
    if payload.tool not in registry.all():
        raise HTTPException(status_code=404, detail="Tool not found")
    tool = registry.get(payload.tool)
    safe_args = _filter_kwargs(tool, payload.arguments)
    result = tool(**safe_args)
    return MCPToolCallResponse(tool=payload.tool, result=_serialize(result))
