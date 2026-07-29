#app/core/config/settings.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

class ConfigurationError(ValueError):
    """Raised when a configuration file is invalid."""

@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    base_url: str
    timeout: float
    max_context_tokens: int = os.getenv("DEFAULT_MAX_CONTEXT_TOKENS")
    max_history_messages: int = os.getenv("DEFAULT_MAX_HISTORY_MESSAGES")
    max_tool_output_chars: int = os.getenv("DEFAULT_MAX_TOOL_OUTPUT_CHARS")
    max_file_size: int = os.getenv("DEFAULT_MAX_FILE_SIZE")
    max_file_list_items: int = os.getenv("DEFAULT_MAX_LIST_ITEMS")
    max_output_lines: int = os.getenv("DEFAULT_MAX_OUTPUT_LINES")
    reserve_response_tokes: int = os.getenv("DEFAULT_RESERVE_RESPONSE_TOKES")

def get_settings() -> Settings:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Please set GROQ_API_KEY environment variable")

    raw_time_out = os.getenv("GROQ_TIMEOUT")
    if raw_time_out is None:
        timeout = 60.0
    else:
        try:
            timeout = float(raw_time_out)
            if timeout <= 0:
                print("Please set GROQ_TIMEOUT to a positive value")
                timeout = 60.0
        except ValueError as error:
            print(f"GROQ timeout error: {error}")
            timeout = 60.0

    model = os.getenv("GROQ_MODEL")
    base_url = os.getenv("GROQ_BASE_URL")

    max_context_tokens = int(os.getenv("DEFAULT_MAX_CONTEXT_TOKENS", "6000"))
    max_history_messages = os.getenv("DEFAULT_MAX_HISTORY_MESSAGES", "20")
    max_tool_output_chars = os.getenv("DEFAULT_MAX_TOOL_OUTPUT_CHARS", "3000")
    max_file_size = os.getenv("DEFAULT_MAX_FILE_SIZE", "10000")
    max_file_list_items = os.getenv("DEFAULT_MAX_FILE_LIST_ITEMS", "50")
    max_output_lines = os.getenv("DEFAULT_MAX_OUTPUT_LINES", "100")
    reserve_response_tokes = os.getenv("DEFAULT_RESERVE_RESPONSE_TOKES", "1000")

    return Settings(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=timeout,
        max_context_tokens=max_context_tokens,
        max_history_messages=max_history_messages,
        max_tool_output_chars=max_tool_output_chars,
        max_file_size=max_file_size,
        max_file_list_items=max_file_list_items,
        max_output_lines=max_output_lines,
        reserve_response_tokes=reserve_response_tokes,
    )