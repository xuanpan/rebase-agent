"""
Unified Chat Engine - LLM-driven conversational orchestrator for transformation analysis.

Single unified system that combines intelligent data collection, conversation flow,
and business discovery with the universal transformation engine.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import json
from datetime import datetime, timezone

try:
    from loguru import logger
except ImportError:
    # Fallback logger for environments without loguru
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..context_manager import ContextManager
from ..question_engine import QuestionEngine
from ..transformation_engine import UniversalTransformationEngine, TransformationPhase


@dataclass
class CollectedBusinessData:
    """Unified structured business data collection model."""
    
    # Business Context
    business_goals: List[str] = None
    pain_points: List[Dict[str, Any]] = None  # {"description": str, "impact": str, "frequency": str}
    success_criteria: List[str] = None
    key_metrics: List[str] = None  # Performance metrics and KPIs
    
    # Stakeholder Information
    decision_makers: List[str] = None
    affected_users: List[str] = None
    technical_contacts: List[str] = None
    
    # Financial Context
    current_costs: Dict[str, float] = None  # {"maintenance": 10000, "lost_productivity": 5000}
    budget_range: Dict[str, float] = None   # {"min": 50000, "max": 150000}
    roi_expectations: Dict[str, Any] = None # {"target_percentage": 200, "payback_months": 12}
    
    # Technical Context
    current_technology: Dict[str, str] = None  # {"framework": "React", "version": "16.8"}
    team_info: Dict[str, Any] = None          # {"size": 5, "experience": "intermediate"}
    system_scale: Dict[str, Any] = None       # {"users": 1000, "requests_per_day": 100000}
    
    # Timeline & Constraints
    timeline_constraints: Dict[str, Any] = None  # {"must_complete_by": "2024-06-01", "flexibility": "moderate"}
    regulatory_requirements: List[str] = None
    business_constraints: List[str] = None
    
    # Urgency & Risk
    urgency_factors: List[Dict[str, str]] = None  # {"factor": "security", "severity": "high"}
    risk_tolerance: str = None  # "low" | "moderate" | "high"
    
    def __post_init__(self):
        """Initialize empty lists/dicts as needed."""
        for field_name, field_type in self.__annotations__.items():
            if getattr(self, field_name) is None:
                if 'List' in str(field_type):
                    setattr(self, field_name, [])
                elif 'Dict' in str(field_type):
                    setattr(self, field_name, {})
    
    def get_completeness_score(self) -> float:
        """Calculate how complete the collected data is (0.0 to 1.0)."""
        total_fields = len(self.__annotations__)
        completed_fields = 0
        
        for field_name in self.__annotations__.keys():
            value = getattr(self, field_name)
            if value:  # Not None and not empty
                if isinstance(value, (list, dict)) and len(value) > 0:
                    completed_fields += 1
                elif isinstance(value, str) and value.strip():
                    completed_fields += 1
                elif isinstance(value, (int, float)) and value > 0:
                    completed_fields += 1
        
        return completed_fields / total_fields
    
    def get_missing_categories(self) -> List[str]:
        """Get categories of information that are still missing or incomplete."""
        missing = []
        
        if not self.business_goals or not self.pain_points:
            missing.append("business_context")
        if not self.decision_makers or not self.affected_users:
            missing.append("stakeholder_mapping")
        if not self.current_costs or not self.budget_range:
            missing.append("financial_context")
        if not self.current_technology or not self.team_info:
            missing.append("technical_context")
        if not self.timeline_constraints:
            missing.append("timeline_constraints")
        if not self.urgency_factors or not self.risk_tolerance:
            missing.append("risk_assessment")
        
        return missing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ChatResponse:
    """Unified chat response with intelligent data collection insights."""
    message: str
    suggested_responses: List[str]
    current_phase: str
    progress_percentage: float
    
    # Enhanced LLM-driven fields
    collected_data: Optional[Dict[str, Any]] = None
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


class ConversationIntent(str, Enum):
    START_TRANSFORMATION = "start_transformation"
    ANSWER_QUESTION = "answer_question"
    REQUEST_CLARIFICATION = "request_clarification"
    APPROVE_BUSINESS_CASE = "approve_business_case"
    REQUEST_MORE_INFO = "request_more_info"
    GENERAL_CHAT = "general_chat"


class ChatEngine:
    """Unified conversational orchestrator with LLM-driven data collection."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        context_manager: ContextManager,
        question_engine: QuestionEngine,
        transformation_engine: UniversalTransformationEngine
    ):
        self.llm_client = llm_client
        self.context_manager = context_manager
        self.question_engine = question_engine
        self.transformation_engine = transformation_engine
        
        # Set up transformation engine connection
        self.transformation_engine.context_manager = context_manager
        
        # In-memory storage for collected business data (in production, this would be persistent)
        self.session_business_data: Dict[str, CollectedBusinessData] = {}
        
        try:
            logger.info("Unified ChatEngine initialized with LLM-driven capabilities")
        except:
            print("Unified ChatEngine initialized with LLM-driven capabilities")
    
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
        """Unified message processing with LLM-driven data collection."""
        
        try:
            # Get conversation context
            context = self.context_manager.get_context(session_id)
            if not context:
                raise ValueError(f"Session not found: {session_id}")
            
            # Get or initialize collected business data for this session
            if session_id not in self.session_business_data:
                self.session_business_data[session_id] = CollectedBusinessData()
            
            collected_data = self.session_business_data[session_id]
            
            # Get conversation history
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in context.conversation_history
            ]
            
            # Step 2: Save answer to DB
            self.context_manager.add_message(session_id, "user", user_message)
            conversation_history.append({"role": "user", "content": user_message})
            
            # Step 3: Build full conversation context
            # Step 4: Send single prompt to LLM for decision
            llm_decision = await self._get_llm_discovery_decision(
                conversation_history, collected_data, context
            )
            
            # Step 5: LLM returns either next question or completion
            if llm_decision.get("status") == "complete":
                # Discovery is complete - transition to next phase
                response_content, next_phase, progress, action_required = await self._generate_completion_response(
                    llm_decision, collected_data, context
                )
            else:
                # Continue discovery with next question
                response_content = llm_decision.get("next_question", "Could you tell me more about your current situation?")
                next_phase = "discovery"
                progress = llm_decision.get("progress_percentage", 15.0)
                action_required = None
                
                # Update collected data from LLM response
                if "extracted_data" in llm_decision:
                    collected_data = await self._update_collected_data(collected_data, llm_decision)
                    self.session_business_data[session_id] = collected_data
            
            # Add assistant response to conversation
            self.context_manager.add_message(session_id, "assistant", response_content)
            
            # Update context with new phase if changed
            if next_phase != context.current_phase:
                self.context_manager.update_context(session_id, current_phase=next_phase)
            
            # Step 6: Update DB + return response
            # Generate suggested responses
            suggested_responses = self._generate_contextual_suggestions(
                next_phase, llm_decision, collected_data
            )
            
            return ChatResponse(
                message=response_content,
                suggested_responses=suggested_responses,
                current_phase=next_phase,
                progress_percentage=progress,
                collected_data=collected_data.to_dict(),
                data_completeness=llm_decision.get("completeness_score", 0.0),
                missing_critical_info=llm_decision.get("missing_critical_info", []),
                extraction_confidence=llm_decision.get("confidence", 0.0),
                next_question_reasoning=llm_decision.get("reasoning", "LLM-driven discovery"),
                action_required=action_required,
                structured_data=collected_data.to_dict(),
                confidence_level=llm_decision.get("confidence", 0.0)
            )
            
        except Exception as e:
            try:
                logger.error(f"Error processing message for session {session_id}: {e}")
            except:
                print(f"Error processing message for session {session_id}: {e}")
            
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
        
        # Simplified analysis using fallback logic (no templates needed)
        try:
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
        
        # Use fallback response for demo mode (no templates needed)
        try:
            logger.warning(f"Using fallback response for initial message")
            # Fallback response for demo mode
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
    
    # =============================================================================
    # LLM-DRIVEN CONVERSATION METHODS  
    # =============================================================================
    
    async def _get_llm_discovery_decision(
        self,
        conversation_history: List[Dict[str, str]],
        collected_data: CollectedBusinessData,
        context
    ) -> Dict[str, Any]:
        """
        Single LLM call to decide: continue discovery or complete discovery.
        This matches your exact requirements for the interactive discovery loop.
        """
        
        discovery_prompt = self._build_discovery_decision_prompt(
            conversation_history, collected_data, context
        )
        
        try:
            response = await self.llm_client.chat_completion([
                {
                    "role": "system", 
                    "content": "You are the Rebase Discovery Agent. Follow the instructions exactly. Respond with either a simple next_question string or a JSON completion object."
                },
                {"role": "user", "content": discovery_prompt}
            ])
            
            # Parse LLM response - handle both formats
            content = response.content.strip()
            
            # Try to parse as JSON first (completion case)
            try:
                decision = json.loads(content)
                if decision.get("status") == "complete":
                    return decision
            except json.JSONDecodeError:
                pass
            
            # If not JSON, treat as simple next_question string
            return {
                "next_question": content,
                "reasoning": "Continuing discovery process",
                "progress_percentage": 15.0,
                "confidence": 0.8
            }
            
        except Exception as e:
            try:
                logger.warning(f"LLM discovery decision failed, using fallback: {e}")
            except:
                print(f"LLM discovery decision failed, using fallback: {e}")
            
            # Fallback decision logic
            completeness = collected_data.get_completeness_score()
            if completeness >= 0.7:
                return {
                    "status": "complete",
                    "summary": collected_data.to_dict(),
                    "completeness_score": completeness,
                    "confidence": 0.8
                }
            else:
                missing = collected_data.get_missing_categories()
                return {
                    "next_question": f"Could you tell me more about {missing[0] if missing else 'your current situation'}?",
                    "reasoning": "Need more information for complete business case",
                    "progress_percentage": completeness * 25,
                    "confidence": 0.6
                }
    
    async def _generate_completion_response(
        self,
        llm_decision: Dict[str, Any],
        collected_data: CollectedBusinessData,
        context
    ) -> Tuple[str, str, float, Optional[str]]:
        """Generate response when discovery is complete and ready for next phase."""
        
        completeness = llm_decision.get("completeness_score", 0.0)
        
        response = f"""
Perfect! I've gathered enough information to move forward. Based on our conversation, I can see we have {completeness:.0%} of the key information needed.

Here's what I've captured:
• Business Goals: {len(collected_data.business_goals)} identified
• Pain Points: {len(collected_data.pain_points)} documented  
• Stakeholders: {len(collected_data.decision_makers)} decision makers mapped
• Technical Context: {'Complete' if collected_data.current_technology else 'Partial'}

Let me now analyze your current system to provide accurate ROI calculations and recommendations. This will take a moment...
        """.strip()
        
        return response, "assessment", 30.0, "proceed_to_assessment"
    

    
    async def _update_collected_data(
        self,
        collected_data: CollectedBusinessData,
        llm_decision: Dict[str, Any]
    ) -> CollectedBusinessData:
        """Update collected data with LLM response, handling both extracted_data and completion summary."""
        
        # Handle completion summary (when status = "complete")
        if llm_decision.get("status") == "complete":
            summary = llm_decision.get("summary", {})
            
            # Map LLM summary fields to our data model
            if "business_goals" in summary:
                goals = summary["business_goals"]
                if isinstance(goals, list):
                    collected_data.business_goals.extend(goals)
                elif isinstance(goals, str):
                    collected_data.business_goals.append(goals)
            
            if "pain_points" in summary:
                pain_points = summary["pain_points"]
                if isinstance(pain_points, list):
                    for point in pain_points:
                        if isinstance(point, str):
                            collected_data.pain_points.append({
                                "description": point,
                                "impact": "unknown", 
                                "frequency": "unknown"
                            })
                        elif isinstance(point, dict):
                            collected_data.pain_points.append(point)
            
            # Map key_metrics → key_metrics field
            if "key_metrics" in summary:
                metrics = summary["key_metrics"]
                if isinstance(metrics, list):
                    collected_data.key_metrics.extend(metrics)
                elif isinstance(metrics, str):
                    collected_data.key_metrics.append(metrics)
            
            # Map constraints → timeline_constraints and business_constraints
            if "constraints" in summary:
                constraints = summary["constraints"]
                if isinstance(constraints, list):
                    for constraint in constraints:
                        if "timeline" in str(constraint).lower() or "time" in str(constraint).lower():
                            collected_data.timeline_constraints["constraint"] = constraint
                        else:
                            collected_data.business_constraints.append(constraint)
            
            # Map stakeholders → decision_makers, affected_users, technical_contacts
            if "stakeholders" in summary:
                stakeholders = summary["stakeholders"]
                if isinstance(stakeholders, list):
                    for stakeholder in stakeholders:
                        # Simple heuristic to categorize stakeholders
                        if any(role in str(stakeholder).lower() for role in ["cto", "manager", "director", "vp"]):
                            collected_data.decision_makers.append(stakeholder)
                        elif any(role in str(stakeholder).lower() for role in ["dev", "engineer", "tech"]):
                            collected_data.technical_contacts.append(stakeholder)
                        else:
                            collected_data.affected_users.append(stakeholder)
            
            # Map urgency → urgency_factors and risk_tolerance
            if "urgency" in summary:
                urgency = summary["urgency"]
                if urgency in ["low", "moderate", "high"]:
                    collected_data.risk_tolerance = urgency
                collected_data.urgency_factors.append({
                    "factor": "business_priority",
                    "severity": urgency
                })
        
        # Handle incremental extracted_data (during discovery)
        extracted = llm_decision.get("extracted_data", {})
        if extracted:
            # Update business goals
            if "business_goals" in extracted:
                new_goals = extracted["business_goals"]
                if isinstance(new_goals, list):
                    collected_data.business_goals.extend(new_goals)
                elif isinstance(new_goals, str):
                    collected_data.business_goals.append(new_goals)
            
            # Update pain points
            if "pain_points" in extracted:
                pain_points = extracted["pain_points"]
                if isinstance(pain_points, list):
                    for point in pain_points:
                        if isinstance(point, str):
                            collected_data.pain_points.append({
                                "description": point,
                                "impact": "unknown",
                                "frequency": "unknown"
                            })
                        elif isinstance(point, dict):
                            collected_data.pain_points.append(point)
            
            # Update stakeholders
            if "stakeholders" in extracted:
                stakeholders = extracted["stakeholders"]
                if isinstance(stakeholders, list):
                    collected_data.decision_makers.extend(stakeholders)
                elif isinstance(stakeholders, str):
                    collected_data.decision_makers.append(stakeholders)
        
        return collected_data
    

    
    def _generate_contextual_suggestions(
        self,
        phase: str,
        llm_decision: Dict[str, Any],
        collected_data: CollectedBusinessData
    ) -> List[str]:
        """Generate contextual suggested responses."""
        
        if phase == "discovery":
            missing = llm_decision.get("missing_critical_info", [])
            if "business_context" in missing:
                return [
                    "Let me explain our main business drivers",
                    "Here are the specific problems we're facing",
                    "Our key goals for this transformation are..."
                ]
            elif "financial_context" in missing:
                return [
                    "Our budget range is...",
                    "We're expecting ROI of...", 
                    "The current costs are..."
                ]
            elif "stakeholder_mapping" in missing:
                return [
                    "The decision makers are...",
                    "Our development team consists of...",
                    "The users affected include..."
                ]
            else:
                return [
                    "That's exactly right",
                    "Let me give you more details",
                    "I have some specific numbers"
                ]
        elif phase == "assessment":
            return [
                "Yes, proceed with the analysis",
                "I need more details on this",
                "What are the technical risks?"
            ]
        else:
            return [
                "Tell me more",
                "That makes sense", 
                "What's next?"
            ]
    
    # =============================================================================
    # PROMPT BUILDING METHODS
    # =============================================================================
    
    def _build_discovery_decision_prompt(
        self,
        conversation_history: List[Dict[str, str]],
        collected_data: CollectedBusinessData,
        context
    ) -> str:
        """Build prompt that matches your exact specification."""
        
        return f"""
You are the Rebase Discovery Agent.
Your goal is to guide the user through a structured discovery process for system modernization.
Use the following conversation so far:
{self._format_conversation_history(conversation_history)}

If important business areas are still missing (goals, pain points, metrics, constraints, stakeholders, urgency), ask the next most relevant question.

If you have sufficient information to summarize, output a structured JSON summary like:
{{
  "status": "complete",
  "summary": {{
    "business_goals": [...],
    "pain_points": [...],
    "key_metrics": [...],
    "constraints": [...],
    "stakeholders": [...],
    "urgency": "..."
  }}
}}

Otherwise, output a single next_question string.
"""
    

    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt inclusion."""
        
        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    # =============================================================================
    # FALLBACK METHODS
    # =============================================================================
    
