"""
Question Engine - AI-powered dynamic question generation system.

Generates contextual business questions for discovery phase based on
domain context, conversation history, and missing information gaps.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .llm_client import LLMClient, LLMConfig, LLMProvider
from .prompt_engine import PromptEngine
from .context_manager import ContextManager, ConversationContext


class QuestionType(str, Enum):
    DISCOVERY = "discovery"
    CLARIFICATION = "clarification" 
    QUANTIFICATION = "quantification"
    VALIDATION = "validation"


@dataclass
class Question:
    id: str
    type: QuestionType
    content: str
    priority: int  # 1-5, higher is more important
    context_area: str  # What business area this question explores
    follow_up_potential: bool  # Whether this question likely needs follow-ups
    
    
@dataclass
class QuestionSet:
    questions: List[Question]
    conversation_phase: str
    completeness_score: float  # 0.0-1.0, how complete our discovery is
    next_priority_area: Optional[str]  # What to focus on next


@dataclass
class DiscoveryAssessment:
    discovered_areas: List[str]
    missing_areas: List[str]
    completeness_percentage: float
    ready_for_next_phase: bool
    confidence_level: float


class QuestionEngine:
    """AI-powered dynamic question generation system."""
    
    def __init__(self, llm_client: LLMClient, prompt_engine: PromptEngine):
        self.llm_client = llm_client
        self.prompt_engine = prompt_engine
        
        # Business areas we need to explore for transformation analysis
        self.required_business_areas = [
            "current_pain_points",
            "business_impact_quantification", 
            "team_and_stakeholder_context",
            "success_criteria_definition",
            "timeline_and_constraints",
            "competitive_and_strategic_drivers"
        ]
        
        logger.info("QuestionEngine initialized")
    
    async def generate_discovery_questions(
        self,
        domain_context: Dict[str, Any],
        conversation_context: ConversationContext,
        max_questions: int = 3
    ) -> QuestionSet:
        """Generate contextual discovery questions based on domain and conversation state."""
        
        # Assess what we already know
        assessment = self._assess_discovery_completeness(conversation_context, domain_context)
        
        # Determine what areas need more exploration
        priority_areas = self._prioritize_missing_areas(assessment.missing_areas, domain_context)
        
        # Generate questions for the most important missing areas
        questions = []
        
        for area in priority_areas[:max_questions]:
            question = await self._generate_area_specific_question(
                area, domain_context, conversation_context
            )
            if question:
                questions.append(question)
        
        return QuestionSet(
            questions=questions,
            conversation_phase=conversation_context.current_phase,
            completeness_score=assessment.completeness_percentage / 100,
            next_priority_area=priority_areas[0] if priority_areas else None
        )
    
    async def generate_followup_question(
        self,
        user_answer: str,
        previous_question: str,
        domain_context: Dict[str, Any],
        conversation_context: ConversationContext
    ) -> Optional[Question]:
        """Generate intelligent follow-up question based on user's answer."""
        
        # Analyze the user's answer for follow-up opportunities
        followup_prompt = self.prompt_engine.render_template(
            "question_generation/generate_followup.jinja2",
            user_answer=user_answer,
            previous_question=previous_question,
            domain_context=domain_context,
            conversation_summary=conversation_context.discovered_facts
        )
        
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=300
            )
            
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": followup_prompt}
            ], config)
            
            # Parse the response to extract the follow-up question
            followup_content = self._extract_question_from_response(response.content)
            
            if followup_content:
                return Question(
                    id=f"followup_{len(conversation_context.conversation_history)}",
                    type=QuestionType.CLARIFICATION,
                    content=followup_content,
                    priority=4,  # Follow-ups are usually high priority
                    context_area="clarification",
                    follow_up_potential=False  # Avoid infinite loops
                )
            
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
        
        return None
    
    def assess_discovery_completeness(
        self, 
        conversation_context: ConversationContext,
        domain_context: Dict[str, Any]
    ) -> DiscoveryAssessment:
        """Assess how complete our discovery is and if we're ready to proceed."""
        return self._assess_discovery_completeness(conversation_context, domain_context)
    
    async def generate_quantification_questions(
        self,
        business_area: str,
        current_facts: Dict[str, Any],
        domain_context: Dict[str, Any]
    ) -> List[Question]:
        """Generate specific questions to quantify business impact."""
        
        quantification_prompt = self.prompt_engine.render_template(
            "question_generation/quantification_questions.jinja2",
            business_area=business_area,
            current_facts=current_facts,
            domain_context=domain_context
        )
        
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4-turbo-preview",
                temperature=0.6,
                max_tokens=500
            )
            
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": quantification_prompt}
            ], config)
            
            questions = self._parse_multiple_questions(
                response.content, QuestionType.QUANTIFICATION, business_area
            )
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating quantification questions: {e}")
            return []
    
    def _assess_discovery_completeness(
        self, 
        conversation_context: ConversationContext,
        domain_context: Dict[str, Any]
    ) -> DiscoveryAssessment:
        """Internal method to assess discovery completeness."""
        
        discovered_facts = conversation_context.discovered_facts
        discovered_areas = []
        missing_areas = []
        
        # Check which business areas we have good coverage for
        for area in self.required_business_areas:
            if self._has_sufficient_coverage(area, discovered_facts, domain_context):
                discovered_areas.append(area)
            else:
                missing_areas.append(area)
        
        completeness_percentage = (len(discovered_areas) / len(self.required_business_areas)) * 100
        
        # We're ready for next phase if we have at least 70% completion
        # and covered the most critical areas
        critical_areas = ["current_pain_points", "business_impact_quantification"]
        has_critical_areas = all(area in discovered_areas for area in critical_areas)
        ready_for_next_phase = completeness_percentage >= 70 and has_critical_areas
        
        # Confidence based on how much quantitative data we have
        quantitative_facts = sum(
            1 for fact in discovered_facts.values() 
            if isinstance(fact, (int, float)) or any(char.isdigit() for char in str(fact))
        )
        confidence_level = min(0.9, quantitative_facts * 0.1 + completeness_percentage * 0.005)
        
        return DiscoveryAssessment(
            discovered_areas=discovered_areas,
            missing_areas=missing_areas,
            completeness_percentage=completeness_percentage,
            ready_for_next_phase=ready_for_next_phase,
            confidence_level=confidence_level
        )
    
    def _has_sufficient_coverage(
        self, 
        area: str, 
        discovered_facts: Dict[str, Any],
        domain_context: Dict[str, Any]
    ) -> bool:
        """Check if we have sufficient information about a business area."""
        
        # Define what constitutes sufficient coverage for each area
        area_requirements = {
            "current_pain_points": ["pain_description", "frequency", "impact"],
            "business_impact_quantification": ["cost_impact", "time_impact", "quality_impact"], 
            "team_and_stakeholder_context": ["team_size", "skill_level", "stakeholder_roles"],
            "success_criteria_definition": ["success_metrics", "measurement_method"],
            "timeline_and_constraints": ["timeline_preference", "budget_constraints"],
            "competitive_and_strategic_drivers": ["business_drivers", "competitive_pressure"]
        }
        
        required_keys = area_requirements.get(area, [])
        
        # Check if we have at least 60% of required information for this area
        covered_keys = sum(
            1 for key in required_keys 
            if any(key in fact_key.lower() for fact_key in discovered_facts.keys())
        )
        
        coverage_ratio = covered_keys / len(required_keys) if required_keys else 0
        return coverage_ratio >= 0.6
    
    def _prioritize_missing_areas(
        self, 
        missing_areas: List[str], 
        domain_context: Dict[str, Any]
    ) -> List[str]:
        """Prioritize which missing areas to ask about first."""
        
        # Base priority order (most important first)
        base_priorities = {
            "current_pain_points": 10,
            "business_impact_quantification": 9,
            "team_and_stakeholder_context": 7,
            "success_criteria_definition": 6,
            "competitive_and_strategic_drivers": 5,
            "timeline_and_constraints": 4
        }
        
        # Adjust priorities based on domain type
        domain_type = domain_context.get("domain_type", "")
        
        if "performance" in domain_type:
            base_priorities["business_impact_quantification"] += 2
        elif "security" in domain_type or "compliance" in domain_type:
            base_priorities["competitive_and_strategic_drivers"] += 2
        elif "framework" in domain_type or "language" in domain_type:
            base_priorities["team_and_stakeholder_context"] += 2
        
        # Sort missing areas by priority
        prioritized_areas = sorted(
            missing_areas,
            key=lambda area: base_priorities.get(area, 0),
            reverse=True
        )
        
        return prioritized_areas
    
    async def _generate_area_specific_question(
        self,
        area: str,
        domain_context: Dict[str, Any], 
        conversation_context: ConversationContext
    ) -> Optional[Question]:
        """Generate a question specific to a business area."""
        
        question_prompt = self.prompt_engine.render_template(
            "question_generation/area_specific_question.jinja2",
            business_area=area,
            domain_context=domain_context,
            conversation_history=conversation_context.conversation_history[-5:],  # Recent context
            discovered_facts=conversation_context.discovered_facts
        )
        
        try:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4-turbo-preview",
                temperature=0.7,
                max_tokens=200
            )
            
            response = await self.llm_client.chat_completion([
                {"role": "user", "content": question_prompt}
            ], config)
            
            question_content = self._extract_question_from_response(response.content)
            
            if question_content:
                return Question(
                    id=f"{area}_{len(conversation_context.conversation_history)}",
                    type=QuestionType.DISCOVERY,
                    content=question_content,
                    priority=self._calculate_question_priority(area),
                    context_area=area,
                    follow_up_potential=True
                )
                
        except Exception as e:
            logger.warning(f"LLM question generation failed for {area}, using template fallback: {e}")
            # Fallback to template-based questions for demo mode
            fallback_questions = {
                "team": "Tell me about your development team - how many people are working on this project?",
                "technology": "What specific technical challenges are you facing with your current setup?",
                "business": "What business outcomes are you hoping to achieve with this transformation?", 
                "timeline": "What's your target timeline for completing this transformation?",
                "budget": "Do you have a rough budget range in mind for this project?",
                "pain_points": "What are the main pain points you're experiencing right now?"
            }
            
            question_content = fallback_questions.get(area, f"Can you tell me more about your {area} requirements?")
            
            return Question(
                id=f"{area}_{len(conversation_context.conversation_history)}",
                type=QuestionType.DISCOVERY,
                content=question_content,
                priority=self._calculate_question_priority(area),
                context_area=area,
                follow_up_potential=True
            )
        
        return None
    
    def _extract_question_from_response(self, response_content: str) -> Optional[str]:
        """Extract a clean question from LLM response."""
        # Remove any markdown, numbering, or extra formatting
        lines = response_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, headers, numbering
            if not line or line.startswith('#') or line.startswith('**'):
                continue
            # Remove common prefixes
            line = line.lstrip('1234567890.-• ')
            if line.endswith('?'):
                return line
        
        # Fallback: return first non-empty line if it looks like a question
        for line in lines:
            line = line.strip().lstrip('1234567890.-• ')
            if line and len(line) > 10:  # Reasonable question length
                return line
        
        return None
    
    def _parse_multiple_questions(
        self, 
        response_content: str, 
        question_type: QuestionType,
        context_area: str
    ) -> List[Question]:
        """Parse multiple questions from LLM response."""
        questions = []
        lines = response_content.strip().split('\n')
        
        for i, line in enumerate(lines):
            question_content = self._extract_question_from_response(line)
            if question_content:
                questions.append(Question(
                    id=f"{context_area}_{question_type}_{i}",
                    type=question_type,
                    content=question_content,
                    priority=self._calculate_question_priority(context_area),
                    context_area=context_area,
                    follow_up_potential=question_type == QuestionType.DISCOVERY
                ))
        
        return questions
    
    def _calculate_question_priority(self, area: str) -> int:
        """Calculate question priority based on business area."""
        priority_map = {
            "current_pain_points": 5,
            "business_impact_quantification": 5,
            "team_and_stakeholder_context": 4,
            "success_criteria_definition": 3,
            "competitive_and_strategic_drivers": 3,
            "timeline_and_constraints": 2,
            "clarification": 4
        }
        return priority_map.get(area, 3)