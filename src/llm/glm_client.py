"""
GLM Client Implementation
=========================

Zhipu GLM uses an OpenAI-compatible API.
"""

from .openai_client import OpenAIClient


class GLMClient(OpenAIClient):
    """
    GLM client

    Uses the OpenAI-compatible interface of the Zhipu Open Platform.
    """

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_MODEL = "glm-4-flash"
    PROVIDER = "glm"
