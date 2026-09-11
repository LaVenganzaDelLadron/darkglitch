from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from dotenv import load_dotenv

from app.core.ai.base import LLMProvider

load_dotenv()


@dataclass
class KeyStats:
    key: str
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    cooldown_until: float = 0.0
    last_used: float | None = None

    @property
    def healthy(self) -> bool:
        return time.monotonic() >= self.cooldown_until

    def public(self) -> dict[str, Any]:
        return {"key": f"{self.key[:4]}..." if self.key else "",
                "usage_count": self.usage_count, "success_count": self.success_count,
                "failure_count": self.failure_count, "cooldown_until": self.cooldown_until,
                "last_used": self.last_used}


class GroqKeyManager:
    def __init__(self, keys: list[str], cooldown_seconds: float = 30):
        clean = [key.strip() for key in keys if key and key.strip()]
        if not clean:
            raise ValueError("At least one Groq API key is required")
        self._keys = [KeyStats(key) for key in clean]
        self.cooldown_seconds = cooldown_seconds
        self._index = 0
        self._lock = Lock()

    @classmethod
    def from_environment(cls) -> "GroqKeyManager":
        keys = _environment_keys()
        return cls(keys)

    def acquire(self) -> KeyStats:
        with self._lock:
            for offset in range(len(self._keys)):
                index = (self._index + offset) % len(self._keys)
                candidate = self._keys[index]
                if candidate.healthy:
                    self._index = (index + 1) % len(self._keys)
                    candidate.usage_count += 1
                    candidate.last_used = time.time()
                    return candidate
        raise RuntimeError("All Groq API keys are temporarily unavailable")

    def success(self, stats: KeyStats) -> None:
        stats.success_count += 1

    def failure(self, stats: KeyStats, *, cooldown: bool = True) -> None:
        stats.failure_count += 1
        if cooldown:
            stats.cooldown_until = time.monotonic() + self.cooldown_seconds

    def status(self) -> list[dict[str, Any]]:
        return [stats.public() for stats in self._keys]


class GroqProvider(LLMProvider):
    """Groq OpenAI-compatible provider with round-robin key failover."""

    RETRYABLE_STATUS = {429, 500, 502, 503}

    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 default_model: str | None = None, timeout_seconds: float | None = None,
                 key_manager: GroqKeyManager | None = None, max_retries: int = 2):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use the Groq provider") from exc
        self._client_class = OpenAI
        if key_manager:
            self.key_manager = key_manager
        else:
            keys = [api_key] if api_key else _environment_keys()
            self.key_manager = GroqKeyManager(keys)
        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.default_model = default_model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.timeout = timeout_seconds or float(os.getenv("GROQ_TIMEOUT", "60"))
        self.max_retries = max(0, max_retries)

    def generate(self, prompt: str, model: str | None = None) -> str:
        return self.generate_messages([{"role": "user", "content": prompt}], model=model)

    def generate_messages(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            stats = self.key_manager.acquire()
            try:
                client = self._client_class(api_key=stats.key, base_url=self.base_url,
                                            timeout=self.timeout)
                response = client.chat.completions.create(
                    messages=messages, model=model or self.default_model)
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError("Groq returned an empty response")
                self.key_manager.success(stats)
                return content.strip()
            except Exception as error:
                last_error = error
                status = getattr(error, "status_code", None)
                retryable = (
                    status in self.RETRYABLE_STATUS
                    or isinstance(error, TimeoutError)
                    or "timeout" in error.__class__.__name__.lower()
                )
                self.key_manager.failure(stats, cooldown=retryable)
                if not retryable:
                    raise
                time.sleep(min(2 ** stats.failure_count, 8))
        raise RuntimeError("Groq request failed after retries") from last_error


def _environment_keys() -> list[str]:
    """Read both canonical and legacy numbered Groq key names.

    Canonical names are GROQ_API_KEY and GROQ_API_KEY_2 through _5.
    GROQ_API_KEY1 through GROQ_API_KEY5 are accepted for compatibility with
    existing .env files.
    """
    keys = [os.getenv("GROQ_API_KEY", "")]
    for index in range(2, 6):
        keys.append(os.getenv(f"GROQ_API_KEY_{index}",
                              os.getenv(f"GROQ_API_KEY{index}", "")))
    if not keys[0]:
        keys[0] = os.getenv("GROQ_API_KEY1", "")
    return keys
