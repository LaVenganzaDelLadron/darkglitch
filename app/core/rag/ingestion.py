from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import EvidenceDocument


class IngestionError(ValueError):
    pass


class EvidenceIngestor:
    """Normalize scanner output while retaining original evidence."""

    def ingest(self, content: Any, *, source: str, **metadata: Any) -> EvidenceDocument:
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        if isinstance(content, str):
            raw = content
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"text": content}
        elif isinstance(content, (dict, list)):
            parsed = content
            raw = json.dumps(content, sort_keys=True, default=str)
        else:
            raise IngestionError("Evidence must be text, bytes, an object, or a list")
        if not raw.strip():
            raise IngestionError("Evidence cannot be empty")
        fields = {key: metadata.pop(key, None) for key in
                  ("scanner_name", "target_host", "severity", "category")}
        parsed_content = parsed if isinstance(parsed, dict) else {"items": parsed}
        return EvidenceDocument(source=source, raw_content=raw,
                                parsed_content=parsed_content, metadata=metadata, **fields)

    def ingest_file(self, path: str | Path, *, source: str | None = None,
                    max_bytes: int = 10_000_000, **metadata: Any) -> EvidenceDocument:
        file_path = Path(path)
        if file_path.stat().st_size > max_bytes:
            raise IngestionError("Uploaded evidence exceeds the configured size limit")
        return self.ingest(file_path.read_bytes(),
                           source=source or file_path.suffix.lstrip(".") or "file",
                           **metadata)
