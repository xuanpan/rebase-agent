"""
Core AI infrastructure for Rebase Agent.

This module provides the foundational AI components for transformation
analysis including LLM clients, context management, and unified
conversation engine for simplified architecture.
"""

from .llm_client import LLMClient
from .context_manager import ContextManager

__all__ = [
    "LLMClient",
    "ContextManager",
]