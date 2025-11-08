"""
Session manager for handling conversation sessions and persistence.

This module manages conversation sessions, including creation, retrieval,
and persistence of conversation state across multiple interactions.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import json
import uuid

from loguru import logger

from .conversation_flow import ConversationState, ConversationPhase
from ..context_manager import ConversationContext, ConversationMessage


class SessionManager:
    """Manages conversation sessions and their persistence."""
    
    def __init__(self):
        """Initialize the session manager."""
        # In-memory storage for development
        # Using in-memory storage for POC (Redis removed for simplicity)
        self.sessions: Dict[str, ConversationState] = {}
        self.session_contexts: Dict[str, ConversationContext] = {}
        
    def create_session(self, user_id: str, initial_message: str, domain: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: User identifier
            initial_message: The first message from the user
            domain: Optional domain hint
            
        Returns:
            Session ID
        """
        
        session_id = str(uuid.uuid4())
        
        # Create conversation state
        conversation_state = ConversationState(
            session_id=session_id,
            current_phase=ConversationPhase.INITIAL,
            domain=domain
        )
        
        # Create conversation context
        conversation_context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            metadata={"initial_message": initial_message}
        )
        
        # Store both
        self.sessions[session_id] = conversation_state
        self.session_contexts[session_id] = conversation_context
        
        logger.info(f"Created session {session_id} for user {user_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """
        Retrieve a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation state or None if not found
        """
        
        return self.sessions.get(session_id)
    
    def get_session_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Retrieve session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation context or None if not found
        """
        
        return self.session_contexts.get(session_id)
    
    def update_session(self, session_id: str, conversation_state: ConversationState) -> bool:
        """
        Update a conversation session.
        
        Args:
            session_id: Session identifier
            conversation_state: Updated state
            
        Returns:
            True if successful, False if session not found
        """
        
        if session_id not in self.sessions:
            return False
        
        conversation_state.updated_at = datetime.now()
        self.sessions[session_id] = conversation_state
        
        logger.info(f"Updated session {session_id}")
        
        return True
    
    def add_message_to_session(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a message to the session context.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            True if successful, False if session not found
        """
        
        context = self.session_contexts.get(session_id)
        if not context:
            return False
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        context.messages.append(message)
        
        logger.info(f"Added message to session {session_id}: {role}")
        
        return True
    
    def get_session_messages(self, session_id: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of messages
        """
        
        context = self.session_contexts.get(session_id)
        if not context:
            return []
        
        messages = context.messages
        if limit:
            messages = messages[-limit:]  # Get most recent messages
        
        return messages
    
    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session summaries
        """
        
        user_sessions = []
        
        for session_id, context in self.session_contexts.items():
            if context.user_id == user_id:
                state = self.sessions.get(session_id)
                
                summary = {
                    "session_id": session_id,
                    "created_at": context.created_at.isoformat(),
                    "current_phase": state.current_phase.value if state else "unknown",
                    "domain": state.domain if state else None,
                    "message_count": len(context.messages),
                    "last_activity": context.updated_at.isoformat()
                }
                
                user_sessions.append(summary)
        
        # Sort by last activity (most recent first)
        user_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return user_sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        
        deleted_state = session_id in self.sessions
        deleted_context = session_id in self.session_contexts
        
        if deleted_state:
            del self.sessions[session_id]
        
        if deleted_context:
            del self.session_contexts[session_id]
        
        if deleted_state or deleted_context:
            logger.info(f"Deleted session {session_id}")
            return True
        
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old inactive sessions.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of sessions cleaned up
        """
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_delete = []
        
        for session_id, context in self.session_contexts.items():
            if context.updated_at < cutoff_time:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_delete)} old sessions")
        
        return len(sessions_to_delete)
    
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export session data for backup or analysis.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        
        state = self.sessions.get(session_id)
        context = self.session_contexts.get(session_id)
        
        if not state or not context:
            return None
        
        # Convert to serializable format
        export_data = {
            "session_id": session_id,
            "state": {
                "current_phase": state.current_phase.value,
                "domain": state.domain,
                "completed_phases": [p.value for p in state.completed_phases],
                "answers": {
                    answer_id: {
                        "question_id": answer.question_id,
                        "answer": answer.answer,
                        "timestamp": answer.timestamp.isoformat(),
                        "confidence": answer.confidence,
                        "source": answer.source
                    }
                    for answer_id, answer in state.answers.items()
                },
                "context": state.context,
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat()
            },
            "context": {
                "user_id": context.user_id,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in context.messages
                ],
                "metadata": context.metadata,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat()
            }
        }
        
        return export_data
    
    def import_session(self, export_data: Dict[str, Any]) -> bool:
        """
        Import session data from backup.
        
        Args:
            export_data: Exported session data
            
        Returns:
            True if successful, False otherwise
        """
        
        try:
            session_id = export_data["session_id"]
            
            # Reconstruct conversation state
            state_data = export_data["state"]
            conversation_state = ConversationState(
                session_id=session_id,
                current_phase=ConversationPhase(state_data["current_phase"]),
                domain=state_data["domain"],
                completed_phases=[ConversationPhase(p) for p in state_data["completed_phases"]],
                context=state_data["context"],
                created_at=datetime.fromisoformat(state_data["created_at"]),
                updated_at=datetime.fromisoformat(state_data["updated_at"])
            )
            
            # Reconstruct answers
            from .conversation_flow import ConversationAnswer
            for answer_id, answer_data in state_data["answers"].items():
                answer = ConversationAnswer(
                    question_id=answer_data["question_id"],
                    answer=answer_data["answer"],
                    timestamp=datetime.fromisoformat(answer_data["timestamp"]),
                    confidence=answer_data["confidence"],
                    source=answer_data["source"]
                )
                conversation_state.answers[answer_id] = answer
            
            # Reconstruct conversation context
            context_data = export_data["context"]
            conversation_context = ConversationContext(
                session_id=session_id,
                user_id=context_data["user_id"],
                messages=[],
                metadata=context_data["metadata"],
                created_at=datetime.fromisoformat(context_data["created_at"]),
                updated_at=datetime.fromisoformat(context_data["updated_at"])
            )
            
            # Reconstruct messages
            for msg_data in context_data["messages"]:
                message = ConversationMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data["metadata"]
                )
                conversation_context.messages.append(message)
            
            # Store reconstructed session
            self.sessions[session_id] = conversation_state
            self.session_contexts[session_id] = conversation_context
            
            logger.info(f"Imported session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all sessions.
        
        Returns:
            Statistics dictionary
        """
        
        total_sessions = len(self.sessions)
        
        # Phase distribution
        phase_counts = {}
        for state in self.sessions.values():
            phase = state.current_phase.value
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        # Domain distribution
        domain_counts = {}
        for state in self.sessions.values():
            domain = state.domain or "unknown"
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Activity in last 24 hours
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_sessions = sum(
            1 for context in self.session_contexts.values()
            if context.updated_at > recent_cutoff
        )
        
        return {
            "total_sessions": total_sessions,
            "recent_sessions_24h": recent_sessions,
            "phase_distribution": phase_counts,
            "domain_distribution": domain_counts,
            "average_messages_per_session": (
                sum(len(context.messages) for context in self.session_contexts.values()) / total_sessions
                if total_sessions > 0 else 0
            )
        }