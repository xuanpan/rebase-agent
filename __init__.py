"""
Rebase Agent - AI Intelligence Layer

This package provides AI-powered automation for transformation workflows,
supporting business-focused analysis and ROI calculation for various
transformation types including modernization, framework migration,
language conversion, performance optimization, and architecture redesign.
"""

__version__ = "0.1.0"
__author__ = "Rebase Team"
__email__ = "team@rebase.com"

# Core exports
from .core.conversation.chat_engine import ChatEngine
from .domains.base_domain import TransformationDomain

__all__ = [
    "ChatEngine", 
    "TransformationDomain",
]