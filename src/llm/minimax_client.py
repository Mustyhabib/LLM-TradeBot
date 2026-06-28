"""
MiniMax Client Implementation
==============================

MiniMax uses an OpenAI-compatible API.
"""

from .openai_client import OpenAIClient


class MiniMaxClient(OpenAIClient):
    """
    MiniMax client

    Uses the OpenAI-compatible interface of the MiniMax platform.
    """

    DEFAULT_BASE_URL = "https://api.minimax.io/v1"
    DEFAULT_MODEL = "MiniMax-M2.1"
    PROVIDER = "minimax"
