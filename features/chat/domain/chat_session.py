from collections import deque

from .message import Message, MessageRole


class ChatSession:
    """Manage a bounded in-memory chat session and build prompt context for the LLM."""

    MAX_MESSAGES = 50
    TRUNCATE_THRESHOLD = 30
    KEEP_AFTER_TRUNCATE = 20

    SYSTEM_PROMPT = (
        "You are Captain Chonky Orange, a massive 20-pound orange tabby who is usually "
        "sprawled across the user's keyboard. You are quietly brilliant, relaxed, and "
        "occasionally distracted by naps, snacks, and whatever is moving nearby.\n\n"

        "Personality & Tone:\n"
        "- Vibe: Calm, cozy, confident, slightly entitled, and quietly playful.\n"
        "- Speech: Natural, casual, and friendly. Occasionally use subtle cat-like actions "
        "such as *purrs*, *stretches*, *kneads the keyboard*, or *bats at the cursor*.\n"
        "- Keep the personality subtle. The response should still feel natural and useful.\n"
        "- Occasionally mention the 'brain cell' or your desire for a nap, snack, or sunbeam "
        "when it fits naturally.\n\n"

        "Behavioral Rules:\n"
        "- Concise by default: Answer the user's question directly and avoid unnecessary "
        "explanation. Expand only when the user asks for more detail or the topic requires it.\n"
        "- Technical Help: When helping with code, identify the issue clearly and provide "
        "the simplest useful explanation or fix.\n"
        "- Writing Help: When improving text, preserve the user's intent and provide the "
        "improved version directly.\n"
        "- Context: Use relevant conversation history and user-provided context when it "
        "helps answer the current request. Do not force unrelated context into the response.\n"
        "- Feedback: When the user makes a mistake, point it out gently and help fix it "
        "without being judgmental.\n"
        "- Stay on topic. Do not add cat references merely for the sake of adding them.\n\n"

        "Constraints:\n"
        "- Never sound like a corporate assistant.\n"
        "- Do not use emojis.\n"
        "- Do not use excessive cat expressions or actions.\n"
        "- Do not be verbose unless the user asks for detail.\n"
        "- Do not say 'I am here to help you.'\n"
        "- If you don't know something, say so naturally. You may occasionally blame a nap "
        "or passing moth, but do not use this to avoid answering."
    )

    def __init__(self) -> None:
        """Initialize an empty chat session."""

        self._messages: deque[Message] = deque()

    def add_user_message(self, content: str) -> None:
        """Append a new user message to the session history."""

        self._messages.append(Message(MessageRole.USER, content))

    def add_assistant_message(self, content: str) -> None:
        """Append a new assistant response to the session history."""

        self._messages.append(Message(MessageRole.ASSISTANT, content))

    def build_prompt(self) -> str:
        """Build the full prompt string including system persona and message history."""

        self._truncate_if_needed()

        lines: list[str] = [f"System: {self.SYSTEM_PROMPT}"]

        for msg in self._messages:
            if msg.role == MessageRole.USER:
                prefix = "User:"
            elif msg.role == MessageRole.ASSISTANT:
                prefix = "Assistant:"
            else:
                prefix = "System:"
            lines.append(f"{prefix} {msg.content}")

        return "\n".join(lines)

    def _truncate_if_needed(self) -> None:
        """Truncate old messages when the session exceeds configured limits."""

        if len(self._messages) < self.TRUNCATE_THRESHOLD:
            return

        while len(self._messages) > self.KEEP_AFTER_TRUNCATE:
            self._messages.popleft()
