from collections import deque
from typing import Iterable

from .message import Message, MessageRole


class ChatSession:
    MAX_MESSAGES = 50
    TRUNCATE_THRESHOLD = 30
    KEEP_AFTER_TRUNCATE = 20

    def __init__(self) -> None:
        self._messages: deque[Message] = deque()

    def add_user_message(self, content: str) -> None:
        self._messages.append(Message(MessageRole.USER, content))

    def add_assistant_message(self, content: str) -> None:
        self._messages.append(Message(MessageRole.ASSISTANT, content))

    def clear(self) -> None:
        self._messages.clear()

    def get_messages(self) -> Iterable[Message]:
        return list(self._messages)

    def build_prompt(self) -> str:
        self._truncate_if_needed()

        lines: list[str] = []
        for msg in self._messages:
            prefix = "User:" if msg.role == MessageRole.USER else "Assistant:"
            lines.append(f"{prefix} {msg.content}")

        return "\n".join(lines)

    def _truncate_if_needed(self) -> None:
        if len(self._messages) < self.TRUNCATE_THRESHOLD:
            return

        while len(self._messages) > self.KEEP_AFTER_TRUNCATE:
            self._messages.popleft()
