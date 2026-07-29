# app/core/models/usage.py
from dataclasses import dataclass

@dataclass(slots=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0