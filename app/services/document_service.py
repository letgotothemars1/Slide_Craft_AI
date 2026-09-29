from __future__ import annotations

import logging
import re
from pathlib import Path

from app import repository
from app.db import SessionLocal
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


def extract_pages_from_pdf(file_path: Path) -> list[tuple[int, str]]:
    """Return non-empty PDF pages with their one-based page numbers."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    parts: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            parts.append((page_number, text.strip()))
    return parts


def extract_text_from_pdf(file_path: Path) -> str:
    """Preserve the old plain-text helper for one-shot callers."""
    return "\n\n".join(text for _, text in extract_pages_from_pdf(file_path))


def split_text_into_chunks(
    text: str,
    *,
    chunk_size: int = 1000,
    overlap: int = 150,
    min_chunk_size: int = 800,
) -> list[str]:
    """
    Split text into overlapping chunks.
    Target size is ~800-1200 symbols with 100-200 overlap for MVP RAG.
    """
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(normalized)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        if end < text_len:
            search_from = min(start + min_chunk_size, end)
            # Try to end at sentence boundary to keep chunks readable.
            last_dot = normalized.rfind(". ", search_from, end)
            last_semicolon = normalized.rfind("; ", search_from, end)
            split_at = max(last_dot, last_semicolon)
            if split_at != -1:
                end = split_at + 1

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        start = max(0, end - overlap)

    return chunks


def index_document(document_id: str, file_path: Path) -> int:
    """
    Parse, chunk, embed and persist document chunks.
    Returns number of indexed chunks.
    """
    logger.debug("document.parsed document_id=%s path=%s", document_id, file_path)
    pages = extract_pages_from_pdf(file_path)
    page_chunks = [
        (page_number, chunk)
        for page_number, text in pages
        for chunk in split_text_into_chunks(text)
    ]
    chunks = [chunk for _, chunk in page_chunks]
    logger.debug("document.chunked document_id=%s chunks=%s", document_id, len(chunks))

    if not chunks:
        raise RuntimeError("Document has no extractable text")

    embedding_service = get_embedding_service()
    vectors = embedding_service.embed_texts(chunks)
    logger.debug("document.embeddings.created document_id=%s vectors=%s", document_id, len(vectors))

    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count mismatch")

    rows = [
        (idx, page_number, chunk, vectors[idx])
        for idx, (page_number, chunk) in enumerate(page_chunks)
    ]
    with SessionLocal() as session:
        repository.replace_document_chunks(session, document_id=document_id, chunks=rows)

    return len(chunks)
