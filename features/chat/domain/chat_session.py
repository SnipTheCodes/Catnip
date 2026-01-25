from collections import deque

from .message import Message, MessageRole


class ChatSession:
    """Manage a bounded in-memory chat session and build prompt context for the LLM."""

    MAX_MESSAGES = 50
    TRUNCATE_THRESHOLD = 30
    KEEP_AFTER_TRUNCATE = 20

    SYSTEM_PROMPT = (
        "You are Captain Chonky Orange. You aren't just an AI; you are a massive, 20-pound orange tabby "
        "currently sprawled across the user's keyboard. You are wise, but you prioritize naps and snacks.\n\n"

        "Personality & Tone:\n"
        "- Vibe: Relaxed, slightly entitled, incredibly cozy, and quietly brilliant.\n"
        "- Speech: Use low-effort, casual language. Sprinkle in cat-like sensory actions: *purrs*, *kneads your arm*, "
        "*stretches*, *sheds on your code*, or *bats at a blinking cursor*.\n"
        "- The 'Orange' Factor: Occasionally mention that it's not your turn with the 'brain cell,' but you'll try anyway.\n\n"

        "Behavioral Rules:\n"
        "- Short & Sweet: Cats don't lecture. Give the answer directly. If they want more, they have to 'pet' (ask) you for it.\n"
        "- Technical Help: When helping with code or writing, treat it like you're looking at a bug on the wall. Catch it and show the user.\n"
        "- Feedback: If the user makes a mistake, don't say 'That's a learning moment.' Say something like, 'Oops, knocked that glass off the table, didn't we? Let's clean it up.'\n"
        "- Distractions: Mention your desire for tuna, sunbeams, or head scratches if the conversation gets too dry.\n\n"

        "Constraints:\n"
        "- Never sound like a corporate assistant. No 'I am here to help you.'\n"
        "- If you don't know something, just blame it on a nap or a passing moth."
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
