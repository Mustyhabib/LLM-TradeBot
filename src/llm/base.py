"""
LLM Abstract Base Class and Configuration
==========================================

Provides a unified LLM client interface supporting multiple LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import httpx
import time

from src.llm.metrics import record_error, record_request, record_success
import re


@dataclass
class LLMConfig:
    """LLM configuration dataclass"""
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    timeout: int = 120
    max_retries: int = 5
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def __post_init__(self):
        if not self.api_key:
            raise ValueError("api_key is required")


@dataclass
class ChatMessage:
    """Chat message"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict] = None


class BaseLLMClient(ABC):
    """
    LLM client abstract base class

    All LLM provider clients must inherit this class and implement the abstract methods.
    """
    
    # Default values to be overridden by subclasses
    DEFAULT_BASE_URL: str = ""
    DEFAULT_MODEL: str = ""
    PROVIDER: str = "base"
    
    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client

        Args:
            config: LLM configuration
        """
        self.config = config
        self.base_url = config.base_url or self.DEFAULT_BASE_URL
        self.model = config.model or self.DEFAULT_MODEL
        self.client = httpx.Client(timeout=config.timeout)
    
    @abstractmethod
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers (subclasses implement different auth methods)"""
        pass
    
    @abstractmethod
    def _build_request_body(
        self, 
        messages: List[ChatMessage],
        **kwargs
    ) -> Dict[str, Any]:
        """Build request body (subclasses may override for different formats)"""
        pass
    
    @abstractmethod
    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Parse response (subclasses may override for different formats)"""
        pass
    
    def _build_url(self) -> str:
        """Build request URL"""
        return f"{self.base_url}/chat/completions"
    
    def _messages_to_list(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Convert ChatMessage list to list of dicts"""
        return [{"role": m.role, "content": m.content} for m in messages]

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimator when provider usage is unavailable."""
        if not text:
            return 0
        cjk_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        non_cjk = len(text) - cjk_count
        return cjk_count + max(0, int(non_cjk / 4))

    def _estimate_prompt_tokens(self, messages: List[ChatMessage]) -> int:
        total = 0
        for msg in messages:
            total += self._estimate_tokens(msg.content)
        return total
    
    def chat(
        self, 
        system_prompt: str, 
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Unified call entry point (simplified)

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            **kwargs: Extra parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse object
        """
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        return self.chat_messages(messages, **kwargs)
    
    def chat_messages(
        self, 
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """
        Multi-turn conversation call

        Args:
            messages: List of messages
            **kwargs: Extra parameters

        Returns:
            LLMResponse object
        """
        url = self._build_url()
        headers = self._build_headers()
        body = self._build_request_body(messages, **kwargs)
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                record_request(self.PROVIDER, self.model)
                est_prompt_tokens = self._estimate_prompt_tokens(messages)
                start_ts = time.time()
                response = self.client.post(url, json=body, headers=headers)
                response.raise_for_status()
                parsed = self._parse_response(response.json())
                usage = parsed.usage or {}
                prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
                completion_tokens = int(usage.get("completion_tokens", 0) or 0)
                total_tokens = int(usage.get("total_tokens", 0) or 0)
                if total_tokens <= 0:
                    if prompt_tokens <= 0:
                        prompt_tokens = est_prompt_tokens
                    if completion_tokens <= 0:
                        completion_tokens = self._estimate_tokens(parsed.content or "")
                    total_tokens = prompt_tokens + completion_tokens
                    parsed.usage = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    }
                latency_ms = int((time.time() - start_ts) * 1000)
                record_success(self.PROVIDER, self.model, latency_ms, parsed.usage)
                return parsed
            except httpx.HTTPStatusError as e:
                last_error = e
                record_error(self.PROVIDER, self.model, f"HTTP {e.response.status_code}")
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    # Retryable HTTP errors
                    wait_time = 2 ** attempt
                    print(f"⚠️ LLM HTTP Error {e.response.status_code}, retrying in {wait_time}s (attempt {attempt + 1}/{self.config.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise
            except (httpx.ConnectError, httpx.ReadError, httpx.WriteError, 
                    ConnectionResetError, ConnectionError, OSError) as e:
                # Network connection errors, need to retry
                last_error = e
                record_error(self.PROVIDER, self.model, type(e).__name__)
                wait_time = 2 ** attempt
                print(f"⚠️ LLM Connection Error: {type(e).__name__}, retrying in {wait_time}s (attempt {attempt + 1}/{self.config.max_retries})")
                time.sleep(wait_time)
                continue
            except Exception as e:
                last_error = e
                record_error(self.PROVIDER, self.model, type(e).__name__)
                # Other unknown errors, raise after last attempt
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ LLM Unexpected Error: {type(e).__name__}: {e}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                raise
        
        raise last_error or Exception("Max retries exceeded")

    
    def close(self):
        """Close HTTP client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
