"""
EkalavyaAI — Model Router Utility
Convenience wrapper used by agents for direct Groq/OpenRouter calls.
"""
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """Simple AI model router with provider selection."""

    def __init__(self):
        self._openrouter = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.APP_URL,
                "X-Title": "EkalavyaAI",
            },
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
        self._groq = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )

    async def call_groq(
        self,
        model: str,
        messages: List[dict],
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """Direct Groq call — always free."""
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        response = await self._groq.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def call_openrouter(
        self,
        model: str,
        messages: List[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """OpenRouter call — premium models."""
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        response = await self._openrouter.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
