"""
Unified Chat Engine - LLM-driven conversational orchestrator for transformation analysis.

Single unified system that combines intelligent data collection, conversation flow,
and business discovery with the universal transformation engine.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re
from datetime import datetime, timezone

try:
    from loguru import logger
except ImportError:
    # Fallback logger for environments without loguru
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..context_manager import ContextManager


@dataclass
class DiscoveryCategory:
    """Represents a discovery category with progress tracking and current vs future state fields."""
    name: str
    progress: float = 0.0  # 0.0 to 1.0
    completion_status: str = "not_started"  # "not_started" | "in_progress" | "complete"
    summary: str = ""
    current_state: Dict[str, Any] = None  # Current/existing state data
    future_state: Dict[str, Any] = None   # Desired future state data
    
    def __post_init__(self):
        if self.current_state is None:
            self.current_state = {}
        if self.future_state is None:
            self.future_state = {}


@dataclass
class CollectedBusinessData:
    """Hierarchical business data collection with parent categories and child fields."""
    
    # Parent Categories (5 core discovery areas for ROI-focused analysis)
    business_goals: DiscoveryCategory = None
    stakeholders: DiscoveryCategory = None  
    current_problems: DiscoveryCategory = None
    key_metrics: DiscoveryCategory = None
    implementation_context: DiscoveryCategory = None
    
    def __post_init__(self):
        """Initialize discovery categories with their child fields."""
        
        # Initialize Business Goals category
        if self.business_goals is None:
            self.business_goals = DiscoveryCategory(
                name="Business Goals",
                current_state={},
                future_state={
                    "primary_objectives": [],     # Main business goals
                    "success_criteria": [],       # How success is measured
                    "kpis": [],                   # Key performance indicators
                    "strategic_alignment": "",    # How this fits company strategy
                    "timeline_goals": {}          # {"short_term": [], "long_term": []}
                }
            )
        
        # Initialize Stakeholders category
        if self.stakeholders is None:
            self.stakeholders = DiscoveryCategory(
                name="Stakeholders",
                current_state={
                    "decision_makers": [],        # [{"name": str, "role": str, "influence": str}]
                    "technical_team": [],         # Engineering stakeholders
                    "business_users": [],         # End users and business stakeholders
                    "external_stakeholders": [],  # Customers, partners, vendors
                    "project_sponsors": []        # Executive sponsors
                },
                future_state={
                    "communication_plan": {},     # How to keep stakeholders informed
                    "change_management": [],      # Training, adoption strategies
                    "resource_needs": {}          # Additional team members needed
                }
            )
        
        # Initialize Current Problems category  
        if self.current_problems is None:
            self.current_problems = DiscoveryCategory(
                name="Current Problems",
                current_state={
                    "technical_issues": [],       # Technical debt, legacy problems
                    "process_inefficiencies": [], # Workflow problems
                    "user_complaints": [],        # User-reported issues
                    "security_risks": [],         # Current security vulnerabilities
                    "compliance_risks": [],       # Regulatory compliance gaps
                    "reliability_issues": [],     # System downtime, failures
                    "operational_risks": [],      # Maintenance, support issues
                    "cost_drains": []             # Areas causing financial loss
                },
                future_state={}  # Problems should be resolved, so future state is empty
            )
        
        # Initialize Key Metrics category
        if self.key_metrics is None:
            self.key_metrics = DiscoveryCategory(
                name="Key Metrics",
                current_state={
                    "performance_metrics": {},    # {"response_time": "2s", "throughput": "100/min"}
                    "business_metrics": {},       # {"revenue": "$1M", "conversion_rate": "2%"}
                    "operational_metrics": {},    # {"uptime": "99%", "error_rate": "5%"}
                    "operational_costs": {},      # {"infrastructure": "$5k/month", "maintenance": "$2k/month", "licenses": "$1k/month"}
                    "user_metrics": {},           # {"satisfaction": "6/10", "adoption": "60%"}
                    "security_metrics": {}        # {"incidents": "5/month", "vulnerabilities": "20"}
                },
                future_state={
                    "performance_targets": {},    # Target performance metrics
                    "business_targets": {},       # Target business metrics  
                    "operational_targets": {},    # Target operational metrics
                    "cost_savings_targets": {},   # Target operational cost reductions
                    "user_targets": {},           # Target user experience
                    "security_targets": {}        # Target security improvements
                }
            )
        
        # Initialize Implementation Context category
        if self.implementation_context is None:
            self.implementation_context = DiscoveryCategory(
                name="Implementation Context",
                current_state={
                    "team_capacity": {},          # Current team size, skills, availability
                    "technical_constraints": [], # Current system limitations
                    "organizational_readiness": {} # Change management readiness
                },
                future_state={
                    "project_budget": {},         # {"max_investment": float, "budget_flexibility": str, "funding_source": str}
                    "resource_plan": {},          # {"team_size_needed": int, "expertise_required": [], "external_help": bool}
                    "timeline_requirements": {},  # {"hard_deadline": str, "preferred_timeline": str}
                    "regulatory_compliance": [],  # Compliance requirements to meet
                    "business_constraints": [],   # Organizational limitations
                    "implementation_risks": []    # Project execution risks
                }
            )
    
    def get_category_progress(self, category_name: str) -> float:
        """Calculate progress for a specific discovery category."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return 0.0
        
        # Count non-empty fields in both current_state and future_state
        total_fields = len(category.current_state) + len(category.future_state)
        completed_fields = 0
        
        # Check current_state fields
        for field_name, field_value in category.current_state.items():
            if field_value:  # Not None and not empty
                if isinstance(field_value, list) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, dict) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, str) and field_value.strip():
                    completed_fields += 1
        
        # Check future_state fields  
        for field_name, field_value in category.future_state.items():
            if field_value:  # Not None and not empty
                if isinstance(field_value, list) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, dict) and len(field_value) > 0:
                    completed_fields += 1
                elif isinstance(field_value, str) and field_value.strip():
                    completed_fields += 1
        
        progress = completed_fields / total_fields if total_fields > 0 else 0.0
        category.progress = progress
        
        # Update completion status
        if progress == 0.0:
            category.completion_status = "not_started"
        elif progress < 1.0:
            category.completion_status = "in_progress"
        else:
            category.completion_status = "complete"
        
        return progress
    
    def get_overall_completeness_score(self) -> float:
        """Calculate overall discovery completeness across all categories."""
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        total_progress = sum(self.get_category_progress(cat) for cat in categories)
        return total_progress / len(categories)
    
    def get_missing_categories(self) -> List[str]:
        """Get categories that need more information."""
        missing = []
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        
        for cat_name in categories:
            progress = self.get_category_progress(cat_name)
            if progress < 0.5:  # Less than 50% complete
                missing.append(cat_name)
        
        return missing
    
    def update_category_field(self, category_name: str, field_name: str, value: Any, state_type: str = "current_state"):
        """Update a specific field within a category's current or future state."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return
        
        # Get the appropriate state dict
        state_dict = category.current_state if state_type == "current_state" else category.future_state
        
        if field_name in state_dict:
            if isinstance(value, list) and isinstance(state_dict[field_name], list):
                state_dict[field_name].extend(value)
            else:
                state_dict[field_name] = value
        
        # Update progress after modification
        self.get_category_progress(category_name)
        
        # Generate category summary
        self._update_category_summary(category_name)
    
    def _update_category_summary(self, category_name: str):
        """Generate a human-readable summary for a category based on its current and future state fields."""
        category = getattr(self, category_name.lower().replace(" ", "_"))
        if not category:
            return
        
        if category_name == "business_goals":
            objectives = category.future_state.get("primary_objectives", [])
            kpis = category.future_state.get("kpis", [])
            summary_parts = []
            if objectives:
                summary_parts.append(f"{len(objectives)} primary objectives")
            if kpis:
                summary_parts.append(f"{len(kpis)} KPIs defined")
            category.summary = ", ".join(summary_parts) if summary_parts else "No goals defined yet"
            
        elif category_name == "current_problems":
            tech_issues = category.current_state.get("technical_issues", [])
            security_risks = category.current_state.get("security_risks", [])
            summary_parts = []
            if tech_issues:
                summary_parts.append(f"{len(tech_issues)} technical issues")
            if security_risks:
                summary_parts.append(f"{len(security_risks)} security risks")
            category.summary = ", ".join(summary_parts) if summary_parts else "No problems identified"
            
        elif category_name == "stakeholders":
            decision_makers = category.current_state.get("decision_makers", [])
            team = category.current_state.get("technical_team", [])
            users = category.current_state.get("business_users", [])
            total_stakeholders = len(decision_makers) + len(team) + len(users)
            category.summary = f"{total_stakeholders} stakeholders identified" if total_stakeholders > 0 else "No stakeholders identified"
            
        elif category_name == "key_metrics":
            current_metrics = len([v for v in category.current_state.values() if v])
            target_metrics = len([v for v in category.future_state.values() if v])
            
            # Check for operational costs specifically
            operational_costs = category.current_state.get("operational_costs", {})
            cost_savings = category.future_state.get("cost_savings_targets", {})
            
            summary_parts = []
            if current_metrics > 0:
                summary_parts.append(f"{current_metrics} current metrics")
            if target_metrics > 0:
                summary_parts.append(f"{target_metrics} targets")
            if operational_costs:
                summary_parts.append(f"operational costs tracked")
            if cost_savings:
                summary_parts.append(f"savings targets set")
                
            category.summary = ", ".join(summary_parts) if summary_parts else "No metrics defined"
        
        elif category_name == "implementation_context":
            current_context = len([v for v in category.current_state.values() if v and (isinstance(v, list) and len(v) > 0 or isinstance(v, dict) and len(v) > 0 or isinstance(v, str) and v.strip())])
            future_context = len([v for v in category.future_state.values() if v and (isinstance(v, list) and len(v) > 0 or isinstance(v, dict) and len(v) > 0 or isinstance(v, str) and v.strip())])
            
            # Check for project budget specifically
            project_budget = category.future_state.get("project_budget", {})
            resource_plan = category.future_state.get("resource_plan", {})
            
            summary_parts = []
            if current_context > 0:
                summary_parts.append(f"{current_context} current constraints")
            if project_budget:
                summary_parts.append("project budget defined")
            if resource_plan:
                summary_parts.append("resource plan set")
                
            category.summary = ", ".join(summary_parts) if summary_parts else "Implementation context not defined"
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        """Get a complete discovery summary for display."""
        categories = ["business_goals", "stakeholders", "current_problems", "key_metrics", "implementation_context"]
        summary = {
            "overall_progress": self.get_overall_completeness_score(),
            "categories": {}
        }
        
        for cat_name in categories:
            category = getattr(self, cat_name.lower().replace(" ", "_"))
            if category:
                summary["categories"][cat_name] = {
                    "name": category.name,
                    "progress": category.progress,
                    "status": category.completion_status,
                    "summary": category.summary,
                    "current_state": category.current_state,
                    "future_state": category.future_state
                }
        
        return summary
    
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
        context_manager: ContextManager
    ):
        self.llm_client = llm_client
        self.context_manager = context_manager
        
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
            # Create new session directly using context manager
            session_id = self.context_manager.create_session(
                initial_message=initial_message,
                user_id=user_context.get("user_id") if user_context else None,
                domain_type="framework_migration"  # Default, can be refined later
            )
            
            # Initialize business data collection for this session
            self.session_business_data[session_id] = CollectedBusinessData()
            
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
                    logger.info(f"Processing extracted data: {llm_decision['extracted_data']}")
                    collected_data = await self._update_collected_data(collected_data, llm_decision)
                    self.session_business_data[session_id] = collected_data
                    logger.info(f"Updated session data. New completeness: {collected_data.get_overall_completeness_score()}")
                else:
                    logger.info("No extracted_data found in LLM decision")
            
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
                collected_data=collected_data.to_dict() if collected_data else {},
                discovery_summary=collected_data.get_discovery_summary() if collected_data else {},
                data_completeness=llm_decision.get("completeness_score", 0.0),
                missing_critical_info=llm_decision.get("missing_critical_info", []),
                extraction_confidence=llm_decision.get("confidence", 0.0),
                next_question_reasoning=llm_decision.get("reasoning", "LLM-driven discovery"),
                action_required=action_required,
                structured_data=llm_decision.get("structured_data", {}),
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
                collected_data={},
                discovery_summary={},
                data_completeness=0.0,
                missing_critical_info=[],
                extraction_confidence=0.0,
                next_question_reasoning="Error recovery",
                action_required=None,
                structured_data={},
                confidence_level=0.0
            )
    
    async def get_discovery_summary(self, session_id: str) -> Dict[str, Any]:
        """Get the discovery summary for a session."""
        collected_data = self.session_business_data.get(session_id)
        if collected_data:
            return collected_data.get_discovery_summary()
        return {}
    
    async def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation and current status."""
        
        context = self.context_manager.get_context(session_id)
        
        if not context:
            return {"error": "Session not found"}
        
        # Get business data if available
        collected_data = self.session_business_data.get(session_id)
        overall_progress = collected_data.get_overall_completeness_score() * 100 if collected_data else 0.0
        
        return {
            "session_id": session_id,
            "domain_type": context.domain_type or "framework_migration",
            "current_phase": context.current_phase,
            "progress_percentage": overall_progress,
            "discovery_summary": collected_data.get_discovery_summary() if collected_data else {},
            "data_completeness": overall_progress / 100.0,
            "missing_categories": collected_data.get_missing_categories() if collected_data else [],
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
            intent = await self._classify_intent(message, context)
            
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
    
    async def _classify_intent(self, message: str, context) -> ConversationIntent:
        """Classify user intent using LLM with fallback to rule-based approach."""
        
        # Build intent classification prompt
        intent_prompt = f"""
Classify the user's intent based on their message and conversation context.

USER MESSAGE: "{message}"
CONVERSATION PHASE: {context.current_phase}
PREVIOUS MESSAGES: {len(context.conversation_history)} messages exchanged

POSSIBLE INTENTS:
- START_TRANSFORMATION: User wants to begin a system modernization/migration project
- ANSWER_QUESTION: User is providing information or answering a discovery question  
- REQUEST_CLARIFICATION: User wants explanation or clarification about something
- APPROVE_BUSINESS_CASE: User is approving/accepting a proposed plan or recommendation
- REQUEST_MORE_INFO: User wants additional details or information
- GENERAL_CHAT: General conversation not related to transformation

Consider:
- The actual meaning, not just keywords
- Context of the conversation phase
- Cultural and linguistic variations
- Synonyms and different ways of expressing the same intent

Respond with only the intent name (e.g., "ANSWER_QUESTION").
"""

        try:
            response = await self.llm_client.chat_completion([
                {
                    "role": "system",
                    "content": "You are an intent classifier. Analyze the user's message and respond with only the intent classification."
                },
                {"role": "user", "content": intent_prompt}
            ])
            
            # Parse LLM response
            intent_str = response.content.strip().upper()
            
            # Map to enum
            intent_mapping = {
                "START_TRANSFORMATION": ConversationIntent.START_TRANSFORMATION,
                "ANSWER_QUESTION": ConversationIntent.ANSWER_QUESTION,
                "REQUEST_CLARIFICATION": ConversationIntent.REQUEST_CLARIFICATION,
                "APPROVE_BUSINESS_CASE": ConversationIntent.APPROVE_BUSINESS_CASE,
                "REQUEST_MORE_INFO": ConversationIntent.REQUEST_MORE_INFO,
                "GENERAL_CHAT": ConversationIntent.GENERAL_CHAT
            }
            
            if intent_str in intent_mapping:
                return intent_mapping[intent_str]
            else:
                # Fallback if LLM returns unexpected value
                return self._fallback_intent_classification(message, context)
                
        except Exception as e:
            try:
                logger.warning(f"LLM intent classification failed, using fallback: {e}")
            except:
                print(f"LLM intent classification failed, using fallback: {e}")
            
            # Fallback to rule-based approach
            return self._fallback_intent_classification(message, context)
    
    def _fallback_intent_classification(self, message: str, context) -> ConversationIntent:
        """Fallback rule-based intent classification for when LLM is unavailable."""
        
        message_lower = message.lower()
        
        # Check for transformation start keywords (more comprehensive)
        transformation_words = ["migrate", "convert", "upgrade", "modernize", "transform", 
                              "update", "refactor", "rebuild", "rewrite", "improve"]
        if any(word in message_lower for word in transformation_words):
            return ConversationIntent.START_TRANSFORMATION
        
        # Check for approval keywords (more comprehensive)
        approval_words = ["yes", "approve", "proceed", "go ahead", "sounds good", 
                         "that works", "okay", "ok", "agreed", "accept", "confirmed"]
        if any(word in message_lower for word in approval_words):
            return ConversationIntent.APPROVE_BUSINESS_CASE
        
        # Check for clarification requests
        clarification_words = ["what", "how", "why", "explain", "clarify", "help me understand"]
        if any(word in message_lower for word in clarification_words):
            return ConversationIntent.REQUEST_CLARIFICATION
        
        # Check for information requests
        info_words = ["more", "details", "tell me", "show me", "additional", "further"]
        if any(word in message_lower for word in info_words):
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
            collected_data={},
            discovery_summary={},
            data_completeness=0.0,
            missing_critical_info=[],
            extraction_confidence=0.0,
            next_question_reasoning="Completion phase response",
            action_required=action_required,
            structured_data=structured_data or {},
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
            # But also try to extract data from the latest user message
            extracted_data = await self._extract_data_from_conversation(conversation_history, collected_data)
            
            return {
                "next_question": content,
                "reasoning": "Continuing discovery process",
                "progress_percentage": self._calculate_progress_from_data(collected_data, extracted_data),
                "confidence": 0.8,
                "extracted_data": extracted_data
            }
            
        except Exception as e:
            try:
                logger.warning(f"LLM discovery decision failed, using fallback: {e}")
            except:
                print(f"LLM discovery decision failed, using fallback: {e}")
            
            # Fallback decision logic
            completeness = collected_data.get_overall_completeness_score()
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
        
        # Get some basic stats from the hierarchical categories
        goals_count = len(collected_data.business_goals.future_state.get("primary_objectives", [])) if collected_data.business_goals else 0
        problems_count = len(collected_data.current_problems.current_state.get("technical_issues", [])) + len(collected_data.current_problems.current_state.get("security_risks", [])) if collected_data.current_problems else 0
        stakeholder_count = (
            len(collected_data.stakeholders.current_state.get("decision_makers", [])) +
            len(collected_data.stakeholders.current_state.get("technical_team", [])) +
            len(collected_data.stakeholders.current_state.get("business_users", []))
        ) if collected_data.stakeholders else 0
        
        response = f"""
Perfect! I've gathered enough information to move forward. Based on our conversation, I can see we have {completeness:.0%} of the key information needed.

Here's what I've captured:
• Business Goals: {goals_count} objectives identified
• Current Problems: {problems_count} issues documented  
• Stakeholders: {stakeholder_count} stakeholders mapped
• Discovery Status: {len([cat for cat in ['business_goals', 'stakeholders', 'current_problems', 'key_metrics', 'implementation_context'] if getattr(collected_data, cat) and getattr(collected_data, cat).progress > 0])}/5 categories started

Let me now analyze your current system to provide accurate ROI calculations and recommendations. This will take a moment...
        """.strip()
        
        return response, "assessment", 30.0, "proceed_to_assessment"
    

    
    async def _update_collected_data(
        self,
        collected_data: CollectedBusinessData,
        llm_decision: Dict[str, Any]
    ) -> CollectedBusinessData:
        """Update collected data with LLM response, using hierarchical category model."""
        
        # Handle completion summary (when status = "complete")
        if llm_decision.get("status") == "complete":
            summary = llm_decision.get("summary", {})
            self._process_completion_summary(summary, collected_data)
        
        # Handle incremental extracted_data (during discovery)
        extracted = llm_decision.get("extracted_data", {})
        if extracted:
            self._process_extracted_data(extracted, collected_data)
        
        return collected_data
    
    def _process_completion_summary(self, summary: Dict[str, Any], collected_data: CollectedBusinessData):
        """Process completion summary data into hierarchical categories."""
        
        # Business goals processing
        if "business_goals" in summary:
            goals = summary["business_goals"]
            if isinstance(goals, list):
                collected_data.update_category_field("business_goals", "primary_objectives", goals, "future_state")
            elif isinstance(goals, str):
                collected_data.update_category_field("business_goals", "primary_objectives", [goals], "future_state")
        
        # Current problems processing (renamed from pain_points)
        if "current_problems" in summary or "pain_points" in summary:
            problems = summary.get("current_problems", summary.get("pain_points", []))
            if isinstance(problems, list):
                for problem in problems:
                    if isinstance(problem, str):
                        collected_data.update_category_field("current_problems", "technical_issues", [problem], "current_state")
                    elif isinstance(problem, dict) and "description" in problem:
                        collected_data.update_category_field("current_problems", "technical_issues", [problem["description"]], "current_state")
        
        # Key metrics processing
        if "key_metrics" in summary:
            metrics = summary["key_metrics"]
            if isinstance(metrics, list):
                for metric in metrics:
                    if isinstance(metric, str):
                        collected_data.update_category_field("key_metrics", "performance_metrics", {metric: ""}, "current_state")
            elif isinstance(metrics, dict):
                collected_data.update_category_field("key_metrics", "performance_metrics", metrics, "current_state")
        
        # Operational costs processing (separate from project budget)
        if "operational_costs" in summary or "current_costs" in summary:
            costs = summary.get("operational_costs", summary.get("current_costs", {}))
            if isinstance(costs, dict):
                collected_data.update_category_field("key_metrics", "operational_costs", costs, "current_state")
        
        # Implementation context processing (project investment focus)
        if "implementation_context" in summary or "constraints" in summary or "project_budget" in summary:
            context_data = summary.get("implementation_context", summary.get("constraints", []))
            
            # Handle project budget separately
            if "project_budget" in summary:
                budget_info = summary["project_budget"]
                if isinstance(budget_info, dict):
                    collected_data.update_category_field("implementation_context", "project_budget", budget_info, "future_state")
            
            # Handle other context items
            if isinstance(context_data, list):
                for item in context_data:
                    if isinstance(item, str):
                        if "timeline" in item.lower() or "deadline" in item.lower():
                            collected_data.update_category_field("implementation_context", "timeline_requirements", [item], "future_state")
                        elif "team" in item.lower() or "resource" in item.lower():
                            collected_data.update_category_field("implementation_context", "resource_plan", [item], "future_state")
                        else:
                            collected_data.update_category_field("implementation_context", "business_constraints", [item], "future_state")
        
        # Stakeholders processing
        if "stakeholders" in summary:
            stakeholders = summary["stakeholders"]
            if isinstance(stakeholders, list):
                for stakeholder in stakeholders:
                    if isinstance(stakeholder, str):
                        # Categorize stakeholder type
                        if any(role in stakeholder.lower() for role in ["cto", "manager", "director", "vp", "ceo", "lead"]):
                            collected_data.update_category_field("stakeholders", "decision_makers", [stakeholder], "current_state")
                        elif any(role in stakeholder.lower() for role in ["dev", "engineer", "tech", "architect"]):
                            collected_data.update_category_field("stakeholders", "technical_team", [stakeholder], "current_state")
                        else:
                            collected_data.update_category_field("stakeholders", "business_users", [stakeholder], "current_state")
    
    def _process_extracted_data(self, extracted: Dict[str, Any], collected_data: CollectedBusinessData):
        """Process incremental extracted data into hierarchical categories."""
        logger.info(f"Processing extracted data: {extracted}")
        
        # Handle business_goals with nested structure
        if "business_goals" in extracted:
            logger.info("Processing business goals")
            goals_data = extracted["business_goals"]
            if isinstance(goals_data, dict) and "primary_objectives" in goals_data:
                objectives = goals_data["primary_objectives"]
                if isinstance(objectives, list):
                    for obj in objectives:
                        collected_data.update_category_field("business_goals", "primary_objectives", [obj], "future_state")
                        logger.info(f"Added business goal: {obj}")
            elif isinstance(goals_data, list):
                for obj in goals_data:
                    collected_data.update_category_field("business_goals", "primary_objectives", [obj], "future_state")
                    logger.info(f"Added business goal: {obj}")
        
        # Handle current_problems with nested structure
        if "current_problems" in extracted:
            logger.info("Processing current problems")
            problems_data = extracted["current_problems"]
            if isinstance(problems_data, dict) and "technical_issues" in problems_data:
                issues = problems_data["technical_issues"]
                if isinstance(issues, list):
                    for issue in issues:
                        collected_data.update_category_field("current_problems", "technical_issues", [issue], "current_state")
                        logger.info(f"Added technical issue: {issue}")
            elif isinstance(problems_data, list):
                for issue in problems_data:
                    collected_data.update_category_field("current_problems", "technical_issues", [issue], "current_state")
                    logger.info(f"Added technical issue: {issue}")
        
        # Handle implementation_context with nested structure
        if "implementation_context" in extracted:
            logger.info("Processing implementation context")
            context_data = extracted["implementation_context"]
            if isinstance(context_data, dict):
                for key, value in context_data.items():
                    if key in ["current_technology", "technology_type", "project_type", "project_timeline"]:
                        collected_data.update_category_field("implementation_context", key, [value] if isinstance(value, str) else value, "current_state")
                        logger.info(f"Added implementation context {key}: {value}")
                    else:
                        collected_data.update_category_field("implementation_context", "business_constraints", [f"{key}: {value}"], "future_state")
                        logger.info(f"Added business constraint {key}: {value}")
        
        # Handle key_metrics
        if "key_metrics" in extracted:
            logger.info("Processing key metrics")
            metrics_data = extracted["key_metrics"]
            if isinstance(metrics_data, dict):
                for key, value in metrics_data.items():
                    collected_data.update_category_field("key_metrics", key, [value] if isinstance(value, str) else value, "current_state")
                    logger.info(f"Added key metric {key}: {value}")
            elif isinstance(metrics_data, list):
                for metric in metrics_data:
                    collected_data.update_category_field("key_metrics", "performance_metrics", [metric], "current_state")
                    logger.info(f"Added performance metric: {metric}")
        
        # Handle stakeholders
        if "stakeholders" in extracted:
            logger.info("Processing stakeholders")
            stakeholders_data = extracted["stakeholders"]
            if isinstance(stakeholders_data, dict) and "key_decision_makers" in stakeholders_data:
                decision_makers = stakeholders_data["key_decision_makers"]
                if isinstance(decision_makers, list):
                    for dm in decision_makers:
                        collected_data.update_category_field("stakeholders", "key_decision_makers", [dm], "current_state")
                        logger.info(f"Added stakeholder: {dm}")
            elif isinstance(stakeholders_data, list):
                for stakeholder in stakeholders_data:
                    collected_data.update_category_field("stakeholders", "business_users", [stakeholder], "current_state")
                    logger.info(f"Added stakeholder: {stakeholder}")
    

    
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
        """Build prompt for LLM to make intelligent discovery decisions."""
        
        # Calculate current data completeness
        completeness = collected_data.get_overall_completeness_score()
        missing_categories = collected_data.get_missing_categories()
        
        # Get summary of what we have vs what we need
        discovery_summary = collected_data.get_discovery_summary()
        
        return f"""
You are the Rebase Discovery Agent for system modernization ROI analysis.

CONVERSATION HISTORY:
{self._format_conversation_history(conversation_history)}

CURRENT DISCOVERY STATE:
Completeness: {completeness:.1%}
Categories with data: {len([cat for cat in discovery_summary['categories'] if discovery_summary['categories'][cat]['progress'] > 0])}/5
Missing critical categories: {', '.join(missing_categories) if missing_categories else 'None'}

DATA COLLECTED SO FAR:
{self._format_detailed_data_summary(collected_data)}

DISCOVERY COMPLETION CRITERIA:
You have enough data to generate an ROI analysis when you have:
1. At least 2 clear business objectives
2. Current system problems/pain points identified
3. Key stakeholders identified (at least decision makers)
4. Some indication of budget/cost constraints
5. Basic understanding of current technology/system

DECISION LOGIC:
- If completeness ≥ 60% AND you have the minimum criteria above → COMPLETE
- If critical ROI information is still missing → CONTINUE with specific question
- Ask targeted questions to fill the biggest gaps

RESPONSE FORMAT:
If ready to complete:
{{
  "status": "complete",
  "summary": "Discovery complete - sufficient data for ROI analysis",
  "completeness_score": {completeness},
  "confidence": 0.8
}}

If continuing discovery, return ONLY the next question text (no JSON):
Ask a specific, targeted question to fill the biggest information gap. Examples:
- "What specific business goals are driving this modernization?"
- "What problems are you experiencing with the current system?"
- "Who are the key decision makers for this project?"
- "What's your rough budget range for this modernization?"

Focus on gathering actionable business information for ROI calculation.
"""
    

    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt inclusion."""
        
        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    def _format_collected_data_summary(self, collected_data: CollectedBusinessData) -> str:
        """Format collected business data for prompt context."""
        if not collected_data:
            return "No data collected yet."
        
        summary = []
        
        # Business Goals
        if collected_data.business_goals and collected_data.business_goals.progress > 0:
            goals = collected_data.business_goals.future_state.get('primary_objectives', [])
            if goals:
                summary.append(f"Business Goals ({len(goals)}): {', '.join(goals[:2])}")
        
        # Current Problems  
        if collected_data.current_problems and collected_data.current_problems.progress > 0:
            problems = collected_data.current_problems.current_state.get('technical_issues', [])
            if problems:
                summary.append(f"Current Problems ({len(problems)}): {', '.join(problems[:2])}")
            
        # Key Metrics
        if collected_data.key_metrics and collected_data.key_metrics.progress > 0:
            metrics = collected_data.key_metrics.current_state
            metric_items = [f"{k}: {v}" for k, v in metrics.items() if v]
            if metric_items:
                summary.append(f"Metrics: {', '.join(metric_items[:2])}")
            
        # Implementation Context
        if collected_data.implementation_context and collected_data.implementation_context.progress > 0:
            context = collected_data.implementation_context.current_state
            context_items = [f"{k}: {v}" for k, v in context.items() if v]
            if context_items:
                summary.append(f"Context: {', '.join(context_items[:2])}")
        
        # Stakeholders
        if collected_data.stakeholders and collected_data.stakeholders.progress > 0:
            stakeholders = collected_data.stakeholders.current_state.get('decision_makers', [])
            if stakeholders:
                summary.append(f"Stakeholders ({len(stakeholders)}): {', '.join(stakeholders[:2])}")
        
        if not summary:
            return "Discovery just starting - minimal data collected."
            
        return "\n".join(summary)
    
    def _format_detailed_data_summary(self, collected_data: CollectedBusinessData) -> str:
        """Format detailed data summary for LLM decision making."""
        if not collected_data:
            return "No data collected."
        
        summary_parts = []
        
        # Business Goals
        if collected_data.business_goals and collected_data.business_goals.progress > 0:
            goals = collected_data.business_goals.future_state.get('primary_objectives', [])
            summary_parts.append(f"✓ Business Goals: {len(goals)} objectives defined")
        else:
            summary_parts.append("✗ Business Goals: Not identified")
        
        # Current Problems
        if collected_data.current_problems and collected_data.current_problems.progress > 0:
            issues = collected_data.current_problems.current_state.get('technical_issues', [])
            summary_parts.append(f"✓ Current Problems: {len(issues)} issues identified")
        else:
            summary_parts.append("✗ Current Problems: Not identified")
        
        # Stakeholders
        if collected_data.stakeholders and collected_data.stakeholders.progress > 0:
            decision_makers = collected_data.stakeholders.current_state.get('decision_makers', [])
            summary_parts.append(f"✓ Stakeholders: {len(decision_makers)} decision makers identified")
        else:
            summary_parts.append("✗ Stakeholders: Not identified")
        
        # Key Metrics (budget/costs)
        if collected_data.key_metrics and collected_data.key_metrics.progress > 0:
            metrics = collected_data.key_metrics.current_state
            has_budget = any('budget' in str(v).lower() or 'cost' in str(v).lower() for v in metrics.values())
            if has_budget:
                summary_parts.append("✓ Financial Info: Budget/cost information available")
            else:
                summary_parts.append("✓ Metrics: Some metrics collected")
        else:
            summary_parts.append("✗ Financial Info: No budget/cost information")
        
        # Implementation Context
        if collected_data.implementation_context and collected_data.implementation_context.progress > 0:
            context = collected_data.implementation_context.current_state
            tech_info = any('tech' in str(v).lower() or 'react' in str(v).lower() for v in context.values())
            if tech_info:
                summary_parts.append("✓ Technical Context: Current technology identified")
            else:
                summary_parts.append("✓ Context: Some implementation details")
        else:
            summary_parts.append("✗ Technical Context: Current system not described")
        
        return "\n".join(summary_parts)
    
    async def _extract_data_from_conversation(self, conversation_history: List[Dict[str, str]], collected_data: CollectedBusinessData) -> Dict[str, Any]:
        """Extract business data from conversation using LLM intelligence."""
        if not conversation_history:
            return {}
        
        # Get the last few messages for context
        recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        # Build context of what we already know
        current_data_summary = self._format_collected_data_summary(collected_data)
        
        extraction_prompt = f"""
You are a business data extraction expert. Analyze the conversation and extract structured business information.

RECENT CONVERSATION:
{self._format_conversation_history(recent_messages)}

ALREADY COLLECTED:
{current_data_summary}

EXTRACT DATA IN JSON FORMAT:
Based on the conversation, extract any new business information that fits these categories:

{{
  "business_goals": {{
    "primary_objectives": ["list of business goals/objectives mentioned"]
  }},
  "current_problems": {{
    "technical_issues": ["list of technical problems/issues mentioned"],
    "performance_issues": ["list of performance problems"],
    "operational_issues": ["list of operational problems"]
  }},
  "key_metrics": {{
    "budget_info": "budget amount if mentioned",
    "cost_info": "current costs if mentioned", 
    "user_scale": "user count/scale if mentioned",
    "timeline": "timeline information if mentioned"
  }},
  "stakeholders": {{
    "key_decision_makers": ["names and roles of decision makers"],
    "team_members": ["team members mentioned"]
  }},
  "implementation_context": {{
    "current_technology": "current tech stack mentioned",
    "project_type": "type of transformation",
    "constraints": ["any constraints or requirements mentioned"]
  }}
}}

RULES:
1. Only extract information that is explicitly mentioned in the conversation
2. Don't make assumptions or infer information not clearly stated
3. Use the exact terminology from the conversation
4. If no relevant information is found in a category, omit that category
5. Focus on NEW information not already collected

Return ONLY the JSON object, no explanations.
"""

        try:
            response = await self.llm_client.chat_completion([
                {
                    "role": "system",
                    "content": "You are a data extraction expert. Extract business information from conversations and return structured JSON."
                },
                {"role": "user", "content": extraction_prompt}
            ])
            
            # Parse LLM response
            content = response.content.strip()
            
            # Try to parse as JSON
            try:
                extracted_data = json.loads(content)
                logger.info(f"LLM extracted data: {extracted_data}")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.warning(f"LLM returned invalid JSON: {content}")
                return {}
                
        except Exception as e:
            logger.error(f"LLM data extraction failed: {e}")
            # Only fall back to minimal extraction if LLM completely fails
            return self._minimal_fallback_extraction(recent_messages)
    
    def _minimal_fallback_extraction(self, recent_messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Minimal fallback extraction for when LLM is unavailable."""
        # Only extract very obvious things like explicit budget numbers
        extracted = {}
        
        last_message = ""
        for msg in reversed(recent_messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "").lower()
                break
        
        if not last_message:
            return {}
        
        # Only extract explicit budget/cost numbers
        budget_matches = re.findall(r'(\d+)\s*m(?:illion)?', last_message)
        if budget_matches and any(word in last_message for word in ["budget", "cost", "million"]):
            if "budget" in last_message:
                extracted["key_metrics"] = {"budget_info": f"${budget_matches[0]}M"}
            elif "cost" in last_message:
                extracted["key_metrics"] = {"cost_info": f"${budget_matches[0]}M"}
        
        logger.info(f"Fallback extracted: {extracted}")
        return extracted
    
    def _calculate_progress_from_data(self, collected_data: CollectedBusinessData, new_extracted_data: Dict[str, Any]) -> float:
        """Calculate progress percentage based on collected data."""
        # Simulate updating data to calculate what the progress would be
        temp_data = collected_data
        if new_extracted_data:
            self._process_extracted_data(new_extracted_data, temp_data)
        
        # Calculate overall completeness
        return temp_data.get_overall_completeness_score() * 100
    
    # =============================================================================
    # FALLBACK METHODS
    # =============================================================================
    
