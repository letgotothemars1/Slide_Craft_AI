from __future__ import annotations

import logging
import math

from app import repository
from app.db import SessionLocal
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return -1.0
    return dot / (norm_a * norm_b)


def retrieve_relevant_chunks(prompt: str, document_id: str, top_k: int = 5) -> list[str]:
    logger.debug("retrieval.started document_id=%s top_k=%s", document_id, top_k)

    embedding_service = get_embedding_service()
    prompt_embedding = embedding_service.embed_text(prompt)

    with SessionLocal() as session:
        document = repository.get_document(session, document_id)
        if document is None:
            raise LookupError(f"Document not found: {document_id}")

        chunks = repository.list_document_chunks(session, document_id)
        if not chunks:
            raise RuntimeError(f"Document has no indexed chunks: {document_id}")

    scored: list[tuple[float, str]] = []
    for chunk in chunks:
        score = _cosine_similarity(prompt_embedding, [float(value) for value in chunk.embedding])
        scored.append((score, chunk.chunk_text))

    scored.sort(key=lambda item: item[0], reverse=True)
    result = [text for _, text in scored[:top_k] if text.strip()]

    logger.debug(
        "retrieval.completed document_id=%s candidates=%s returned=%s",
        document_id,
        len(scored),
        len(result),
    )
    return result
