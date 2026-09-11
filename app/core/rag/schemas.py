from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvidenceDocument:
    source: str
    raw_content: str
    scanner_name: str | None = None
    target_host: str | None = None
    severity: str | None = None
    category: str | None = None
    parsed_content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    title: str
    evidence: str
    severity: str | None = None
    category: str | None = None
    references: list[str] = field(default_factory=list)
    remediation_tags: list[str] = field(default_factory=list)
    document_id: str | None = None
    identifiers: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class EvidenceChunk:
    document_id: str
    text: str
    chunk_type: str = "evidence"
    chunk_index: int = 0
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
