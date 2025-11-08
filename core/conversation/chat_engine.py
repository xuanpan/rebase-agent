"""
Chat Engine - Main conversational orchestrator for chat-first transformation analysis.

Coordinates between message processing, conversation flow, response generation,
and the universal transformation engine to provide natural chat interactions.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime, timezone
from loguru import logger

from ..llm_client import LLMClient
from ..prompt_engine import PromptEngine
from ..context_manager import ContextManager
from ..question_engine import QuestionEngine
from ..transformation_engine import UniversalTransformationEngine, TransformationPhase


@dataclass
class ChatResponse:
    message: str
    suggested_responses: List[str]
    current_phase: str
    progress_percentage: float
    action_required: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence_level: float = 0.0


@dataclass
class MessageAnalysis:
    original_message: str
    business_entities: Dict[str, Any]
    pain_points_mentioned: List[str]
    quantitative_data: Dict[str, Any]
    sentiment: str
    intent: str
    confidence: float


class ConversationIntent(str, Enum):
    START_TRANSFORMATION = "start_transformation"
    ANSWER_QUESTION = "answer_question"
    REQUEST_CLARIFICATION = "request_clarification"
    APPROVE_BUSINESS_CASE = "approve_business_case"
    REQUEST_MORE_INFO = "request_more_info"
    GENERAL_CHAT = "general_chat"


class ChatEngine:
    """Main conversational orchestrator for transformation analysis."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_engine: PromptEngine,
        context_manager: ContextManager,
        question_engine: QuestionEngine,
        transformation_engine: UniversalTransformationEngine
    ):
        self.llm_client = llm_client
        self.prompt_engine = prompt_engine
        self.context_manager = context_manager
        self.question_engine = question_engine
        self.transformation_engine = transformation_engine
        
        # Set up transformation engine connection
        self.transformation_engine.context_manager = context_manager
        
        logger.info("ChatEngine initialized")
    
    async def start_conversation(
        self,
        initial_message: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new transformation conversation."""
        
        try:
            # Create new session
            session_id = await self.transformation_engine.start_transformation_analysis(
                user_request=initial_message,
                user_id=user_context.get("user_id") if user_context else None
            )
            
            # Generate initial response
            response = await self._generate_initial_response(initial_message, session_id)
            
            return {
                "session_id": session_id,
                "response": response,
                "phase": "discovery",
                "progress": 5.0
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise
    
    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> ChatResponse:
        """Process user message and generate appropriate response."""
        
        try:
            # Get conversation context
            context = self.context_manager.get_context(session_id)
            if not context:
                raise ValueError(f"Session not found: {session_id}")
            
            # Analyze the user message
            message_analysis = await self._analyze_message(user_message, context)
            
            # Process through transformation engine
            transformation_result = await self.transformation_engine.process_user_input(
                session_id, user_message
            )
            
            # Generate conversational response
            chat_response = await self._generate_chat_response(
                message_analysis, transformation_result, context
            )
            
            logger.debug(f"Processed message for session {session_id}: {message_analysis.intent}")
            return chat_response
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            # Return friendly error response
            return ChatResponse(
                message="I apologize, but I encountered an issue processing your message. Could you please try rephrasing?",
                suggested_responses=["Let me rephrase that", "Can you help me understand?"],
                current_phase="error",
                progress_percentage=0.0,
                confidence_level=0.0
            )
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation and current status."""
        
        transformation_status = await self.transformation_engine.get_transformation_status(session_id)
        context = self.context_manager.get_context(session_id)
        
        if not context:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "domain_type": transformation_status.domain_type,
            "current_phase": transformation_status.current_phase.value,
            "progress_percentage": transformation_status.completion_percentage,
            "discovered_facts": context.discovered_facts,
            "business_case": transformation_status.business_case,
            "conversation_length": len(context.conversation_history),
            "started_at": context.created_at.isoformat(),
            "last_updated": context.updated_at.isoformat()
        }
    
    async def _analyze_message(
        self,
        message: str,
        context
    ) -> MessageAnalysis:
        """Analyze user message for intent, entities, and business context."""
        
        analysis_prompt = self.prompt_engine.render_template(
            "conversation/analyze_user_message.jinja2",
            user_message=message,
            conversation_history=[msg.to_dict() for msg in context.conversation_history[-5:]],
            current_phase=context.current_phase,
            domain_type=context.domain_type
        )
        
        try:
            # Try LLM analysis first
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": analysis_prompt}
            ])
            
            # Parse AI analysis - simplified for now
            # In real implementation, this would use structured output or JSON parsing
            
        except Exception as e:
            logger.warning(f"LLM analysis failed, using rule-based fallback: {e}")
            # Fall back to rule-based analysis for demo mode
            response = {"content": "Rule-based analysis used."}
            
            # Extract business entities
            business_entities = {}
            if any(word in message.lower() for word in ["team", "developer", "people"]):
                # Extract team size
                import re
                match = re.search(r'(\d+)\s*(?:developers?|people|team)', message.lower())
                if match:
                    business_entities["team_size"] = int(match.group(1))
            
            # Extract pain points
            pain_indicators = ["slow", "complex", "difficult", "problem", "issue", "struggle", "hard"]
            pain_points = [word for word in pain_indicators if word in message.lower()]
            
            # Determine intent
            intent = self._classify_intent(message, context)
            
            return MessageAnalysis(
                original_message=message,
                business_entities=business_entities,
                pain_points_mentioned=pain_points,
                quantitative_data={},
                sentiment="neutral",  # Simplified
                intent=intent.value,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return MessageAnalysis(
                original_message=message,
                business_entities={},
                pain_points_mentioned=[],
                quantitative_data={},
                sentiment="neutral",
                intent=ConversationIntent.GENERAL_CHAT.value,
                confidence=0.5
            )
    
    def _classify_intent(self, message: str, context) -> ConversationIntent:
        """Classify user intent based on message content and context."""
        
        message_lower = message.lower()
        
        # Check for transformation start keywords
        if any(word in message_lower for word in ["migrate", "convert", "upgrade", "modernize", "transform"]):
            return ConversationIntent.START_TRANSFORMATION
        
        # Check for approval keywords
        if any(word in message_lower for word in ["yes", "approve", "proceed", "go ahead", "sounds good"]):
            return ConversationIntent.APPROVE_BUSINESS_CASE
        
        # Check for clarification requests
        if any(word in message_lower for word in ["what", "how", "why", "explain", "clarify"]):
            return ConversationIntent.REQUEST_CLARIFICATION
        
        # Check for information requests
        if any(word in message_lower for word in ["more", "details", "tell me", "show me"]):
            return ConversationIntent.REQUEST_MORE_INFO
        
        # Default to answering question if we're in discovery phase
        if context.current_phase == "discovery":
            return ConversationIntent.ANSWER_QUESTION
        
        return ConversationIntent.GENERAL_CHAT
    
    async def _generate_initial_response(
        self,
        initial_message: str,
        session_id: str
    ) -> str:
        """Generate initial conversational response to start the transformation analysis."""
        
        initial_prompt = self.prompt_engine.render_template(
            "conversation/initial_response.jinja2",
            user_message=initial_message,
            session_id=session_id
        )
        
        try:
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": initial_prompt}
            ])
            
            # Add the response to conversation history
            self.context_manager.add_message(session_id, "assistant", response.content)
            
            return response.content
            
        except Exception as e:
            logger.warning(f"LLM response generation failed, using template fallback: {e}")
            # Fall back to template-based response for demo mode
            fallback_response = f"I'd love to help you with your transformation project! Based on your message about '{initial_message[:100]}...', I can see this is a framework migration project. Let me gather some key information to provide you with accurate ROI calculations and a detailed implementation plan."
            
            # Add the response to conversation history
            self.context_manager.add_message(session_id, "assistant", fallback_response)
            
            return fallback_response
            
        except Exception as e:
            logger.error(f"Error generating initial response: {e}")
            return ("I'd love to help you explore this transformation! "
                   "Let me understand your current situation better. "
                   "What specific challenges are you facing that made you consider this change?")
    
    async def _generate_chat_response(
        self,
        message_analysis: MessageAnalysis,
        transformation_result: Dict[str, Any],
        context
    ) -> ChatResponse:
        """Generate conversational response based on analysis and transformation result."""
        
        # Extract information from transformation result
        phase = transformation_result.get("phase", context.current_phase)
        progress = transformation_result.get("progress", 0.0)
        response_content = transformation_result.get("response", "")
        
        # Generate suggested responses based on phase and context
        suggested_responses = self._generate_suggested_responses(phase, message_analysis)
        
        # Determine if any action is required
        action_required = None
        if phase == "justification":
            action_required = "approval_decision"
        elif phase == "planning":
            action_required = "implementation_approval"
        
        # Extract structured data if available
        structured_data = None
        if "business_case" in transformation_result:
            structured_data = transformation_result["business_case"]
        elif "assessment" in transformation_result:
            structured_data = transformation_result["assessment"]
        
        return ChatResponse(
            message=response_content,
            suggested_responses=suggested_responses,
            current_phase=phase,
            progress_percentage=progress,
            action_required=action_required,
            structured_data=structured_data,
            confidence_level=message_analysis.confidence
        )
    
    def _generate_suggested_responses(
        self,
        phase: str,
        message_analysis: MessageAnalysis
    ) -> List[str]:
        """Generate contextual suggested responses for the user."""
        
        if phase == "discovery":
            return [
                "Let me tell you more about that",
                "That's exactly the kind of issue we can address",
                "I have some specific numbers on this"
            ]
        elif phase == "justification":
            return [
                "Yes, let's proceed",
                "I need more details on this", 
                "What are the risks?",
                "Show me the implementation plan"
            ]
        elif phase == "planning":
            return [
                "This looks good, let's start",
                "Can we adjust the timeline?",
                "What support will we need?"
            ]
        else:
            return [
                "Tell me more",
                "That makes sense",
                "What's next?"
            ]