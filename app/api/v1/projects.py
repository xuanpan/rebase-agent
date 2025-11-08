"""
Projects API - Project management and tracking endpoints.

Provides endpoints for managing transformation projects, tracking progress,
and handling project-related data and workflows.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from core.context_manager import ContextManager
from app.dependencies import get_context_manager


router = APIRouter(prefix="/projects")


class ProjectSummary(BaseModel):
    session_id: str
    domain_type: Optional[str]
    current_phase: str
    progress_percentage: float
    created_at: str
    updated_at: str
    title: Optional[str] = None


@router.get("/")
async def list_projects(
    user_id: Optional[str] = None,
    limit: int = 50,
    context_manager: ContextManager = Depends(get_context_manager)
):
    """List transformation projects/sessions."""
    try:
        # Get active sessions
        active_sessions = context_manager.list_active_sessions(user_id)
        
        projects = []
        for session_id in active_sessions[:limit]:
            context = context_manager.get_context(session_id)
            if context:
                # Generate a title from discovered facts or initial message
                title = None
                if context.conversation_history:
                    first_message = context.conversation_history[0].content
                    title = first_message[:50] + "..." if len(first_message) > 50 else first_message
                
                projects.append(ProjectSummary(
                    session_id=session_id,
                    domain_type=context.domain_type,
                    current_phase=context.current_phase,
                    progress_percentage=_calculate_progress(context),
                    created_at=context.created_at.isoformat(),
                    updated_at=context.updated_at.isoformat(),
                    title=title
                ))
        
        return {
            "projects": projects,
            "total_count": len(projects),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get("/{session_id}")
async def get_project_details(
    session_id: str,
    context_manager: ContextManager = Depends(get_context_manager)
):
    """Get detailed project information."""
    try:
        context = context_manager.get_context(session_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get recent context summary
        summary = context_manager.get_recent_context_summary(session_id)
        
        return {
            "session_id": session_id,
            "domain_type": context.domain_type,
            "current_phase": context.current_phase,
            "progress_percentage": _calculate_progress(context),
            "discovered_facts": context.discovered_facts,
            "business_metrics": context.business_metrics,
            "conversation_summary": summary,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project details: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_project(
    session_id: str,
    context_manager: ContextManager = Depends(get_context_manager)
):
    """Delete a transformation project."""
    try:
        success = context_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or could not be deleted"
            )
        
        return {
            "message": f"Project {session_id} deleted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


@router.post("/{session_id}/archive")
async def archive_project(
    session_id: str,
    context_manager: ContextManager = Depends(get_context_manager)
):
    """Archive a transformation project (mark as completed/inactive)."""
    try:
        context = context_manager.get_context(session_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Update context to mark as archived
        success = context_manager.update_context(
            session_id,
            current_phase="archived"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to archive project"
            )
        
        return {
            "message": f"Project {session_id} archived successfully",
            "session_id": session_id,
            "status": "archived"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive project: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_projects(
    days_old: int = 30,
    context_manager: ContextManager = Depends(get_context_manager)
):
    """Clean up old/expired projects."""
    try:
        context_manager.cleanup_expired_sessions(days_old)
        
        return {
            "message": f"Cleaned up projects older than {days_old} days",
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup projects: {str(e)}"
        )


@router.get("/health")
async def projects_health_check():
    """Health check for projects functionality."""
    return {
        "status": "healthy",
        "service": "projects_api",
        "endpoints": [
            "/projects/",
            "/projects/{session_id}",
            "/projects/{session_id}/archive",
            "/projects/cleanup"
        ]
    }


def _calculate_progress(context) -> float:
    """Calculate project progress percentage."""
    phase_percentages = {
        "discovery": 20.0,
        "assessment": 40.0,
        "justification": 70.0,
        "planning": 90.0,
        "completed": 100.0,
        "archived": 100.0
    }
    
    base_progress = phase_percentages.get(context.current_phase, 0.0)
    
    # Add bonus progress based on discovered facts
    if context.current_phase == "discovery":
        facts_bonus = min(20.0, len(context.discovered_facts) * 2)
        return base_progress + facts_bonus
    
    return base_progress