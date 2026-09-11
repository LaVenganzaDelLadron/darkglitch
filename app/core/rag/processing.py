from __future__ import annotations

import re

from .schemas import EvidenceDocument, Finding

_PATTERNS = {
    "urls": r"https?://[^\s\"']+",
    "cves": r"\bCVE-\d{4}-\d{4,7}\b",
    "cwes": r"\bCWE-\d+\b",
    "owasp": r"\bA\d{2}:\d{4}\b",
}


class EvidenceProcessor:
    def extract(self, document: EvidenceDocument) -> dict[str, list[str]]:
        text = document.raw_content
        extracted = {name: sorted(set(re.findall(pattern, text, re.IGNORECASE)))
                     for name, pattern in _PATTERNS.items()}
        extracted["status_codes"] = sorted(set(re.findall(r"\b[1-5]\d\d\b", text)))
        extracted["methods"] = sorted(set(re.findall(
            r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", text, re.IGNORECASE)))
        return extracted

    def to_finding(self, document: EvidenceDocument, title: str | None = None) -> Finding:
        return Finding(title=title or document.category or "Security finding",
                       evidence=document.raw_content, severity=document.severity,
                       category=document.category, document_id=document.document_id,
                       identifiers=self.extract(document))

    def enrich(self, document: EvidenceDocument) -> EvidenceDocument:
        document.parsed_content = {
            **document.parsed_content, "extracted": self.extract(document)
        }
        return document
