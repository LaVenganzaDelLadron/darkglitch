from __future__ import annotations

from dataclasses import dataclass

from app.core.ai.base import LLMProvider

from .chunking import EvidenceChunker
from .context import ContextManager
from .ingestion import EvidenceIngestor
from .prompt import PromptBuilder
from .retriever import EvidenceRetriever
from .validation import ResponseValidator


@dataclass
class AnalysisResult:
    response: str
    retrieved_chunks: int


class RAGPipeline:
    def __init__(self, provider: LLMProvider, retriever: EvidenceRetriever,
                 ingestor: EvidenceIngestor | None = None,
                 chunker: EvidenceChunker | None = None,
                 context: ContextManager | None = None):
        self.provider = provider
        self.retriever = retriever
        self.ingestor = ingestor or EvidenceIngestor()
        self.chunker = chunker or EvidenceChunker()
        self.context = context or ContextManager()
        self.prompts = PromptBuilder()
        self.validator = ResponseValidator()

    def ingest(self, content: object, *, source: str, **metadata: object) -> str:
        document = self.ingestor.ingest(content, source=source, **metadata)
        self.retriever.index(self.chunker.chunk(document))
        return document.document_id

    def analyze(self, request: str, *, top_k: int = 5,
                response_format: str = "markdown") -> AnalysisResult:
        evidence = self.retriever.retrieve(request, top_k=top_k)
        if not evidence:
            raise ValueError("Insufficient evidence to produce an analysis")
        context = self.context.build(evidence)
        messages = self.prompts.build(request, context, response_format=response_format)
        if hasattr(self.provider, "generate_messages"):
            response = self.provider.generate_messages(messages)
        else:
            response = self.provider.generate("\n\n".join(message["content"] for message in messages))
        return AnalysisResult(self.validator.validate(response, evidence,
                                                      response_format=response_format),
                              len(evidence))
