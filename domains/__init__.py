"""
Transformation domains for business-focused analysis.

This module contains domain-specific implementations for different types
of transformations including modernization, framework migration, language
conversion, performance optimization, architecture redesign, and dependency upgrade.
"""

from .base_domain import TransformationDomain
from .domain_registry import DomainRegistry

__all__ = [
    "TransformationDomain",
    "DomainRegistry",
]