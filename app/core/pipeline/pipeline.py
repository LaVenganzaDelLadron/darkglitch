#app/core/pipeline/pipeline.py
from __future__ import annotations
from app.core.pipeline.context import PipelineContext
from app.core.pipeline.router import Router
from app.core.pipeline.executor import Executor
from app.core.config.prompt import PromptLoader
from app.tools.registry import ToolRegistry


class Pipeline:

    def __init__(self, context: PipelineContext, registry: ToolRegistry | None = None):
        self.context = context
        self.router = Router()
        self.executor = Executor(registry=registry)

    def run(self, prompt: str):

        route = self.router.route(prompt)

        # Dynamically load the prompt template based on the user's intent
        system_prompt = PromptLoader.load(route.prompts)

        return self.executor.execute(
            task=route.task,
            prompt=prompt,
            prompts=route.prompts,
            context=self.context,
            system_prompt=system_prompt,
        )