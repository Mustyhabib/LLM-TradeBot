"""
LLM Module
==========

Provides a unified multi-LLM provider interface.

Supported providers:
- OpenAI (GPT-4, GPT-3.5)
- DeepSeek (deepseek-chat, deepseek-coder)
- Claude (Anthropic)
- Qwen (Tongyi Qianwen)
- Gemini (Google)
- Kimi (Moonshot)
- MiniMax
- GLM (Zhipu)
- OpenRouter (Owl-alpha)

Usage example:

    from src.llm import create_client, LLMConfig

    # Create DeepSeek client
    config = LLMConfig(api_key="sk-xxx", model="deepseek-chat")
    client = create_client("deepseek", config)

    # Send request
    response = client.chat(
        system_prompt="You are a helpful assistant",
        user_prompt="Hello!"
    )
    print(response.content)
"""

from .base import LLMConfig, BaseLLMClient, ChatMessage, LLMResponse
from .factory import create_client, get_supported_providers, register_provider

# 导出具体客户端类（便于类型检查和直接实例化）
from .openai_client import OpenAIClient
from .deepseek_client import DeepSeekClient
from .claude_client import ClaudeClient
from .qwen_client import QwenClient
from .gemini_client import GeminiClient
from .kimi_client import KimiClient
from .minimax_client import MiniMaxClient
from .glm_client import GLMClient
from .openrouter_client import OpenRouterClient

__all__ = [
    # Core interfaces
    "LLMConfig",
    "BaseLLMClient",
    "ChatMessage",
    "LLMResponse",
    "create_client",
    "get_supported_providers",
    "register_provider",
    # Concrete clients
    "OpenAIClient",
    "OpenRouterClient",
    "DeepSeekClient",
    "ClaudeClient",
    "QwenClient",
    "GeminiClient",
    "KimiClient",
    "MiniMaxClient",
    "GLMClient",
]
