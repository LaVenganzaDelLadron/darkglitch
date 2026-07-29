#app/core/models/message.py
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Literal, Any

Role = Literal[
    "system",
    "user",
    "assistant",
    "tool",
]


def _tc_to_openai(tc: Any) -> dict:
    """Convert a ToolCall or dict to OpenAI-compatible tool_call format."""
    if hasattr(tc, "to_openai_dict"):
        return tc.to_openai_dict()
    # Fallback for plain dicts
    return {
        "id": tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", ""),
        "type": "function",
        "function": {
            "name": tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", ""),
            "arguments": json.dumps(
                tc.get("arguments", {}) if isinstance(tc, dict) else getattr(tc, "arguments", {})
            ),
        },
    }


@dataclass(slots=True)
class Message:
    role: Role
    content: str
    tool_call_id: str = ""
    tool_calls: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to OpenAI/Groq API-compatible dict."""
        d: dict[str, Any] = {
            "role": self.role,
        }

        if self.role == "tool":
            d["tool_call_id"] = self.tool_call_id
            d["content"] = str(self.content)

        elif self.role == "assistant" and self.tool_calls:
            # OpenAI format: content (nullable), tool_calls with id/type/function
            d["content"] = self.content if self.content else None
            d["tool_calls"] = [_tc_to_openai(tc) for tc in self.tool_calls]

        else:
            d["content"] = self.content

        return d