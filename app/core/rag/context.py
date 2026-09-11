from __future__ import annotations

from dataclasses import dataclass

from .chunking import estimate_tokens
from .store import SearchResult


@dataclass
class ContextWindow:
    text: str
    tokens: int
    included_chunks: int


class ContextManager:
    def __init__(self, max_tokens: int = 6000, reserve_response_tokens: int = 1000,
                 max_history_messages: int = 20):
        self.max_tokens = max_tokens
        self.reserve_response_tokens = reserve_response_tokens
        self.max_history_messages = max_history_messages

    def build(self, results: list[SearchResult], history: list[dict] | None = None,
              tool_output: str | None = None) -> ContextWindow:
        budget = max(0, self.max_tokens - self.reserve_response_tokens)
        sections: list[str] = []
        used = 0
        for result in results:
            section = f"[Evidence {len(sections) + 1} | score={result.score:.3f}]\n{result.chunk.text}"
            tokens = estimate_tokens(section)
            if used + tokens > budget:
                continue
            sections.append(section)
            used += tokens
        if history:
            for message in history[-self.max_history_messages:]:
                text = str(message.get("content", ""))
                tokens = estimate_tokens(text)
                if used + tokens > budget:
                    break
                sections.append(f"[Conversation]\n{text}")
                used += tokens
        if tool_output:
            remaining = max(0, (budget - used) * 4)
            sections.append(f"[Tool output]\n{tool_output[:remaining]}")
        return ContextWindow("\n\n".join(sections), estimate_tokens("\n\n".join(sections)),
                            sum(section.startswith("[Evidence") for section in sections))
