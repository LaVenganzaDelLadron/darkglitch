from __future__ import annotations

import json
from typing import Any


class ReportGenerator:
    SECTIONS = ("executive_summary", "target_information", "scan_metadata",
                "findings", "evidence", "technical_analysis", "risk_rating",
                "owasp_mapping", "cwe_mapping", "cvss", "poc_summary",
                "remediation", "references")

    def generate(self, analysis: str, *, target: str | None = None,
                 metadata: dict[str, Any] | None = None,
                 response_format: str = "markdown") -> str | dict[str, Any]:
        if response_format == "json":
            return {"executive_summary": analysis, "target_information": target,
                    "scan_metadata": metadata or {}, "analysis": analysis}
        if response_format != "markdown":
            raise ValueError("response_format must be markdown or json")
        return "\n".join(["# DarkGlitch Security Report", "",
                          f"## Target Information\n{target or 'Not provided'}",
                          "", "## Scan Metadata", "```json",
                          json.dumps(metadata or {}, indent=2, sort_keys=True),
                          "```", "", "## Analysis", analysis])
