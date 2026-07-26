import os
from dotenv import load_dotenv
from core.ai.base import LLMProvider

load_dotenv()

class GroqProvider(LLMProvider):
    """LLM provider backed by Groq's OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout_seconds: float | None = None,
    ):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install the OpenAI Python package to use the Groq provider: pip install openai"
            ) from exc

        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY must be set to use the Groq provider")

        timeout = timeout_seconds or float(os.getenv("GROQ_TIMEOUT", "60"))
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            timeout=timeout,
        )
        self.default_model = default_model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def generate(self, prompt: str, model: str | None = None) -> str:
        response = self.client.responses.create(
            input=prompt,
            model=model or self.default_model,
        )
        return response.output_text.strip()
