#app/tools/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class ToolResult:
    """Result returned by any tool operation.

    Every tool must return a ToolResult. The compression layer
    (output_compressor) is applied before this is stored in conversation
    memory or sent to the LLM.
    """
    success: bool
    content: str = ""
    error: str | None = None
    truncated: bool = False
    original_length: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def output(self) -> str:
        """Backward-compatible alias for content."""
        return self.content

    @output.setter
    def output(self, value: str) -> None:
        self.content = value


@dataclass(slots=True)
class ToolParameter:
    """JSON Schema for a single parameter."""
    type: str
    description: str = ""
    enum: list[str] | None = None
    default: Any = None


@dataclass(slots=True)
class ToolOperation:
    """A callable operation exposed as a tool to the LLM."""
    name: str
    description: str
    parameters: dict
    fn: Callable[..., ToolResult]


class Tool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def operations(self) -> list[ToolOperation]:
        raise NotImplementedError