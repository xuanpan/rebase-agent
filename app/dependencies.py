"""
Dependency injection setup for FastAPI application.

Provides dependency injection for core components including LLM clients,
transformation engine, and other services.
"""

from functools import lru_cache
from typing import Optional
from loguru import logger

from .config import Settings, get_settings
from core.llm_client import LLMClient
from core.context_manager import ContextManager
from core.conversation.chat_engine import ChatEngine
from domains.domain_registry import DomainRegistry


# Redis removed for POC simplicity - using file-based session storage
# def get_redis_client(settings: Settings = None) -> Optional[redis.Redis]:
#     """Get Redis client for session management."""
#     return None


@lru_cache()
def get_llm_client() -> LLMClient:
    """Get configured LLM client."""
    settings = get_settings()
    
    return LLMClient(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key
    )


# Prompt engine removed - using inline prompts in ChatEngine now


@lru_cache() 
def get_context_manager() -> ContextManager:
    """Get configured context manager."""
    # Using file-based storage only for POC simplicity
    return ContextManager()


# QuestionEngine simplified - functionality moved to ChatEngine


@lru_cache()
def get_domain_registry() -> DomainRegistry:
    """Get configured domain registry with auto-discovered domains."""
    return DomainRegistry()


# TransformationEngine simplified - functionality moved to ChatEngine


@lru_cache()
def get_chat_engine() -> ChatEngine:
    """Get configured unified chat engine."""
    # The unified ChatEngine handles all functionality internally
    return ChatEngine(
        llm_client=get_llm_client(),
        context_manager=get_context_manager()
    )


# Enhanced functionality is now unified in the main ChatEngine


# Health check dependencies
async def check_llm_health() -> dict:
    """Check health of LLM providers."""
    try:
        llm_client = get_llm_client()
        return await llm_client.health_check()
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {"error": str(e)}


async def check_redis_health() -> dict:
    """Redis removed for POC simplicity.""" 
    return {"redis": False, "reason": "not_configured_for_poc"}


async def check_domain_health() -> dict:
    """Check domain registry health."""
    try:
        registry = get_domain_registry()
        domains = registry.list_domains()
        validation_results = registry.validate_all_domains()
        
        return {
            "domains_registered": len(domains),
            "domains": domains,
            "validation_results": validation_results
        }
    except Exception as e:
        logger.error(f"Domain health check failed: {e}")
        return {"error": str(e)}