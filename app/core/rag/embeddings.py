from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

from .schemas import EvidenceChunk


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embeddings for tests and offline deployments."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for word in text.lower().split():
                index = int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big") % self.dimensions
                vector[index] += 1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors

    def embed_chunks(self, chunks: list[EvidenceChunk]) -> dict[str, list[float]]:
        return dict(zip((chunk.chunk_id for chunk in chunks), self.embed([c.text for c in chunks])))
