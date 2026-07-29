#app/core/models/response.py
from dataclasses import dataclass, field
from app.core.models.tool_call import ToolCall
from app.core.models.usage import Usage

@dataclass(slots=True)
class AIResponse:
    content: str | None
    model: str
    usage: Usage
    finish_reason: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)