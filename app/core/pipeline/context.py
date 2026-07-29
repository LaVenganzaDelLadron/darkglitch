#app/core/pipeline/context.py
from __future__ import annotations
from dataclasses import dataclass, field
from app.core.ai.base import LLMProvider
from app.core.memory.conversation import ConversationMemory
from app.core.memory.project import ProjectMemory


@dataclass(slots=True)
class PipelineContext:
    llm: LLMProvider
    conversation: ConversationMemory
    project: ProjectMemory
    metadata: dict = field(default_factory=dict)