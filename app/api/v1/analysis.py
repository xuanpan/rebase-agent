"""
Analysis API - Technical analysis and domain information endpoints.

Provides endpoints for domain information, technical analysis capabilities,
and system health checks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel
from loguru import logger

from domains.domain_registry import DomainRegistry
from app.dependencies import (
    get_domain_registry, 
    check_llm_health,
    check_redis_health, 
    check_domain_health
)


router = APIRouter(prefix="/analysis")


@router.get("/domains")
async def list_domains(
    registry: DomainRegistry = Depends(get_domain_registry)
):
    """List all available transformation domains."""
    try:
        domains = registry.list_domains()
        domain_info = []
        
        for domain_name in domains:
            info = registry.get_domain_info(domain_name)
            if info:
                domain_info.append(info)
        
        return {
            "domains": domain_info,
            "total_count": len(domains)
        }
        
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list domains: {str(e)}"
        )


@router.get("/domains/{domain_name}")
async def get_domain_info(
    domain_name: str,
    registry: DomainRegistry = Depends(get_domain_registry)
):
    """Get detailed information about a specific domain."""
    try:
        info = registry.get_domain_info(domain_name)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain not found: {domain_name}"
            )
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get domain info: {str(e)}"
        )


@router.post("/domains/detect")
async def detect_domain(
    request: Dict[str, str],
    registry: DomainRegistry = Depends(get_domain_registry)
):
    """Auto-detect appropriate domain for a transformation request."""
    try:
        user_request = request.get("description", "")
        if not user_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description is required"
            )
        
        # Get domain suggestions
        suggestions = registry.suggest_domains(user_request, limit=3)
        
        # Get best match
        best_domain = await registry.auto_detect_domain(user_request)
        
        return {
            "best_match": {
                "domain": best_domain.get_domain_name(),
                "description": best_domain.get_domain_description(),
                "confidence": suggestions[0][1] if suggestions else 0.0
            },
            "suggestions": [
                {
                    "domain": domain_name,
                    "confidence": score,
                    "info": registry.get_domain_info(domain_name)
                }
                for domain_name, score in suggestions
            ],
            "user_request": user_request
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect domain: {str(e)}"
        )


@router.get("/health/comprehensive")
async def comprehensive_health_check():
    """Comprehensive health check for all system components."""
    try:
        health_results = {
            "llm": await check_llm_health(),
            "redis": await check_redis_health(),
            "domains": await check_domain_health()
        }
        
        # Determine overall health
        all_healthy = True
        for component, status in health_results.items():
            if isinstance(status, dict):
                if "error" in status:
                    all_healthy = False
                elif component == "llm":
                    # Check if at least one LLM provider is healthy
                    provider_healthy = any(
                        v for k, v in status.items() 
                        if k in ["openai", "anthropic"] and isinstance(v, bool)
                    )
                    if not provider_healthy:
                        all_healthy = False
        
        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "components": health_results,
            "timestamp": "2024-11-08T12:00:00Z"  # In real app, use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive health check: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": "2024-11-08T12:00:00Z"
        }


@router.get("/health")
async def analysis_health_check():
    """Health check for analysis functionality."""
    return {
        "status": "healthy",
        "service": "analysis_api",
        "endpoints": [
            "/analysis/domains",
            "/analysis/domains/{domain_name}",
            "/analysis/domains/detect",
            "/analysis/health/comprehensive"
        ]
    }