#app/core/memory/project.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectMemory:
    root: Path | None = None
    language: str | None = None
    framework: str | None = None
    repository_name: str | None = None
    branch: str | None = None
    opened_files: list[Path] = field(default_factory=list)
    scanned: bool = False
    metadata: dict = field(default_factory=dict)

    def open(self, path: str | Path) -> None:
        self.root = Path(path).resolve()

    def reset(self) -> None:
        self.root = None
        self.language = None
        self.framework = None
        self.repository_name = None
        self.branch = None
        self.opened_files.clear()
        self.metadata.clear()
        self.scanned = False