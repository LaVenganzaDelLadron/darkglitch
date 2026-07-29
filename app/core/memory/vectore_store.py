#app/core/memory/vector_store.py
from __future__ import annotations
from abc import ABC, abstractmethod

class VectorStore(ABC):
    @abstractmethod
    def add(self, document_id: str, embedding: list[float], metadata: dict):
        pass

    @abstractmethod
    def search(self, embedding: list[float], limit: int = 5):
        pass

    @abstractmethod
    def delete(self, document_id: str):
        pass

    @abstractmethod
    def clear(self):
        pass