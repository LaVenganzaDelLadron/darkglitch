#app/core/ai/factory.py
from app.core.config.settings import Settings, get_settings
from app.core.ai.base import LLMProvider
from app.core.ai.groq import GroqProvider


class LLMFactory:
    _providers = {
        "groq": GroqProvider
    }

    @classmethod
    def create(cls, provider: str = "groq") -> LLMProvider:
        provider = provider.lower()

        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")

        settings = get_settings()

        return cls._providers[provider](
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            timeout=settings.timeout,
        )