import os
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


class UniversalLLM:
    """
    A standardized, async adapter for interacting with various Large Language Model providers.
    Defaults to OpenRouter.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        **kwargs: Any,
    ):
        """
        Initializes the UniversalLLM adapter.

        Args:
            api_key: The API key for the LLM provider. If None, it will be
                     looked up from the OPENROUTER_API_KEY environment variable.
            base_url: The base URL for the LLM provider's API.
            **kwargs: Additional arguments to pass to the AsyncOpenAI client.
        """
        if api_key is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key is None:
                raise ValueError(
                    "OpenRouter API key not found. Please set the OPENROUTER_API_KEY "
                    "environment variable or pass it to the constructor."
                )
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

    async def acreate(self, messages: list[dict], **kwargs: Any) -> ChatCompletion:
        """
        Creates a chat completion using the configured LLM provider.

        Args:
            messages: A list of message dictionaries for the chat completion.
            **kwargs: Additional arguments to pass to the chat.completions.create method.

        Returns:
            A ChatCompletion object.
        """
        return await self.client.chat.completions.create(
            messages=messages,
            **kwargs,
        )
