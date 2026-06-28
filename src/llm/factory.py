"""
LLM Client Factory
==================

Provides a unified client creation interface, returning the corresponding implementation based on provider name.
"""

from typing import Dict, Type
from .base import BaseLLMClient, LLMConfig
from .openai_client import OpenAIClient
from .deepseek_client import DeepSeekClient
from .claude_client import ClaudeClient
from .qwen_client import QwenClient
from .gemini_client import GeminiClient
from .kimi_client import KimiClient
from .minimax_client import MiniMaxClient
from .glm_client import GLMClient
from .openrouter_client import OpenRouterClient


# Register all supported providers
PROVIDERS: Dict[str, Type[BaseLLMClient]] = {
    "openai": OpenAIClient,
    "deepseek": DeepSeekClient,
    "claude": ClaudeClient,
    "qwen": QwenClient,
    "gemini": GeminiClient,
    "kimi": KimiClient,
    "minimax": MiniMaxClient,
    "glm": GLMClient,
    "openrouter": OpenRouterClient
}


def create_client(provider: str, config: LLMConfig) -> BaseLLMClient:
    """
    Factory method: create the corresponding client based on provider

    Args:
        provider: Provider name (openai, deepseek, claude, qwen, gemini, kimi, minimax, glm)
        config: LLM configuration

    Returns:
        The corresponding LLM client instance

    Raises:
        ValueError: Unsupported provider

    Example:
        >>> config = LLMConfig(api_key="sk-xxx")
        >>> client = create_client("deepseek", config)
        >>> response = client.chat("You are helpful", "Hello!")
        >>> print(response.content)
    """
    provider_lower = provider.lower()
    
    client_class = PROVIDERS.get(provider_lower)
    if not client_class:
        supported = ", ".join(PROVIDERS.keys())
        raise ValueError(
            f"Unsupported provider: '{provider}'. "
            f"Supported providers: {supported}"
        )
    
    return client_class(config)


def get_supported_providers() -> list:
    """Get list of all supported providers"""
    return list(PROVIDERS.keys())


def register_provider(name: str, client_class: Type[BaseLLMClient]):
    """
    Register a custom provider

    Args:
        name: Provider name
        client_class: Client class (must inherit from BaseLLMClient)
    """
    if not issubclass(client_class, BaseLLMClient):
        raise TypeError("client_class must be a subclass of BaseLLMClient")
    
    PROVIDERS[name.lower()] = client_class
