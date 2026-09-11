from __future__ import annotations

from app.core.rag.chunking import EvidenceChunker
from app.core.rag.embeddings import HashEmbeddingProvider
from app.core.rag.ingestion import EvidenceIngestor
from app.core.rag.retriever import EvidenceRetriever
from app.core.rag.store import InMemoryVectorStore

ingestor = EvidenceIngestor()
retriever = EvidenceRetriever(HashEmbeddingProvider(), InMemoryVectorStore())
chunker = EvidenceChunker()

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field

    class IngestRequest(BaseModel):
        source: str
        content: str
        scanner_name: str | None = None
        target_host: str | None = None
        severity: str | None = None
        category: str | None = None

    class QueryRequest(BaseModel):
        query: str = Field(min_length=1)
        top_k: int = Field(default=5, ge=1, le=50)

    app = FastAPI(title="DarkGlitch AI Pipeline", version="1.0")

    @app.post("/evidence")
    def ingest(request: IngestRequest):
        document = ingestor.ingest(request.content, source=request.source,
                                   scanner_name=request.scanner_name,
                                   target_host=request.target_host,
                                   severity=request.severity, category=request.category)
        chunks = chunker.chunk(document)
        retriever.index(chunks)
        return {"document_id": document.document_id, "chunks": len(chunks)}

    @app.post("/retrieve")
    def retrieve(request: QueryRequest):
        results = retriever.retrieve(request.query, top_k=request.top_k)
        return {"results": [{"score": result.score, **result.chunk.to_dict()}
                            for result in results]}
except ImportError:
    app = None
