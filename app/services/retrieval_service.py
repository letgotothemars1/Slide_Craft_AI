from __future__ import annotations

import logging
import math

from app import repository
from app.db import SessionLocal
from app.services.embedding_service import get_embedding_service
from app.project_schemas import SourceRef

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
    """Legacy one-shot shape: return only chunk text."""
    return [excerpt for _, excerpt in _rank_chunks(prompt, document_id, top_k)[1]]


def retrieve_relevant_source_refs(prompt: str, document_id: str, top_k: int = 5) -> list[SourceRef]:
    """Modular project shape: never guess a missing source page."""
    filename, ranked = _rank_chunks(prompt, document_id, top_k)
    if any(page_number is None for page_number, _ in ranked):
        raise RuntimeError("Document was indexed without page numbers; re-upload the PDF")
    return [
        SourceRef(document_id=document_id, filename=filename, page_number=page_number, excerpt=excerpt)
        for page_number, excerpt in ranked
    ]


def _rank_chunks(prompt: str, document_id: str, top_k: int) -> tuple[str, list[tuple[int | None, str]]]:
    logger.debug("retrieval.started document_id=%s top_k=%s", document_id, top_k)

    with SessionLocal() as session:
        document = repository.get_document(session, document_id)
        if document is None:
            raise LookupError(f"Document not found: {document_id}")

        chunks = repository.list_document_chunks(session, document_id)
        if not chunks:
            raise RuntimeError(f"Document has no indexed chunks: {document_id}")

        filename = document.filename

    embedding_service = get_embedding_service()
    prompt_embedding = embedding_service.embed_text(prompt)

    scored: list[tuple[float, int | None, str]] = []
    for chunk in chunks:
        if len(chunk.embedding) != len(prompt_embedding):
            raise RuntimeError("Document embedding provider changed; re-upload the PDF")
        score = _cosine_similarity(prompt_embedding, [float(value) for value in chunk.embedding])
        scored.append((score, chunk.page_number, chunk.chunk_text))

    scored.sort(key=lambda item: item[0], reverse=True)
    result = [(page_number, excerpt) for _, page_number, excerpt in scored[:top_k] if excerpt.strip()]

    logger.debug(
        "retrieval.completed document_id=%s candidates=%s returned=%s",
        document_id,
        len(scored),
        len(result),
    )
    return filename, result
