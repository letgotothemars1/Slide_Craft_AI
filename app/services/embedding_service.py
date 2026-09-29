from __future__ import annotations

import logging
import hashlib
import re

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """OpenAI embeddings wrapper for document indexing and retrieval."""

    def __init__(self) -> None:
        if not settings.openai_enabled:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return list(response.data[0].embedding)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [list(item.embedding) for item in sorted(response.data, key=lambda row: row.index)]


class LocalEmbeddingService:
    """Deterministic lexical vectors for a key-free local course demo."""

    dimensions = 256

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        return vector

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def get_embedding_service() -> OpenAIEmbeddingService | LocalEmbeddingService:
    if settings.openai_enabled:
        return OpenAIEmbeddingService()
    return LocalEmbeddingService()
