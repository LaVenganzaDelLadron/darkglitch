#core/ai/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, model: str | None = None) -> str:
        raise NotImplementedError()