#app/tools/registry.py
from __future__ import annotations
from app.tools.base import Tool, ToolOperation, ToolResult


class ToolRegistry:

    def __init__(self):
        self._operations: dict[str, ToolOperation] = {}

    def register(self, tool: Tool) -> None:
        """Register all operations from a tool."""
        for op in tool.operations():
            self._operations[op.name] = op

    def unregister(self, name: str) -> None:
        """Unregister a single operation by its full name."""
        self._operations.pop(name, None)

    def get(self, name: str) -> ToolOperation:
        """Get a registered operation by its full name."""
        if name not in self._operations:
            raise KeyError(f"Tool operation '{name}' is not registered.")
        return self._operations[name]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a registered operation by name with given arguments."""
        op = self.get(name)
        return op.fn(**kwargs)

    def schemas(self) -> list[dict]:
        """Return OpenAI-compatible tool schemas for all registered operations."""
        return [
            {
                "type": "function",
                "function": {
                    "name": op.name,
                    "description": op.description,
                    "parameters": op.parameters,
                },
            }
            for op in self._operations.values()
        ]

    def names(self) -> list[str]:
        return list(self._operations.keys())

    def all(self) -> list[ToolOperation]:
        return list(self._operations.values())