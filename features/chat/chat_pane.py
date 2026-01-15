import asyncio
from typing import Optional, Callable

from textual import events
from textual.containers import Container, VerticalScroll
from textual.widgets import (
    TabPane,
    TextArea,
    Markdown,
    LoadingIndicator,
    RichLog,
    Static,
)

from .ollama_client import OllamaClient


async def _send_message(text_log: RichLog, user_message: str):
    """Handles sending user input to LLM and displaying the response."""
    try:
        loading = LoadingIndicator()
        await text_log.mount(loading)

        buffer = ""
        response_widget = Markdown("", classes="ai-message")
        await text_log.mount(response_widget)

        first_chunk = True
        async for chunk in OllamaClient.stream_response(user_message):
            if first_chunk:
                await loading.remove()
                first_chunk = False

            buffer += chunk
            await response_widget.update(buffer)
            text_log.scroll_end(animate=False)
            await asyncio.sleep(0)

    except Exception as e:
        await text_log.mount(Static(str(e), classes="ai-message"))


class ChatPane(TabPane):
    """A chat-box for interacting with AI via Ollama."""

    def __init__(
            self,
            title: str = "Cat Me",
            tab_id: str = "cat-me",
            get_chat_log: Optional[Callable[[], RichLog]] = None,
    ):
        super().__init__(title=title, id=tab_id)
        self.text_area: Optional[TextArea] = None
        self.message = None
        self.get_chat_log = get_chat_log

    def compose(self):
        """Create the chat UI layout."""
        yield Container(
            VerticalScroll(
                RichLog(
                    id="chat-log-content",
                    highlight=True,
                    markup=True,
                    wrap=True,
                    auto_scroll=True,
                ),
                id="chat-log",
            ),
            TextArea(classes="chat-input"),
            classes="chat-pane",
        )

    def on_mount(self):
        """Ensure the text area is focused when the chat opens."""
        self.text_area = self.query_one(TextArea)
        self.text_area.focus()

    def on_key(self, event: events.Key) -> None:
        if event.key == "shift+enter":
            event.prevent_default()
            self._send_current_message()

    def _send_current_message(self):
        user_message = self.text_area.text.strip()
        if not user_message:
            return

        if not self.get_chat_log:
            return

        text_log = self.get_chat_log()
        text_log.mount(Static(user_message, classes="user-message"))

        self.text_area.clear()
        self.run_worker(_send_message(text_log, user_message))
