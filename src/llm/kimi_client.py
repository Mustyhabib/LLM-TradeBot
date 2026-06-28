"""
Kimi Client Implementation
==========================

Kimi (Moonshot AI) uses an OpenAI-compatible API.
"""

from .openai_client import OpenAIClient


class KimiClient(OpenAIClient):
    """
    Kimi client

    Uses the OpenAI-compatible interface of the Moonshot platform.
    """

    DEFAULT_BASE_URL = "https://api.moonshot.ai/v1"
    DEFAULT_MODEL = "moonshot-v1-8k"
    PROVIDER = "kimi"
