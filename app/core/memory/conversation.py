#app/core/memory/conversation.py
from __future__ import annotations
from collections import deque
from app.core.models.message import Message


# Rough token estimation: ~4 chars per token for English text
_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Rough token estimation based on character count."""
    return len(text) // _CHARS_PER_TOKEN + 1


def _message_tokens(msg: Message) -> int:
    """Estimate the token count for a single message including role overhead."""
    total = _estimate_tokens(msg.content)
    # Add overhead for role, tool_call_id, and JSON structure
    total += 4  # base overhead per message
    if msg.tool_calls:
        for tc in msg.tool_calls:
            tc_str = str(tc)
            total += _estimate_tokens(tc_str)
    if msg.tool_call_id:
        total += _estimate_tokens(msg.tool_call_id)
    return total


class ConversationMemory:
    def __init__(self, max_messages: int = 20):
        self._messages: deque[Message] = deque(maxlen=max_messages)

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def add_user(self, content: str) -> None:
        self.add(
            Message(
                role="user",
                content=content,
            )
        )

    def add_assistant(self, content: str, tool_calls: list | None = None) -> None:
        self.add(
            Message(
                role="assistant",
                content=content,
                tool_calls=tool_calls or [],
            )
        )

    def add_tool(self, content: str, tool_call_id: str) -> None:
        self.add(
            Message(
                role="tool",
                content=content,
                tool_call_id=tool_call_id,
            )
        )

    def add_system(self, content: str) -> None:
        self.add(
            Message(
                role="system",
                content=content,
            )
        )

    def remove_last(self) -> None:
        if self._messages:
            self._messages.pop()

    def clear(self) -> None:
        self._messages.clear()

    def messages(self) -> list[Message]:
        return list(self._messages)

    def api_messages(self) -> list[dict]:
        return [m.to_dict() for m in self._messages]

    def estimated_tokens(self) -> int:
        """Estimate total tokens for all messages in memory."""
        return sum(_message_tokens(m) for m in self._messages)

    def trim_to_fit(self, max_tokens: int, reserve_tokens: int = 1000) -> list[Message]:
        """Remove oldest messages until the estimated token count fits within budget.

        Always keeps at least the most recent user-assistant exchange.
        Returns the trimmed list of messages (does NOT modify internal storage).
        """
        budget = max_tokens - reserve_tokens
        if budget <= 0:
            return []

        messages_list = list(self._messages)

        # Keep removing oldest messages until we fit the budget
        while len(messages_list) > 2 and sum(_message_tokens(m) for m in messages_list) > budget:
            # Remove the oldest non-system message
            removed = False
            for i, msg in enumerate(messages_list):
                if msg.role != "system":
                    messages_list.pop(i)
                    removed = True
                    break
            if not removed:
                # Only system messages left, can't remove further
                break

        return messages_list

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)