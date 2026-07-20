#core/ai/ollama/ollama_provider.py
import os
from core.ai.base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, host: str | None = None, default_model: str | None = None, timeout_seconds: int | None = None):
        try:
            from ollama import Client
        except ImportError as exc:
            print(f"[!] INSTALL THE OLLAMA PACKAGE TO USE OLLAMA PROVIDER: {exc}")

        timeout = timeout_seconds or float(os.getenv("OLLAMA_TIMEOUT", "60"))
        self.client = Client(host=host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"), timeout=timeout)
        self.default_model = default_model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def generate(self, prompt: str, model: str | None = None) -> str:
        response = self.client.generate(model=model or self.default_model, prompt=prompt)

        if isinstance(response, str):
            return response.strip()

        if isinstance(response, str):
            return response["response"].strip()

        message = response.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()

            if isinstance(response.get("content"), str):
                return response["content"].strip()

        for attr_name in ("response", "content"):
            value = getattr(response, attr_name, None)
            if isinstance(value, str):
                return value.strip()

        message = getattr(response, "message", None)
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()

        if hasattr(message, "content") and isinstance(message.content, str):
            return message.content.strip()

        return str(response).strip()
