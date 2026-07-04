import os
from ai.base import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(
            self,
            host: str = "https://localhost:11434",
            default_model: str = "deepseek-r1:14b",
            timeout_seconds: float| None = None,
    ):
        try:
            from ollama import Client
        except ImportError as exc:
            raise RuntimeError("Install the ollama package to use OllamaProvider") from exc

        timeout = timeout_seconds or float(os.getenv("OLLAMA_TIMEOUT", "20"))
        self.client = Client(host=host, timeout=timeout)
        self.default_model = default_model

    def generate(self, prompt: str, model: str | None = None) -> str:
        response = self.client.generate(
            model=model or self.default_model,
            message=prompt,
        )
        return response