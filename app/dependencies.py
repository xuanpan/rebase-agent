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
from core.prompt_engine import PromptEngine, bootstrap_default_templates
from core.context_manager import ContextManager
from core.question_engine import QuestionEngine
from core.transformation_engine import UniversalTransformationEngine
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


@lru_cache()
def get_prompt_engine(settings: Settings = None) -> PromptEngine:
    """Get configured prompt engine with default templates."""
    if settings is None:
        settings = get_settings()
    
    engine = PromptEngine()
    
    # Bootstrap default templates if they don't exist
    bootstrap_default_templates(engine)
    
    return engine


@lru_cache() 
def get_context_manager() -> ContextManager:
    """Get configured context manager."""
    # Using file-based storage only for POC simplicity
    return ContextManager()


@lru_cache()
def get_question_engine() -> QuestionEngine:
    """Get configured question engine."""
    return QuestionEngine(
        llm_client=get_llm_client(),
        prompt_engine=get_prompt_engine()
    )


@lru_cache()
def get_domain_registry() -> DomainRegistry:
    """Get configured domain registry with auto-discovered domains."""
    return DomainRegistry()


@lru_cache()
def get_transformation_engine() -> UniversalTransformationEngine:
    """Get configured universal transformation engine."""
    engine = UniversalTransformationEngine(
        llm_client=get_llm_client(),
        prompt_engine=get_prompt_engine(),
        context_manager=get_context_manager(),
        question_engine=get_question_engine()
    )
    
    # Connect domain registry
    engine.set_domain_registry(get_domain_registry())
    
    return engine


@lru_cache()
def get_chat_engine() -> ChatEngine:
    """Get configured chat engine for conversational interface."""
    return ChatEngine(
        llm_client=get_llm_client(),
        prompt_engine=get_prompt_engine(),
        context_manager=get_context_manager(), 
        question_engine=get_question_engine(),
        transformation_engine=get_transformation_engine()
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