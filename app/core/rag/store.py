from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .schemas import EvidenceChunk


@dataclass
class SearchResult:
    chunk: EvidenceChunk
    score: float


class InMemoryVectorStore:
    """Dependency-free vector store implementing the Qdrant-facing contract."""

    def __init__(self):
        self._items: dict[str, tuple[EvidenceChunk, list[float]]] = {}

    def upsert(self, chunks: list[EvidenceChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        for chunk, vector in zip(chunks, vectors):
            self._items[chunk.chunk_id] = (chunk, vector)

    def search(self, vector: list[float], limit: int = 5,
               filters: dict[str, Any] | None = None) -> list[SearchResult]:
        def matches(chunk: EvidenceChunk) -> bool:
            return all(chunk.metadata.get(key) == value
                       for key, value in (filters or {}).items())

        results = []
        for chunk, candidate in self._items.values():
            if not matches(chunk):
                continue
            denominator = math.sqrt(sum(x * x for x in vector) *
                                    sum(x * x for x in candidate)) or 1.0
            score = sum(x * y for x, y in zip(vector, candidate)) / denominator
            results.append(SearchResult(chunk, score))
        return sorted(results, key=lambda result: result.score, reverse=True)[:max(1, limit)]

    def delete_document(self, document_id: str) -> None:
        self._items = {key: value for key, value in self._items.items()
                       if value[0].document_id != document_id}

    def clear(self) -> None:
        self._items.clear()


class QdrantVectorStore:
    """Qdrant adapter with the same operations as the local store.

    Importing this module does not require qdrant-client; deployments that select
    this backend receive an actionable dependency error instead.
    """

    def __init__(self, url: str, collection: str = "darkglitch-evidence",
                 api_key: str | None = None, vector_size: int = 256):
        try:
            from qdrant_client import QdrantClient, models
        except ImportError as error:
            raise RuntimeError("Install qdrant-client to use QdrantVectorStore") from error
        self._models = models
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection = collection
        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    def upsert(self, chunks: list[EvidenceChunk], vectors: list[list[float]]) -> None:
        points = [
            self._models.PointStruct(id=chunk.chunk_id, vector=vector,
                                     payload=chunk.to_dict())
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: list[float], limit: int = 5,
               filters: dict[str, Any] | None = None) -> list[SearchResult]:
        query_filter = None
        if filters:
            query_filter = self._models.Filter(must=[
                self._models.FieldCondition(key=key,
                    match=self._models.MatchValue(value=value))
                for key, value in filters.items()
            ])
        points = self.client.search(collection_name=self.collection, query_vector=vector,
                                    query_filter=query_filter, limit=limit)
        return [SearchResult(EvidenceChunk(**point.payload), point.score) for point in points]

    def delete_document(self, document_id: str) -> None:
        self.client.delete(collection_name=self.collection, points_selector=self._models.Filter(
            must=[self._models.FieldCondition(key="document_id",
                  match=self._models.MatchValue(value=document_id))]))

    def clear(self) -> None:
        self.client.delete_collection(self.collection)
