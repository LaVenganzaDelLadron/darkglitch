#app/core/memory/embedding.py
from __future__ import annotations
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass