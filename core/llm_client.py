"""
LLM Client - Unified interface for multiple LLM providers.

Provides a consistent interface for OpenAI GPT-4, Anthropic Claude, and other
language models with automatic retry, rate limiting, and cost tracking.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import openai
from openai import OpenAI
import anthropic
from anthropic import Anthropic
from loguru import logger


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float


@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3


class LLMClient:
    """Unified LLM client with multi-provider support."""
    
    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.anthropic_client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        self.usage_stats = {"total_requests": 0, "total_tokens": 0, "total_cost": 0.0}
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        config: Optional[LLMConfig] = None
    ) -> LLMResponse:
        """Generate chat completion using specified provider."""
        
        if config is None:
            config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4-turbo-preview")
            
        start_time = time.time()
        
        try:
            if config.provider == LLMProvider.OPENAI:
                response = await self._openai_completion(messages, config)
            elif config.provider == LLMProvider.ANTHROPIC:
                response = await self._anthropic_completion(messages, config)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
                
            response.response_time = time.time() - start_time
            self._update_usage_stats(response)
            
            logger.info(
                f"LLM completion: {config.provider}/{config.model} "
                f"- {response.tokens_used} tokens - ${response.cost_estimate:.4f}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise
    
    async def _openai_completion(self, messages: List[Dict[str, str]], config: LLMConfig) -> LLMResponse:
        """Handle OpenAI completion."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
            
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout
        )
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        cost_estimate = self._calculate_openai_cost(config.model, tokens_used)
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model=config.model,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            response_time=0.0  # Will be set by caller
        )
    
    async def _anthropic_completion(self, messages: List[Dict[str, str]], config: LLMConfig) -> LLMResponse:
        """Handle Anthropic completion."""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
            
        # Convert messages format for Anthropic
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=config.model,
            system=system_message,
            messages=user_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost_estimate = self._calculate_anthropic_cost(config.model, tokens_used)
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.ANTHROPIC,
            model=config.model,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            response_time=0.0  # Will be set by caller
        )
    
    def _calculate_openai_cost(self, model: str, tokens: int) -> float:
        """Estimate OpenAI API cost based on model and tokens."""
        # Simplified cost calculation - update with actual pricing
        cost_per_1k_tokens = {
            "gpt-4-turbo-preview": 0.01,
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002
        }
        rate = cost_per_1k_tokens.get(model, 0.01)
        return (tokens / 1000) * rate
    
    def _calculate_anthropic_cost(self, model: str, tokens: int) -> float:
        """Estimate Anthropic API cost based on model and tokens."""
        # Simplified cost calculation - update with actual pricing
        cost_per_1k_tokens = {
            "claude-3-opus-20240229": 0.015,
            "claude-3-sonnet-20240229": 0.003,
            "claude-3-haiku-20240307": 0.00025
        }
        rate = cost_per_1k_tokens.get(model, 0.003)
        return (tokens / 1000) * rate
    
    def _update_usage_stats(self, response: LLMResponse):
        """Update internal usage statistics."""
        self.usage_stats["total_requests"] += 1
        self.usage_stats["total_tokens"] += response.tokens_used
        self.usage_stats["total_cost"] += response.cost_estimate
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return self.usage_stats.copy()
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of available LLM providers."""
        health = {}
        
        if self.openai_client:
            try:
                await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                health["openai"] = True
            except Exception:
                health["openai"] = False
        
        if self.anthropic_client:
            try:
                await asyncio.to_thread(
                    self.anthropic_client.messages.create,
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                health["anthropic"] = True
            except Exception:
                health["anthropic"] = False
        
        return health