from __future__ import annotations

from .embeddings import EmbeddingProvider
from .store import InMemoryVectorStore, SearchResult
from .schemas import EvidenceChunk


class EvidenceRetriever:
    def __init__(self, embeddings: EmbeddingProvider, store: InMemoryVectorStore,
                 top_k: int = 5):
        self.embeddings, self.store, self.top_k = embeddings, store, top_k

    def index(self, chunks: list[EvidenceChunk]) -> None:
        self.store.upsert(chunks, self.embeddings.embed([chunk.text for chunk in chunks]))

    def retrieve(self, query: str, *, top_k: int | None = None,
                 filters: dict | None = None) -> list[SearchResult]:
        results = self.store.search(self.embeddings.embed([query])[0],
                                    limit=top_k or self.top_k, filters=filters)
        unique: dict[str, SearchResult] = {}
        for result in results:
            unique.setdefault(result.chunk.text, result)
        return list(unique.values())
