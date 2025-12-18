import pytest
from unittest.mock import patch, MagicMock
import os

import agentic_hustler


@patch('agentic_hustler.llm.AsyncOpenAI')
def test_universal_llm_init_with_openrouter_defaults(mock_async_openai):
    """
    Tests that UniversalLLM initializes with OpenRouter defaults
    when no arguments are provided.
    """
    # Mock the environment variable
    fake_api_key = "sk-or-v1-fake-key"
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": fake_api_key}):
        # Instantiate the adapter
        llm = agentic_hustler.UniversalLLM()

    # Assert AsyncOpenAI was called with the correct default arguments
    mock_async_openai.assert_called_once_with(
        api_key=fake_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    assert llm.client is mock_async_openai.return_value


@patch('agentic_hustler.llm.AsyncOpenAI')
def test_universal_llm_init_with_custom_settings(mock_async_openai):
    """
    Tests that UniversalLLM can be initialized with custom settings.
    """
    custom_api_key = "ollama-custom-key"
    custom_base_url = "http://localhost:11434/v1"

    # Instantiate the adapter with custom settings
    llm = agentic_hustler.UniversalLLM(
        api_key=custom_api_key,
        base_url=custom_base_url
    )

    # Assert AsyncOpenAI was called with the custom arguments
    mock_async_openai.assert_called_once_with(
        api_key=custom_api_key,
        base_url=custom_base_url
    )
    assert llm.client is mock_async_openai.return_value


@patch('agentic_hustler.llm.AsyncOpenAI')
def test_universal_llm_init_raises_error_without_api_key(mock_async_openai):
    """
    Tests that UniversalLLM raises a ValueError if no API key is provided
    and none is found in the environment.
    """
    # Ensure the environment variable is not set
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OpenRouter API key not found"):
            agentic_hustler.UniversalLLM()

    # Assert that the client was never initialized
    mock_async_openai.assert_not_called()


@patch('agentic_hustler.llm.AsyncOpenAI')
async def test_universal_llm_acreate_proxies_call(mock_async_openai):
    """
    Tests that the acreate method correctly proxies the call to the
    internal OpenAI client.
    """
    # Setup
    fake_api_key = "sk-or-v1-fake-key"
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": fake_api_key}):
        llm = agentic_hustler.UniversalLLM()

    # Mock the chat completions create method
    mock_create = MagicMock()
    mock_completion = MagicMock()
    mock_create.return_value = mock_completion
    llm.client.chat.completions.create = mock_create

    # Define test arguments
    messages = [{"role": "user", "content": "Hello"}]
    model = "google/gemini-pro"
    temperature = 0.7

    # Call acreate
    result = await llm.acreate(messages=messages, model=model, temperature=temperature)

    # Assert the underlying client was called correctly
    mock_create.assert_called_once_with(messages=messages, model=model, temperature=temperature)

    # Assert the result is the mocked completion object
    assert result is mock_completion
