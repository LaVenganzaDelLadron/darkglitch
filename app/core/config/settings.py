from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(ValueError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    timeout: float
    model: str = "openai/gpt-oss-120b"
    base_url: str = "https://api.groq.com/openai/v1"
    max_context_tokens: int = 6000
    max_history_messages: int = 20
    max_tool_output_chars: int = 3000
    max_file_size: int = 10_000_000
    max_file_list_items: int = 50
    max_output_lines: int = 100
    reserve_response_tokens: int = 1000

    @property
    def reserve_response_tokes(self) -> int:
        """Backward-compatible spelling used by older pipeline code."""
        return self.reserve_response_tokens


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a positive integer") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be a positive integer")
    return value


def get_settings() -> Settings:
    raw_timeout = os.getenv("GROQ_TIMEOUT", "60")
    try:
        timeout = float(raw_timeout)
    except ValueError as error:
        raise ConfigurationError("GROQ_TIMEOUT must be a positive number") from error
    if timeout <= 0:
        raise ConfigurationError("GROQ_TIMEOUT must be a positive number")
    return Settings(
        api_key=os.getenv("GROQ_API_KEY"),
        timeout=timeout,
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        max_context_tokens=_positive_int("DEFAULT_MAX_CONTEXT_TOKENS", 6000),
        max_history_messages=_positive_int("DEFAULT_MAX_HISTORY_MESSAGES", 20),
        max_tool_output_chars=_positive_int("DEFAULT_MAX_TOOL_OUTPUT_CHARS", 3000),
        max_file_size=_positive_int("DEFAULT_MAX_FILE_SIZE", 10_000_000),
        max_file_list_items=_positive_int("DEFAULT_MAX_LIST_ITEMS", 50),
        max_output_lines=_positive_int("DEFAULT_MAX_OUTPUT_LINES", 100),
        reserve_response_tokens=_positive_int("DEFAULT_RESERVE_RESPONSE_TOKENS", 1000),
    )
