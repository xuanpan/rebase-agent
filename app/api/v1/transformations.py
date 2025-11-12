"""
Transformations API - Simple transformation endpoints using unified ChatEngine.

These endpoints redirect transformation requests to use the unified chat interface.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from loguru import logger

from core.conversation.chat_engine import ChatEngine
from app.dependencies import get_chat_engine


router = APIRouter(prefix="/transformations")


class TransformationRequest(BaseModel):
    description: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class TransformationResult(BaseModel):
    session_id: str
    status: str
    message: str


@router.post("/analyze")
async def analyze_transformation(
    request: TransformationRequest,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Start a new transformation analysis using the unified chat engine."""
    try:
        # Use the unified chat engine for transformation analysis
        session_id = f"transform_{request.user_id or 'anonymous'}"
        
        # Start a conversation session with transformation focus
        response = await chat_engine.start_conversation(
            session_id=session_id,
            user_message=f"I need help with a transformation: {request.description}"
        )
        
        return {
            "session_id": session_id,
            "message": "Transformation analysis started using unified chat interface",
            "response": response.content,
            "next_step": "Use /chat/message to continue the conversation"
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
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Get current conversation status from the chat engine."""
    try:
        # Get conversation summary instead of transformation status
        summary = await chat_engine.get_conversation_summary(session_id)
        
        return {
            "session_id": session_id,
            "status": "active",
            "summary": summary,
            "message": "Use the unified chat interface for detailed interaction"
        }
        
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
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Legacy endpoint - phase transitions now handled through chat interface."""
    return {
        "session_id": session_id,
        "message": f"Phase transitions are now handled through the unified chat interface. Please use /chat/message to guide the conversation to the '{phase}' phase."
    }


@router.get("/detect-domain")
async def detect_transformation_domain(
    description: str
):
    """Simple domain detection - all transformations use unified approach."""
    return {
        "description": description,
        "detected_domain": "unified_business_transformation",
        "confidence": 1.0,
        "message": "All transformations now use the unified chat-based approach for better user experience"
    }


@router.get("/health")
async def transformations_health_check():
    """Health check for transformation functionality."""
    return {
        "status": "healthy",
        "service": "transformations_api_unified",
        "note": "Transformation functionality unified into chat interface",
        "endpoints": [
            "/transformations/analyze",
            "/transformations/detect-domain",
            "/transformations/sessions/{session_id}/status",
            "/transformations/health"
        ]
    }