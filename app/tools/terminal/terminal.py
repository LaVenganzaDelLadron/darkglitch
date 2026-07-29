#app/tools/terminal/terminal.py
from __future__ import annotations
import subprocess
from app.tools.base import Tool, ToolResult, ToolOperation
from app.core.utils.output_compressor import compress_output


class TerminalTool(Tool):

    name = "terminal"
    description = "Execute shell commands in the terminal."

    def run(
        self,
        command: str,
        max_lines: int = 100,
        head: int = 50,
        tail: int = 30,
    ) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
            )

            raw_output = result.stdout if result.returncode == 0 else (result.stderr or result.stdout)
            error_output = result.stderr if result.returncode != 0 else None

            # Apply compression: binary/JSON/HTML detection + text truncation
            compressed = compress_output(raw_output)

            return ToolResult(
                success=result.returncode == 0,
                content=compressed.content,
                error=error_output or (compressed.summary if compressed.truncated else None),
                truncated=compressed.truncated,
                original_length=compressed.original_length,
                metadata={
                    "returncode": result.returncode,
                    "original_type": compressed.original_type,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )

    def operations(self) -> list[ToolOperation]:
        return [
            ToolOperation(
                name=f"{self.name}.run",
                description="Execute a shell command and return its output. Long outputs are automatically summarized.",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute.",
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of lines to return. Output exceeding this is truncated.",
                            "default": 100,
                        },
                        "head": {
                            "type": "integer",
                            "description": "Number of lines from the start to show when truncated.",
                            "default": 50,
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines from the end to show when truncated.",
                            "default": 30,
                        },
                    },
                    "required": ["command"],
                },
                fn=self.run,
            ),
        ]