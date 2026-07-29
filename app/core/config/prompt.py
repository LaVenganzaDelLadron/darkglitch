#app/core/config/prompt.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path


class PromptLoader:
    _prompt_dir = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "prompts"
    )

    @classmethod
    def load(cls, name: str, **kwargs) -> str:
        path = cls._prompt_dir / f"{name}.md"

        if not path.exists():
            raise FileNotFoundError(
                f"Prompt '{name}' not found."
            )

        text = path.read_text(
            encoding="utf-8"
        )

        values = {
            "DATETIME": datetime.now().isoformat(),
            **kwargs,
        }

        return text.format(**values)