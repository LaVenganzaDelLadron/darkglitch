# app/core/pipeline/context_builder.py
"""
Context Builder for LLM requests.

Builds the message list in the correct order:
1. System prompt (single, no duplicates)
2. Recent conversation (trimmed to token budget)
3. Compressed tool outputs
4. Current user message

Ensures only necessary information is sent to the LLM.
"""
from __future__ import annotations

from app.core.models.message import Message
from app.core.memory.conversation import ConversationMemory


# Rough token estimation
_CHARS_PER_TOKEN = 4


def _estimate_tokens_for_messages(messages: list[Message]) -> int:
    """Estimate total tokens for a list of messages."""
    total = 0
    for msg in messages:
        total += len(msg.content) // _CHARS_PER_TOKEN + 1
        total += 4  # overhead per message
        if msg.tool_calls:
            for tc in msg.tool_calls:
                total += len(str(tc)) // _CHARS_PER_TOKEN + 1
        if msg.tool_call_id:
            total += len(msg.tool_call_id) // _CHARS_PER_TOKEN + 1
    return total


def build_messages(
    system_prompt: str | None,
    conversation: ConversationMemory | None,
    current_user_message: str,
    max_context_tokens: int = 6000,
    reserve_tokens: int = 1000,
) -> list[dict]:
    """Build the final message list for an LLM request.

    Order:
    1. System prompt (if provided, only once)
    2. Conversation history (trimmed to fit token budget)
    3. Current user message

    Args:
        system_prompt: System-level instructions for the LLM.
        conversation: Conversation memory with previous messages.
        current_user_message: The latest user input to send.
        max_context_tokens: Maximum total context tokens allowed.
        reserve_tokens: Tokens reserved for the LLM response.

    Returns:
        List of message dicts ready for the LLM API.
    """
    messages: list[dict] = []

    # 1. System prompt (single, never duplicated)
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt,
        })

    # 2. Conversation history — trim to fit token budget
    if conversation and len(conversation) > 0:
        # Calculate remaining budget after system prompt
        system_tokens = _estimate_tokens_for_messages(
            [Message(role="system", content=system_prompt or "")]
        )
        available_for_history = max_context_tokens - reserve_tokens - system_tokens

        # Get trimmed messages from conversation memory
        trimmed = conversation.trim_to_fit(
            max_tokens=available_for_history,
            reserve_tokens=0,  # Already accounted for
        )

        for msg in trimmed:
            # Skip any stale system messages (we prepend fresh one above)
            if msg.role == "system":
                continue
            messages.append(msg.to_dict())

    # 3. Current user message (always last)
    messages.append({
        "role": "user",
        "content": current_user_message,
    })

    return messages