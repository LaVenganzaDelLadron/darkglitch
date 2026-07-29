#app/core/utils/output_compressor.py
"""
Central output compression layer for all tools.

Ensures no tool output larger than the configured limit ever reaches
the LLM context window. Handles binary, JSON, HTML, and text output.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Any
from app.core.config.settings import get_settings


@dataclass(slots=True)
class CompressedResult:
    """Compressed version of tool output ready for LLM consumption."""
    content: str
    truncated: bool = False
    original_length: int = 0
    original_type: str = "text"  # text, json, html, binary
    summary: str = ""


def detect_binary(text: str) -> bool:
    """Detect if output contains binary content."""
    if not text:
        return False
    # Check for null bytes and high proportion of non-printable chars
    null_count = text.count("\x00")
    if null_count > 0:
        return True
    # Sample first 4096 bytes for binary detection
    sample = text[:4096]
    non_printable = sum(1 for c in sample if c not in ["\n", "\r", "\t"] and (ord(c) < 32 or ord(c) > 126))
    return non_printable > len(sample) * 0.3


def detect_json(text: str) -> dict | list | None:
    """Try to parse text as JSON, return parsed object or None."""
    text_stripped = text.strip()
    if not text_stripped:
        return None
    try:
        return json.loads(text_stripped)
    except (json.JSONDecodeError, ValueError):
        return None


def detect_html(text: str) -> bool:
    """Detect if output is HTML content."""
    if not text:
        return False
    sample = text[:2000].lower()
    # Look for common HTML signatures
    html_signals = [
        "<!doctype html", "<html", "<head>", "<body>",
        "</html>", "</body>", "<div", "<span", "<a href",
    ]
    return any(signal in sample for signal in html_signals)


def summarize_json(data: Any, max_preview_chars: int = 500) -> str:
    """Summarize JSON data with structure overview instead of full content."""
    lines: list[str] = []

    if isinstance(data, dict):
        lines.append("JSON object")
        lines.append(f"Top-level keys: {', '.join(list(data.keys())[:20])}")
        remaining = len(data) - 20
        if remaining > 0:
            lines.append(f"... and {remaining} more keys")
        lines.append(f"Total bytes: {len(json.dumps(data)):,}")
        # Add first key's preview if small enough
        if data:
            first_key = next(iter(data))
            first_val = data[first_key]
            preview = json.dumps({first_key: first_val}, indent=2)
            if len(preview) < max_preview_chars:
                lines.append("")
                lines.append("Preview (first key):")
                lines.append(preview)

    elif isinstance(data, list):
        lines.append(f"JSON array with {len(data)} items")
        if data:
            lines.append(f"Total bytes: {len(json.dumps(data)):,}")
            # Show structure of first item
            first = data[0]
            if isinstance(first, dict):
                lines.append(f"Item keys: {', '.join(list(first.keys())[:20])}")
            elif isinstance(first, (list, tuple)):
                lines.append(f"Item type: array of {type(first[0]).__name__ if first else 'unknown'}")
            else:
                lines.append(f"Item type: {type(first).__name__}")
            # Show first item if small
            preview = json.dumps(first, indent=2) if isinstance(first, (dict, list)) else str(first)
            if len(preview) < max_preview_chars:
                lines.append("")
                lines.append("First item preview:")
                lines.append(preview)

    else:
        lines.append(f"JSON {type(data).__name__}: {data}")

    return "\n".join(lines)


def summarize_html(text: str) -> str:
    """Extract key metadata from HTML instead of returning full page."""
    lines: list[str] = ["HTML document"]

    # Title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        lines.append(f"Title: {title[:200]}")

    # Meta description
    desc_match = re.search(
        r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
        text, re.IGNORECASE
    )
    if desc_match:
        lines.append(f"Meta description: {desc_match.group(1)[:200]}")

    # Headers
    h1_count = len(re.findall(r"<h1[^>]*>", text, re.IGNORECASE))
    h2_count = len(re.findall(r"<h2[^>]*>", text, re.IGNORECASE))
    h3_count = len(re.findall(r"<h3[^>]*>", text, re.IGNORECASE))
    lines.append(f"Headers: {h1_count} h1, {h2_count} h2, {h3_count} h3")

    # Links
    link_count = len(re.findall(r"<a\s+[^>]*href\s*=", text, re.IGNORECASE))
    lines.append(f"Links: {link_count}")

    # Scripts
    script_count = len(re.findall(r"<script[^>]*>", text, re.IGNORECASE))
    lines.append(f"Scripts: {script_count}")

    # Forms
    form_count = len(re.findall(r"<form[^>]*>", text, re.IGNORECASE))
    lines.append(f"Forms: {form_count}")

    # Images
    img_count = len(re.findall(r"<img[^>]*>", text, re.IGNORECASE))
    lines.append(f"Images: {img_count}")

    # Total size
    lines.append(f"Total bytes: {len(text):,}")

    return "\n".join(lines)


def truncate_text(text: str, max_chars: int, head_lines: int = 50, tail_lines: int = 30) -> CompressedResult:
    """Truncate text with head/tail preview when it exceeds max_chars."""
    total_lines = text.count("\n") + 1
    total_chars = len(text)

    if total_chars <= max_chars:
        return CompressedResult(
            content=text,
            truncated=False,
            original_length=total_chars,
        )

    lines = text.splitlines(keepends=True)

    if len(lines) <= head_lines + tail_lines:
        # Keep all lines if the line count is small
        truncated = text[:max_chars]
        return CompressedResult(
            content=truncated,
            truncated=True,
            original_length=total_chars,
            summary=f"[Output truncated to {max_chars:,} chars. Total: {total_chars:,} chars, {total_lines:,} lines]",
        )

    # Head portion
    head = "".join(lines[:head_lines])
    # Tail portion
    tail = "".join(lines[-tail_lines:])

    content = (
        f"[Output truncated. Total: {total_chars:,} chars, {total_lines:,} lines]\n"
        f"\n"
        f"--- First {head_lines} lines ---\n"
        f"{head}"
        f"\n... (middle {total_lines - head_lines - tail_lines} lines omitted) ...\n"
        f"\n"
        f"--- Last {tail_lines} lines ---\n"
        f"{tail}"
    )

    return CompressedResult(
        content=content,
        truncated=True,
        original_length=total_chars,
        summary=f"[Output truncated. {total_chars:,} chars, {total_lines:,} lines. Showing first {head_lines} and last {tail_lines} lines.]",
    )


def compress_output(text: str, max_chars: int | None = None) -> CompressedResult:
    """
    Main compression entry point.

    Detects output type (binary, JSON, HTML, text) and applies
    appropriate compression strategy. All tools should pipe their
    output through this before returning.
    """
    if max_chars is None:
        settings = get_settings()
        try:
            max_chars = int(settings.max_tool_output_chars)
        except (TypeError, ValueError):
            max_chars = 3000

    if not text:
        return CompressedResult(content="", original_length=0)

    total_chars = len(text)

    # 1. Binary detection
    if detect_binary(text):
        return CompressedResult(
            content="<binary output omitted>",
            truncated=True,
            original_length=total_chars,
            original_type="binary",
            summary=f"<binary output, {total_chars:,} bytes>",
        )

    # 2. JSON detection
    parsed_json = detect_json(text)
    if parsed_json is not None:
        summary = summarize_json(parsed_json)
        if len(summary) <= max_chars:
            return CompressedResult(
                content=summary,
                truncated=len(json.dumps(parsed_json)) > max_chars,
                original_length=total_chars,
                original_type="json",
                summary=f"JSON structure extracted ({total_chars:,} bytes → {len(summary):,} chars)",
            )
        else:
            # Even the summary is too long; truncate it
            truncated_summary = summary[:max_chars]
            return CompressedResult(
                content=truncated_summary + "\n... (summary truncated)",
                truncated=True,
                original_length=total_chars,
                original_type="json",
            )

    # 3. HTML detection
    if detect_html(text):
        summary = summarize_html(text)
        if len(summary) <= max_chars:
            return CompressedResult(
                content=summary,
                truncated=True,
                original_length=total_chars,
                original_type="html",
                summary=f"HTML metadata extracted ({total_chars:,} bytes → {len(summary):,} chars)",
            )
        # Even HTML summary is too long; truncate text style
        return truncate_text(summary, max_chars)

    # 4. Plain text truncation
    return truncate_text(text, max_chars)