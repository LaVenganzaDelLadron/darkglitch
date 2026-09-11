"""Read-only scan for likely hard-coded credentials in local text files."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

MAX_FILE_SIZE = 1_000_000
IGNORED_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", "node_modules"}

PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("credential_assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token|access[_-]?token)"
        r"\s*[:=]\s*['\"]([^'\"$\s]{8,})['\"]"
    )),
)


@dataclass(frozen=True, slots=True)
class CredentialFinding:
    path: str
    line: int
    kind: str
    redacted_value: str


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "[REDACTED]"
    return f"{value[:3]}...{value[-3:]}"


def _files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and not any(part in IGNORED_DIRECTORIES for part in child.parts):
                    yield child


def scan(paths: Iterable[str | Path]) -> tuple[list[CredentialFinding], list[str]]:
    findings: list[CredentialFinding] = []
    skipped: list[str] = []
    for path in _files(Path(item) for item in paths):
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                skipped.append(f"{path}: larger than {MAX_FILE_SIZE} bytes")
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped.append(str(path))
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in PATTERNS:
                match = pattern.search(line)
                if match:
                    value = match.group(1) if kind == "credential_assignment" else match.group(0)
                    findings.append(CredentialFinding(str(path), line_number, kind, _redact(value)))
                    break
    return findings, skipped


def format_report(findings: list[CredentialFinding], skipped: list[str],
                  json_output: bool = False) -> str:
    payload = {"findings": [asdict(item) for item in findings], "skipped": skipped}
    if json_output:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [f"Credential audit: {len(findings)} finding(s)"]
    for finding in findings:
        lines.append(f"- {finding.kind} at {finding.path}:{finding.line} "
                     f"({finding.redacted_value})")
    lines.extend(f"Skipped: {item}" for item in skipped)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darkglitch credentials")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    findings, skipped = scan(args.paths)
    print(format_report(findings, skipped, args.json_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
