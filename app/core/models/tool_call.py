#app/core/models/tool_call.py
from __future__ import annotations
import json
from dataclasses import dataclass, field


@dataclass(slots=True)
class ToolCall:
    id: str = ""
    name: str = ""
    arguments: dict = field(default_factory=dict)

    def __post_init__(self):
        """Ensure arguments is a dict, parsing JSON string if needed."""
        if isinstance(self.arguments, str):
            try:
                self.arguments = json.loads(self.arguments)
            except (json.JSONDecodeError, TypeError):
                self.arguments = {"raw": self.arguments}

    def to_dict(self) -> dict:
        """Simple dict representation (legacy)."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    def to_openai_dict(self) -> dict:
        """OpenAI-compatible tool call format for API submission."""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments),
            },
        }