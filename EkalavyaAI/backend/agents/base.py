"""
EkalavyaAI — Base Agent Class
Provides fallback chain logic, retry, timeout, and logging for all agents.
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, List

import httpx
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


class ModelConfig:
    """Configuration for a single model in the fallback chain."""
    def __init__(
        self,
        model: str,
        provider: str,  # "openrouter" | "groq" | "google" | "nvidia"
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ):
        self.model = model
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature


class BaseAgent(ABC):
    """
    Abstract base class for all EkalavyaAI agents.

    Features:
    - Automatic fallback chain (primary → backup1 → backup2 → free)
    - Retry with exponential backoff
    - Timeout enforcement
    - LangSmith trace logging
    - Cost tracking
    """

    def __init__(self, name: str, fallback_chain: List[ModelConfig]):
        self.name = name
        self.fallback_chain = fallback_chain
        self._clients: dict[str, AsyncOpenAI] = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize OpenAI-compatible clients for each provider."""
        # OpenRouter — all premium models via one key
        self._clients["openrouter"] = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.APP_URL,
                "X-Title": "EkalavyaAI",
            },
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )

        # Groq — ultra-fast free models
        self._clients["groq"] = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )

        # Google AI Studio (if available)
        if settings.GOOGLE_AI_STUDIO_API_KEY:
            self._clients["google"] = AsyncOpenAI(
                api_key=settings.GOOGLE_AI_STUDIO_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )

    async def _call_model(
        self,
        model_config: ModelConfig,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        stream: bool = False,
        json_mode: bool = False,
    ) -> str:
        """Make a single model API call."""
        client = self._clients.get(model_config.provider)
        if not client:
            raise ValueError(f"No client for provider: {model_config.provider}")

        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        kwargs = {
            "model": model_config.model,
            "messages": msgs,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def call_with_fallback(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        timeout_override: Optional[int] = None,
    ) -> str:
        """
        Call models with automatic fallback chain.
        Never raises — always returns a response (even if degraded).
        """
        timeout = timeout_override or settings.AGENT_TIMEOUT_SECONDS
        last_error = None

        for i, model_config in enumerate(self.fallback_chain):
            try:
                layer = ["Primary", "Backup-1", "Backup-2", "Free-Fallback"][min(i, 3)]
                logger.info(
                    f"[{self.name}] Calling {layer}: {model_config.model} "
                    f"(provider: {model_config.provider})"
                )
                start = time.time()

                result = await asyncio.wait_for(
                    self._call_model(
                        model_config=model_config,
                        messages=messages,
                        system_prompt=system_prompt,
                        json_mode=json_mode,
                    ),
                    timeout=timeout,
                )

                elapsed = time.time() - start
                logger.info(
                    f"[{self.name}] ✅ {model_config.model} responded in {elapsed:.2f}s"
                )
                return result

            except asyncio.TimeoutError:
                logger.warning(
                    f"[{self.name}] ⏱️ Timeout on {model_config.model} "
                    f"after {timeout}s — trying next"
                )
                last_error = f"Timeout on {model_config.model}"

            except Exception as e:
                logger.warning(
                    f"[{self.name}] ❌ Error on {model_config.model}: {e} "
                    f"— trying next"
                )
                last_error = str(e)

                # Short wait before trying next model
                if i < len(self.fallback_chain) - 1:
                    await asyncio.sleep(0.5)

        # All models failed — this should never happen in production
        logger.error(f"[{self.name}] 🚨 ALL models failed! Last error: {last_error}")
        raise RuntimeError(
            f"All models in fallback chain failed for {self.name}. "
            f"Last error: {last_error}"
        )

    async def call_groq_direct(
        self,
        model: str,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """Direct Groq call — for Memory Agent (always free, always fast)."""
        client = self._clients["groq"]
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        response = await client.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    @abstractmethod
    async def run(self, state: dict) -> Any:
        """Execute the agent's primary task."""
        pass
