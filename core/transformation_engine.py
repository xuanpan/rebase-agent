"""
Universal Transformation Engine - Core orchestrator for the 4-phase workflow.

Orchestrates the universal transformation workflow (Discover → Assess → Justify → Plan)
across all transformation domains with business-centric focus.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timezone
from loguru import logger

from .llm_client import LLMClient
from .prompt_engine import PromptEngine
from .context_manager import ContextManager, ConversationContext
from .question_engine import QuestionEngine, DiscoveryAssessment


class TransformationPhase(str, Enum):
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment" 
    JUSTIFICATION = "justification"
    PLANNING = "planning"
    COMPLETED = "completed"


@dataclass
class BusinessCase:
    total_investment: float
    annual_benefits: float
    roi_percentage: float
    payback_period_months: float
    confidence_level: float
    recommendation: str  # "GO" | "NO-GO" | "CONDITIONAL"
    cost_breakdown: List[Dict[str, Any]]
    benefits_breakdown: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    assumptions: List[str]
    next_steps: List[str]


@dataclass
class TransformationResult:
    session_id: str
    domain_type: str
    current_phase: TransformationPhase
    discovery_summary: Optional[Dict[str, Any]] = None
    technical_assessment: Optional[Dict[str, Any]] = None
    business_case: Optional[BusinessCase] = None
    implementation_plan: Optional[Dict[str, Any]] = None
    completion_percentage: float = 0.0


class UniversalTransformationEngine:
    """Core orchestrator for transformation analysis workflow."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_engine: PromptEngine,
        context_manager: ContextManager,
        question_engine: QuestionEngine
    ):
        self.llm_client = llm_client
        self.prompt_engine = prompt_engine
        self.context_manager = context_manager
        self.question_engine = question_engine
        
        # Will be injected by domain registry
        self.domain_registry = None
        
        logger.info("UniversalTransformationEngine initialized")
    
    def set_domain_registry(self, registry):
        """Set the domain registry for transformation type resolution."""
        self.domain_registry = registry
        logger.info("Domain registry connected to transformation engine")
    
    async def start_transformation_analysis(
        self,
        user_request: str,
        user_id: Optional[str] = None
    ) -> str:
        """Start a new transformation analysis session."""
        
        # Auto-detect transformation domain from user request
        if not self.domain_registry:
            raise ValueError("Domain registry not configured")
        
        domain = await self._detect_transformation_domain(user_request)
        
        # Create new conversation session
        session_id = self.context_manager.create_session(
            initial_message=user_request,
            user_id=user_id,
            domain_type=domain.get_domain_name()
        )
        
        logger.info(f"Started transformation analysis: {session_id} ({domain.get_domain_name()})")
        return session_id
    
    async def process_user_input(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Process user input and advance the conversation/workflow."""
        
        context = self.context_manager.get_context(session_id)
        if not context:
            raise ValueError(f"Session not found: {session_id}")
        
        domain = self.domain_registry.get_domain(context.domain_type)
        if not domain:
            raise ValueError(f"Domain not found: {context.domain_type}")
        
        # Add user message to conversation history
        self.context_manager.add_message(session_id, "user", user_message)
        
        # Process based on current phase
        if context.current_phase == TransformationPhase.DISCOVERY:
            return await self._handle_discovery_phase(session_id, user_message, domain, context)
        elif context.current_phase == TransformationPhase.ASSESSMENT:
            return await self._handle_assessment_phase(session_id, user_message, domain, context)
        elif context.current_phase == TransformationPhase.JUSTIFICATION:
            return await self._handle_justification_phase(session_id, user_message, domain, context)
        elif context.current_phase == TransformationPhase.PLANNING:
            return await self._handle_planning_phase(session_id, user_message, domain, context)
        else:
            return {"error": f"Invalid phase: {context.current_phase}"}
    
    async def get_transformation_status(self, session_id: str) -> TransformationResult:
        """Get the current status and results of a transformation analysis."""
        
        context = self.context_manager.get_context(session_id)
        if not context:
            raise ValueError(f"Session not found: {session_id}")
        
        # Calculate completion percentage based on phase and discovered facts
        completion = self._calculate_completion_percentage(context)
        
        result = TransformationResult(
            session_id=session_id,
            domain_type=context.domain_type or "unknown",
            current_phase=TransformationPhase(context.current_phase),
            completion_percentage=completion
        )
        
        # Add phase-specific data if available
        if context.current_phase in [TransformationPhase.ASSESSMENT, TransformationPhase.JUSTIFICATION, TransformationPhase.PLANNING]:
            result.discovery_summary = context.discovered_facts
        
        if context.current_phase in [TransformationPhase.JUSTIFICATION, TransformationPhase.PLANNING]:
            # Generate business case if we have enough information
            if context.business_metrics:
                result.business_case = await self._generate_business_case(session_id, context)
        
        return result
    
    async def force_phase_transition(self, session_id: str, target_phase: TransformationPhase) -> bool:
        """Force transition to a specific phase (for testing/admin)."""
        try:
            success = self.context_manager.update_context(
                session_id, 
                current_phase=target_phase.value
            )
            if success:
                logger.info(f"Force transitioned session {session_id} to {target_phase}")
            return success
        except Exception as e:
            logger.error(f"Error forcing phase transition: {e}")
            return False
    
    async def detect_transformation_domain(self, user_request: str):
        """Public method to detect transformation domain from user request."""
        return await self._detect_transformation_domain(user_request)
    
    async def _detect_transformation_domain(self, user_request: str):
        """Auto-detect the transformation domain from user request."""
        # This will use the domain registry's auto-detection logic
        return await self.domain_registry.auto_detect_domain(user_request)
    
    async def _handle_discovery_phase(
        self, 
        session_id: str,
        user_message: str, 
        domain,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle discovery phase interaction."""
        
        # Extract business insights from user message
        insights = await self._extract_business_insights(user_message, domain, context)
        
        # Update discovered facts
        self.context_manager.update_context(session_id, discovered_facts=insights)
        
        # Assess discovery completeness
        domain_context = domain.get_question_context({"session_context": context})
        assessment = self.question_engine.assess_discovery_completeness(context, domain_context)
        
        if assessment.ready_for_next_phase:
            # Transition to assessment phase
            return await self._transition_to_assessment(session_id, domain, context)
        else:
            # Generate next discovery questions
            question_set = await self.question_engine.generate_discovery_questions(
                domain_context, context, max_questions=2
            )
            
            # Generate conversational response with questions
            agent_response = await self._generate_discovery_response(
                user_message, question_set, domain, context, assessment
            )
            
            # Add agent response to conversation
            self.context_manager.add_message(session_id, "assistant", agent_response)
            
            return {
                "phase": "discovery",
                "response": agent_response,
                "questions": [q.content for q in question_set.questions],
                "progress": assessment.completeness_percentage,
                "next_area": question_set.next_priority_area
            }
    
    async def _handle_assessment_phase(
        self,
        session_id: str, 
        user_message: str,
        domain,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle assessment phase interaction."""
        
        # Run technical assessment using domain-specific logic
        assessment_results = await domain.assess_transformation_complexity(
            context.discovered_facts
        )
        
        # Store assessment results
        self.context_manager.update_context(
            session_id,
            business_metrics={"assessment": assessment_results}
        )
        
        # Generate assessment summary response
        response = await self._generate_assessment_response(assessment_results, domain, context)
        
        self.context_manager.add_message(session_id, "assistant", response)
        
        # Automatically transition to justification
        self.context_manager.update_context(session_id, current_phase="justification")
        
        return {
            "phase": "justification", 
            "response": response,
            "assessment": assessment_results,
            "progress": 60.0
        }
    
    async def _handle_justification_phase(
        self,
        session_id: str,
        user_message: str,
        domain, 
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle justification phase interaction."""
        
        # Generate comprehensive business case
        business_case = await self._generate_business_case(session_id, context)
        
        # Generate business case presentation
        response = await self._generate_business_case_response(business_case, domain, context)
        
        self.context_manager.add_message(session_id, "assistant", response)
        
        # Transition to planning if user approves
        if "yes" in user_message.lower() or "approve" in user_message.lower() or "proceed" in user_message.lower():
            self.context_manager.update_context(session_id, current_phase="planning")
            
            return {
                "phase": "planning",
                "response": response + "\n\nGreat! Let's move on to planning the implementation strategy.",
                "business_case": business_case,
                "progress": 80.0
            }
        
        return {
            "phase": "justification",
            "response": response,
            "business_case": business_case,
            "progress": 70.0
        }
    
    async def _handle_planning_phase(
        self,
        session_id: str,
        user_message: str,
        domain,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Handle planning phase interaction."""
        
        # Generate implementation plan using domain-specific logic
        implementation_plan = await domain.generate_implementation_strategies(
            context.discovered_facts
        )
        
        # Generate planning response
        response = await self._generate_planning_response(implementation_plan, domain, context)
        
        self.context_manager.add_message(session_id, "assistant", response)
        
        # Mark as completed
        self.context_manager.update_context(session_id, current_phase="completed")
        
        return {
            "phase": "completed",
            "response": response,
            "implementation_plan": implementation_plan,
            "progress": 100.0
        }
    
    async def _extract_business_insights(
        self,
        user_message: str,
        domain,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Extract business insights from user message using AI."""
        
        extraction_prompt = self.prompt_engine.render_template(
            "analysis/extract_business_insights.jinja2",
            user_message=user_message,
            domain_type=domain.get_domain_name(),
            conversation_history=context.conversation_history[-5:],
            current_facts=context.discovered_facts
        )
        
        try:
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": extraction_prompt}
            ])
            
            # Parse insights from LLM response
            # This would include more sophisticated parsing in a real implementation
            insights = {}
            if "team size" in user_message.lower():
                # Extract team size
                import re
                match = re.search(r'(\d+)\s*(?:developers?|people|team)', user_message.lower())
                if match:
                    insights["team_size"] = int(match.group(1))
            
            # Add more parsing logic based on domain and message content
            insights["last_user_message"] = user_message
            insights["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return insights
            
        except Exception as e:
            logger.warning(f"LLM business insights extraction failed, using fallback: {e}")
            # Fallback to simple pattern-based extraction for demo mode
            insights = {}
            
            # Extract some basic information using simple patterns
            import re
            if "team size" in user_message.lower() or "developers" in user_message.lower():
                match = re.search(r'(\d+)\s*(?:developers?|people|team)', user_message.lower())
                if match:
                    insights["team_size"] = int(match.group(1))
            
            if "react" in user_message.lower():
                insights["current_technology"] = "React"
            if "vue" in user_message.lower():
                insights["target_technology"] = "Vue.js"
            if "difficult" in user_message.lower() or "maintain" in user_message.lower():
                insights["pain_points"] = ["maintenance_issues"]
            
            insights["raw_message"] = user_message
            insights["extraction_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return insights
    
    async def _generate_business_case(self, session_id: str, context: ConversationContext) -> BusinessCase:
        """Generate comprehensive business case using domain-specific ROI calculations."""
        
        domain = self.domain_registry.get_domain(context.domain_type)
        
        # Use domain-specific ROI calculator
        benefits = await domain.calculate_transformation_benefits(
            context.discovered_facts,
            {"target_state": "improved"}  # This would be more specific in real implementation
        )
        
        # For now, return a simplified business case
        # In real implementation, this would use sophisticated financial modeling
        return BusinessCase(
            total_investment=150000.0,
            annual_benefits=300000.0,
            roi_percentage=100.0,
            payback_period_months=6.0,
            confidence_level=0.75,
            recommendation="GO",
            cost_breakdown=[
                {"category": "Development", "amount": 120000, "timeline": "3 months"},
                {"category": "Training", "amount": 20000, "timeline": "1 month"}, 
                {"category": "Infrastructure", "amount": 10000, "timeline": "Ongoing"}
            ],
            benefits_breakdown=[
                {"category": "Developer Productivity", "annual_value": 180000, "confidence": 0.8},
                {"category": "Maintenance Savings", "annual_value": 80000, "confidence": 0.9},
                {"category": "Performance Gains", "annual_value": 40000, "confidence": 0.6}
            ],
            risks=[
                {
                    "category": "Implementation Risk",
                    "probability": 0.3,
                    "impact": 50000,
                    "mitigation": "Phased rollout approach"
                }
            ],
            assumptions=[
                "Current team productivity baseline maintained",
                "No major technical blockers encountered",
                "Stakeholder buy-in achieved"
            ],
            next_steps=[
                "Stakeholder approval",
                "Detailed implementation planning",
                "Resource allocation"
            ]
        )
    
    def _calculate_completion_percentage(self, context: ConversationContext) -> float:
        """Calculate completion percentage based on phase and progress."""
        phase_base_percentages = {
            "discovery": 0.0,
            "assessment": 30.0,
            "justification": 60.0,
            "planning": 80.0,
            "completed": 100.0
        }
        
        base = phase_base_percentages.get(context.current_phase, 0.0)
        
        # Add progress within current phase based on discovered facts
        if context.current_phase == "discovery":
            facts_count = len(context.discovered_facts)
            phase_progress = min(25.0, facts_count * 3)  # Up to 25% for discovery
            return base + phase_progress
        
        return base
    
    # Placeholder methods for response generation (to be implemented)
    async def _generate_discovery_response(self, user_message, question_set, domain, context, assessment):
        return f"Thanks for that information! I have {len(question_set.questions)} more questions to complete our analysis."
    
    async def _generate_assessment_response(self, assessment_results, domain, context):
        return "Based on my analysis, I've completed the technical assessment. Let me show you the business case."
    
    async def _generate_business_case_response(self, business_case, domain, context):
        return f"Here's your business case: ROI of {business_case.roi_percentage}% with {business_case.payback_period_months} month payback. Recommendation: {business_case.recommendation}"
    
    async def _generate_planning_response(self, implementation_plan, domain, context):
        return "Here's your implementation roadmap with recommended next steps."
    
    async def _transition_to_assessment(self, session_id, domain, context):
        self.context_manager.update_context(session_id, current_phase="assessment")
        return {
            "phase": "assessment",
            "response": "Great! I have enough information to start the technical assessment.",
            "progress": 30.0
        }