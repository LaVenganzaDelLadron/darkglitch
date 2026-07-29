#app/core/pipeline/router.py
from __future__ import annotations
from app.core.pipeline.route import Route


class Router:

    def route(self, user_input: str) -> Route:

        text = user_input.lower()

        if "security" in text:
            return Route(
                task="security",
                prompts="security",
            )

        if "planner" in text:
            return Route(
                task="planner",
                prompts="planner",
            )

        if "review" in text:
            return Route(
                task="review",
                prompts="code_review",
            )

        if "debug" in text:
            return Route(
                task="debug",
                prompts="debugging",
            )

        if "document" in text:
            return Route(
                task="documentation",
                prompts="documentation",
            )

        return Route(
            task="chat",
            prompts="chat",
        )