"""
Transformations API - Direct transformation analysis endpoints.

Provides structured API endpoints for transformation analysis,
business case generation, and implementation planning.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from loguru import logger

from core.transformation_engine import UniversalTransformationEngine, TransformationResult
from app.dependencies import get_transformation_engine


router = APIRouter(prefix="/transformations")


class TransformationRequest(BaseModel):
    description: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class BusinessCaseResponse(BaseModel):
    total_investment: float
    annual_benefits: float
    roi_percentage: float
    payback_period_months: float
    confidence_level: float
    recommendation: str
    cost_breakdown: List[Dict[str, Any]]
    benefits_breakdown: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]


@router.post("/analyze")
async def analyze_transformation(
    request: TransformationRequest,
    engine: UniversalTransformationEngine = Depends(get_transformation_engine)
):
    """Start a new transformation analysis (non-conversational)."""
    try:
        session_id = await engine.start_transformation_analysis(
            user_request=request.description,
            user_id=request.user_id
        )
        
        return {
            "session_id": session_id,
            "message": "Transformation analysis started",
            "next_step": "Use /chat/message to continue with conversational analysis"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing transformation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze transformation: {str(e)}"
        )


@router.get("/sessions/{session_id}/status")
async def get_transformation_status(
    session_id: str,
    engine: UniversalTransformationEngine = Depends(get_transformation_engine)
):
    """Get current status of transformation analysis."""
    try:
        result = await engine.get_transformation_status(session_id)
        
        return {
            "session_id": result.session_id,
            "domain_type": result.domain_type,
            "current_phase": result.current_phase.value,
            "completion_percentage": result.completion_percentage,
            "discovery_summary": result.discovery_summary,
            "technical_assessment": result.technical_assessment,
            "business_case": result.business_case,
            "implementation_plan": result.implementation_plan
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting transformation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transformation status: {str(e)}"
        )


@router.post("/sessions/{session_id}/force-phase/{phase}")
async def force_phase_transition(
    session_id: str,
    phase: str,
    engine: UniversalTransformationEngine = Depends(get_transformation_engine)
):
    """Force transition to a specific phase (admin/testing endpoint)."""
    try:
        from core.transformation_engine import TransformationPhase
        
        target_phase = TransformationPhase(phase.lower())
        success = await engine.force_phase_transition(session_id, target_phase)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to transition phase"
            )
        
        return {
            "session_id": session_id,
            "new_phase": phase,
            "message": f"Successfully transitioned to {phase}"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid phase: {phase}"
        )
    except Exception as e:
        logger.error(f"Error forcing phase transition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force phase transition: {str(e)}"
        )


@router.get("/detect-domain")
async def detect_transformation_domain(
    description: str,
    engine: UniversalTransformationEngine = Depends(get_transformation_engine)
):
    """Detect the most likely transformation domain for a given description."""
    try:
        domain_info = await engine.detect_transformation_domain(description)
        
        return {
            "description": description,
            "detected_domain": domain_info["domain"],
            "confidence": domain_info["confidence"],
            "domain_info": domain_info["info"],
            "suggested_approach": domain_info["approach"]
        }
        
    except Exception as e:
        logger.error(f"Error detecting domain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect domain: {str(e)}"
        )


@router.get("/health")
async def transformations_health_check():
    """Health check for transformation functionality."""
    return {
        "status": "healthy",
        "service": "transformations_api",
        "endpoints": [
            "/transformations/analyze",
            "/transformations/detect-domain",
            "/transformations/sessions/{session_id}/status",
            "/transformations/sessions/{session_id}/force-phase/{phase}"
        ]
    }