import asyncio
from typing import Optional

from textual import events
from textual.containers import Vertical, VerticalScroll
from textual.widgets import (TabPane, TextArea, Markdown, LoadingIndicator,
                             Static)

from .domain.chat_session import ChatSession
from .ollama_client import OllamaClient


class ChatPane(TabPane):
    """A chat-box for interacting with AI via Ollama."""

    def __init__(self, title: str = "Cat Me", tab_id: str = "cat-me"):
        super().__init__(title=title, id=tab_id)
        self.text_area: Optional[TextArea] = None
        self.message = None
        self.chat_session = ChatSession()

    def compose(self):
        """Create the chat UI layout."""

        yield Vertical(
            VerticalScroll(classes="chat-log"),
            TextArea(classes="chat-input"),
            classes="chat-pane")

    def on_mount(self):
        """Ensure the text area is focused when the chat opens."""

        self.text_area = self.query_one(".chat-input")
        self.text_area.focus()

    def on_key(self, event: events.Key) -> None:
        """Submit message when user presses ctrl+enter."""

        if event.key == "ctrl+enter":
            event.prevent_default()
            text_log = self.query_one(".chat-log")
            self._send_current_message(text_log)

    async def _send_message(self, text_log: VerticalScroll):
        """Handle sending user input to LLM and displaying the response."""

        try:
            loading = LoadingIndicator()
            await text_log.mount(loading)

            buffer = ""
            response_widget = Markdown("", classes="ai-message")
            await text_log.mount(response_widget)

            first_chunk = True
            prompt = self.chat_session.build_prompt()
            async for chunk in OllamaClient.stream_response(prompt):
                if first_chunk:
                    await loading.remove()
                    first_chunk = False

                buffer += chunk
                await response_widget.update(buffer)
                text_log.scroll_end(animate=False)
                await asyncio.sleep(0)

            self.chat_session.add_assistant_message(buffer)

        except Exception as e:
            await text_log.mount(Static(str(e), classes="ai-message"))

    def _send_current_message(self, text_log: VerticalScroll):
        user_message = self.text_area.text.strip()
        if not user_message:
            return

        self.chat_session.add_user_message(user_message)

        text_log.mount(Static(user_message, classes="user-message"))

        self.text_area.clear()
        self.run_worker(self._send_message(text_log))
