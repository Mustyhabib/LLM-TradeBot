"""
DeepSeek Client Implementation
==============================

DeepSeek uses an OpenAI-compatible API, only the default configuration needs to be modified.
"""

from .openai_client import OpenAIClient


class DeepSeekClient(OpenAIClient):
    """
    DeepSeek client

    Inherits from OpenAI client, uses OpenAI-compatible API.
    """
    
    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"
    PROVIDER = "deepseek"
