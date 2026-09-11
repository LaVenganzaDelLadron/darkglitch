from __future__ import annotations

import re

from .store import SearchResult


class ResponseValidator:
    REQUIRED_HEADINGS = ("Executive Summary", "Evidence", "Remediation", "Confidence")

    def validate(self, response: str, evidence: list[SearchResult], *, response_format: str = "markdown") -> str:
        if not response.strip():
            raise ValueError("The model returned an empty response")
        if response_format == "json":
            import json
            try:
                json.loads(response)
            except json.JSONDecodeError as error:
                raise ValueError("The model returned invalid JSON") from error
            return response
        if not evidence:
            raise ValueError("Insufficient evidence to produce an analysis")
        missing = [heading for heading in self.REQUIRED_HEADINGS
                   if not re.search(rf"(?im)^#+\s*{re.escape(heading)}\b", response)]
        if missing:
            raise ValueError(f"Response is missing required sections: {', '.join(missing)}")
        return response
