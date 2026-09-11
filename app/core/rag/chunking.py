from __future__ import annotations

from .schemas import EvidenceChunk, EvidenceDocument


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class EvidenceChunker:
    def __init__(self, target_tokens: int = 500, overlap_tokens: int = 75):
        if target_tokens <= overlap_tokens:
            raise ValueError("target_tokens must be greater than overlap_tokens")
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(self, document: EvidenceDocument) -> list[EvidenceChunk]:
        text = document.raw_content
        if estimate_tokens(text) <= self.target_tokens:
            parts = [text]
        else:
            size, overlap, parts, start = self.target_tokens * 4, self.overlap_tokens * 4, [], 0
            while start < len(text):
                end = min(len(text), start + size)
                if end < len(text):
                    boundary = text.rfind("\n", start, end)
                    if boundary > start:
                        end = boundary
                parts.append(text[start:end].strip())
                if end == len(text):
                    break
                start = max(start + 1, end - overlap)
        return [
            EvidenceChunk(
                document_id=document.document_id, text=part, chunk_index=index,
                token_count=estimate_tokens(part),
                metadata={**document.metadata, "source": document.source,
                          "severity": document.severity, "target_host": document.target_host},
            )
            for index, part in enumerate(parts) if part
        ]
