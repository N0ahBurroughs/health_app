from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from ..models import MemoryChunk


def _embed_text(text: str) -> list[float]:
    # Deterministic lightweight embedding (placeholder for real model embeddings).
    buckets = [0.0] * 8
    for idx, char in enumerate(text[:256]):
        buckets[idx % 8] += float(ord(char))
    total = sum(buckets) or 1.0
    return [value / total for value in buckets]


def write_memory(db: Session, user_id: str, memory_type: str, content: str, metadata: dict[str, Any]):
    embedding = _embed_text(content)
    record = MemoryChunk(
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        embedding=embedding,
        metadata=metadata,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def search_memory(db: Session, user_id: str, query: str, top_k: int = 5):
    embedding = _embed_text(query)
    results = (
        db.query(MemoryChunk)
        .filter(MemoryChunk.user_id == user_id)
        .order_by(MemoryChunk.embedding.l2_distance(embedding))
        .limit(top_k)
        .all()
    )
    return [
        {
            "id": item.id,
            "type": item.memory_type,
            "content": item.content,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat(),
        }
        for item in results
    ]
