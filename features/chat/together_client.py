from typing import Any

from together import Together

from utils.config_parser import ConfigParser


class TogetherClient:
    """Handles AI-powered autocomplete using Together AI's Python SDK."""

    def __init__(self):
        """Initialize the TogetherAI client with the API key from config."""
        self.api_key = ConfigParser.get("together_api_key")
        self.client = Together(api_key=self.api_key) if self.api_key else None


def get_response(user_message: str) -> str:
    """Fetches a code completion suggestion from Together AI."""
    ai = TogetherClient()
    if not ai.client:
        return "Together API key is not set. Please configure it in $HOME/.config/catnip/config.json"
    try:
        response: Any = ai.client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",  # Choose best model for code
            messages=[
                {"role": "system",
                 "content": "You are a concise assistant, cat vibe."},
                {"role": "user", "content": user_message}
            ], )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error while fetching response: {e}"
