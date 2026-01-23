from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str
