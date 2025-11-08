"""
Chat API - Conversational interface for transformation analysis.

Provides endpoints for chat-first transformation analysis including
conversation management, message processing, and session handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
from loguru import logger

from core.conversation.chat_engine import ChatEngine, ChatResponse
from app.dependencies import get_chat_engine


router = APIRouter(prefix="/chat")


# Request/Response Models
class StartConversationRequest(BaseModel):
    initial_message: str
    user_context: Optional[Dict[str, Any]] = None


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    message: str
    suggested_responses: List[str]
    current_phase: str
    progress_percentage: float
    action_required: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_level: float


class ConversationSessionResponse(BaseModel):
    session_id: str
    domain_type: Optional[str]
    current_phase: str
    progress_percentage: float
    discovered_facts: Dict[str, Any]
    conversation_length: int
    started_at: str
    last_updated: str


# API Endpoints
@router.post("/start", response_model=Dict[str, Any])
async def start_conversation(
    request: StartConversationRequest,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Start a new transformation conversation."""
    try:
        result = await chat_engine.start_conversation(
            initial_message=request.initial_message,
            user_context=request.user_context
        )
        
        logger.info(f"Started conversation: {result['session_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Send a message and get AI response."""
    try:
        response = await chat_engine.process_message(
            session_id=request.session_id,
            user_message=request.message
        )
        
        return ChatMessageResponse(
            message=response.message,
            suggested_responses=response.suggested_responses,
            current_phase=response.current_phase,
            progress_percentage=response.progress_percentage,
            action_required=response.action_required,
            structured_data=response.structured_data,
            confidence_level=response.confidence_level
        )
        
    except ValueError as e:
        # Session not found or invalid
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}/summary", response_model=ConversationSessionResponse)
async def get_conversation_summary(
    session_id: str,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Get conversation summary and current status."""
    try:
        summary = await chat_engine.get_conversation_summary(session_id)
        
        if "error" in summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"]
            )
        
        return ConversationSessionResponse(
            session_id=summary["session_id"],
            domain_type=summary.get("domain_type"),
            current_phase=summary["current_phase"], 
            progress_percentage=summary["progress_percentage"],
            discovered_facts=summary["discovered_facts"],
            conversation_length=summary["conversation_length"],
            started_at=summary["started_at"],
            last_updated=summary["last_updated"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation summary: {str(e)}"
        )


@router.get("/sessions/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = 50,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Get conversation message history."""
    try:
        # Get conversation history through context manager
        context_manager = chat_engine.context_manager
        messages = context_manager.get_conversation_history(
            session_id, 
            limit=limit
        )
        
        if not messages and not context_manager.get_context(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "session_id": session_id,
            "messages": [msg.to_dict() for msg in messages],
            "total_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_conversation(
    session_id: str,
    chat_engine: ChatEngine = Depends(get_chat_engine)
):
    """Delete a conversation session."""
    try:
        success = chat_engine.context_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or could not be deleted"
            )
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/health")
async def chat_health_check():
    """Health check for chat functionality."""
    return {
        "status": "healthy",
        "service": "chat_api",
        "endpoints": [
            "/chat/start",
            "/chat/message", 
            "/chat/sessions/{session_id}/summary",
            "/chat/sessions/{session_id}/history"
        ]
    }