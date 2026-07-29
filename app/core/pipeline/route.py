# app/core/pipeline/route.py
from dataclasses import dataclass

@dataclass(slots=True)
class Route:
    task: str
    prompts: str