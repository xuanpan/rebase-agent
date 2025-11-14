"""Chat and conversation models."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ConversationIntent(str, Enum):
    START_TRANSFORMATION = "start_transformation"
    ANSWER_QUESTION = "answer_question"
    REQUEST_CLARIFICATION = "request_clarification"
    APPROVE_BUSINESS_CASE = "approve_business_case"
    REQUEST_MORE_INFO = "request_more_info"
    GENERAL_CHAT = "general_chat"


@dataclass
class ChatResponse:
    """Unified chat response with intelligent data collection insights."""
    message: str
    suggested_responses: List[str]
    current_phase: str
    progress_percentage: float
    
    # Enhanced LLM-driven fields  
    collected_data: Optional[Dict[str, Any]] = None
    discovery_summary: Optional[Dict[str, Any]] = None
    data_completeness: float = 0.0
    missing_critical_info: List[str] = None
    extraction_confidence: float = 0.0
    next_question_reasoning: str = ""
    
    # Original fields
    action_required: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_level: float = 0.0
    
    def __post_init__(self):
        if self.missing_critical_info is None:
            self.missing_critical_info = []


@dataclass
class MessageAnalysis:
    original_message: str
    business_entities: Dict[str, Any]
    pain_points_mentioned: List[str]
    quantitative_data: Dict[str, Any]
    sentiment: str
    intent: str
    confidence: float