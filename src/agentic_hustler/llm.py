import os
from openai import AsyncOpenAI
from typing import List, Dict

class UniversalLLM:
    def __init__(self, provider="openrouter"):
        self.provider = provider
        self.api_key = self._get_key(provider)
        self.base_url = self._get_url(provider)
        
        self.headers = None
        if provider == "openrouter":
            self.headers = {
                "HTTP-Referer": "https://localhost",
                "X-Title": "AgenticHustler",
            }

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.headers
        )

    def _get_url(self, provider):
        if provider == "openrouter": return "https://openrouter.ai/api/v1"
        if provider == "openai": return "https://api.openai.com/v1"
        if provider == "ollama": return "http://localhost:11434/v1"
        return os.getenv("CUSTOM_LLM_URL")

    def _get_key(self, provider):
        if provider == "ollama": return "ollama"
        if provider == "openrouter": return os.getenv("OPENROUTER_API_KEY")
        return os.getenv(f"{provider.upper()}_API_KEY")

    async def chat(self, messages: List[Dict], model: str, temperature=0.7):
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise e
