"""
Context Manager - Conversation and project context management.

Handles long-term conversation memory, project state persistence,
cross-phase context continuity, and stakeholder context switching.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from loguru import logger


class ContextScope(str, Enum):
    SESSION = "session"
    PROJECT = "project"  
    USER = "user"
    GLOBAL = "global"


@dataclass
class ConversationMessage:
    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass 
class ConversationContext:
    session_id: str
    user_id: Optional[str]
    domain_type: Optional[str]
    current_phase: str
    discovered_facts: Dict[str, Any]
    business_metrics: Dict[str, Any]
    conversation_history: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "domain_type": self.domain_type,
            "current_phase": self.current_phase,
            "discovered_facts": self.discovered_facts,
            "business_metrics": self.business_metrics,
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            domain_type=data.get("domain_type"),
            current_phase=data["current_phase"],
            discovered_facts=data["discovered_facts"],
            business_metrics=data["business_metrics"],
            conversation_history=[
                ConversationMessage.from_dict(msg) for msg in data["conversation_history"]
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )


class ContextManager:
    """Manages conversation and project context across sessions."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize context manager with file-based storage."""
        # Redis removed for POC simplicity
        
        if storage_dir is None:
            storage_dir = Path.cwd() / ".rebase" / "context"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for active sessions
        self._session_cache: Dict[str, ConversationContext] = {}
        
        logger.info(f"ContextManager initialized with storage: {self.storage_dir}")
    
    def create_session(
        self, 
        initial_message: Optional[str] = None,
        user_id: Optional[str] = None,
        domain_type: Optional[str] = None
    ) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            domain_type=domain_type,
            current_phase="discovery",
            discovered_facts={},
            business_metrics={},
            conversation_history=[],
            created_at=now,
            updated_at=now
        )
        
        if initial_message:
            self.add_message(session_id, "user", initial_message)
        
        self._session_cache[session_id] = context
        self._persist_context(context)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        # Check cache first
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        
        # Try loading from persistent storage
        context = self._load_context(session_id)
        if context:
            self._session_cache[session_id] = context
        
        return context
    
    def update_context(
        self,
        session_id: str,
        discovered_facts: Optional[Dict[str, Any]] = None,
        business_metrics: Optional[Dict[str, Any]] = None,
        current_phase: Optional[str] = None,
        domain_type: Optional[str] = None
    ) -> bool:
        """Update context for a session."""
        context = self.get_context(session_id)
        if not context:
            logger.warning(f"Context not found for session: {session_id}")
            return False
        
        # Update fields if provided
        if discovered_facts is not None:
            context.discovered_facts.update(discovered_facts)
        
        if business_metrics is not None:
            context.business_metrics.update(business_metrics)
        
        if current_phase is not None:
            context.current_phase = current_phase
            
        if domain_type is not None:
            context.domain_type = domain_type
        
        context.updated_at = datetime.now(timezone.utc)
        
        # Update cache and persist
        self._session_cache[session_id] = context
        self._persist_context(context)
        
        return True
    
    def add_message(
        self,
        session_id: str, 
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a message to the conversation history."""
        context = self.get_context(session_id)
        if not context:
            logger.warning(f"Context not found for session: {session_id}")
            return False
        
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )
        
        context.conversation_history.append(message)
        context.updated_at = datetime.now(timezone.utc)
        
        # Update cache and persist
        self._session_cache[session_id] = context
        self._persist_context(context)
        
        logger.debug(f"Added {role} message to session {session_id}")
        return True
    
    def get_conversation_history(
        self, 
        session_id: str,
        limit: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[ConversationMessage]:
        """Get conversation history with optional filtering."""
        context = self.get_context(session_id)
        if not context:
            return []
        
        messages = context.conversation_history
        
        # Filter by role if specified
        if role_filter:
            messages = [msg for msg in messages if msg.role == role_filter]
        
        # Limit number of messages if specified
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_recent_context_summary(self, session_id: str, max_messages: int = 10) -> Dict[str, Any]:
        """Get a summary of recent context for LLM consumption."""
        context = self.get_context(session_id)
        if not context:
            return {}
        
        recent_messages = context.conversation_history[-max_messages:]
        
        return {
            "session_id": session_id,
            "domain_type": context.domain_type,
            "current_phase": context.current_phase,
            "discovered_facts": context.discovered_facts,
            "business_metrics": context.business_metrics,
            "recent_conversation": [
                {"role": msg.role, "content": msg.content} 
                for msg in recent_messages
            ],
            "conversation_length": len(context.conversation_history),
            "session_duration_minutes": (
                context.updated_at - context.created_at
            ).total_seconds() / 60
        }
    
    def list_active_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """List active session IDs, optionally filtered by user."""
        sessions = []
        
        # Check cached sessions first
        for session_id, context in self._session_cache.items():
            if user_id is None or context.user_id == user_id:
                sessions.append(session_id)
        
        # TODO: Also check persistent storage for sessions not in cache
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        try:
            # Remove from cache
            if session_id in self._session_cache:
                del self._session_cache[session_id]
            
            # Remove from persistent storage
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def _persist_context(self, context: ConversationContext):
        """Persist context to file storage."""
        try:
            # Store as JSON file (Redis removed for POC simplicity)
            session_file = self.storage_dir / f"{context.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(context.to_dict(), f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error persisting context for {context.session_id}: {e}")
    
    def _load_context(self, session_id: str) -> Optional[ConversationContext]:
        """Load context from file storage."""
        try:
            # Load from file storage (Redis removed for POC simplicity)
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    context_dict = json.load(f)
                return ConversationContext.from_dict(context_dict)
            
        except Exception as e:
            logger.error(f"Error loading context for {session_id}: {e}")
        
        return None
    
    def cleanup_expired_sessions(self, days_old: int = 30):
        """Clean up old sessions from storage."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        cleaned_count = 0
        
        try:
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        context_dict = json.load(f)
                    
                    created_at = datetime.fromisoformat(context_dict["created_at"])
                    if created_at < cutoff_date:
                        session_file.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error checking session file {session_file}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")