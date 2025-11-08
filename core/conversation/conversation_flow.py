"""
Conversation flow management for guiding users through transformation processes.

This module handles the structured conversation flow that guides users through
the discovery, assessment, justification, and planning phases of transformation.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json
from datetime import datetime

from loguru import logger


class ConversationPhase(Enum):
    """Phases of the transformation conversation."""
    INITIAL = "initial"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    JUSTIFICATION = "justification"
    PLANNING = "planning"
    COMPLETE = "complete"


class QuestionType(Enum):
    """Types of questions in the conversation."""
    OPEN_ENDED = "open_ended"
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    SCALE = "scale"  # 1-10 rating


@dataclass
class ConversationQuestion:
    """A question in the conversation flow."""
    id: str
    phase: ConversationPhase
    question_text: str
    question_type: QuestionType
    required: bool = True
    options: Optional[List[str]] = None  # For multiple choice
    min_value: Optional[int] = None      # For numeric/scale
    max_value: Optional[int] = None      # For numeric/scale
    follow_up_questions: List[str] = field(default_factory=list)
    business_context: Optional[str] = None
    
    
@dataclass
class ConversationAnswer:
    """An answer to a conversation question."""
    question_id: str
    answer: Any
    timestamp: datetime
    confidence: float = 1.0
    source: str = "user"  # user, inferred, default
    

@dataclass
class ConversationState:
    """Current state of the conversation."""
    session_id: str
    current_phase: ConversationPhase
    domain: Optional[str] = None
    answers: Dict[str, ConversationAnswer] = field(default_factory=dict)
    completed_phases: List[ConversationPhase] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ConversationFlow:
    """Manages the conversation flow for transformation processes."""
    
    def __init__(self):
        """Initialize the conversation flow."""
        self.questions = self._initialize_questions()
        self.phase_requirements = self._initialize_phase_requirements()
        
    def _initialize_questions(self) -> Dict[str, ConversationQuestion]:
        """Initialize the question database."""
        
        questions = {}
        
        # Discovery Phase Questions
        discovery_questions = [
            ConversationQuestion(
                id="business_challenge",
                phase=ConversationPhase.DISCOVERY,
                question_text="What specific business challenges are you trying to solve with this transformation?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Understanding the business driver helps prioritize solutions and measure success."
            ),
            ConversationQuestion(
                id="current_system_overview",
                phase=ConversationPhase.DISCOVERY,
                question_text="Can you describe your current system? What technologies, frameworks, and architecture are you using?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Technical baseline assessment for scope and complexity estimation."
            ),
            ConversationQuestion(
                id="team_size",
                phase=ConversationPhase.DISCOVERY,
                question_text="How many developers are on your team?",
                question_type=QuestionType.NUMERIC,
                min_value=1,
                max_value=1000,
                business_context="Team size affects timeline, coordination complexity, and training requirements."
            ),
            ConversationQuestion(
                id="timeline_constraints",
                phase=ConversationPhase.DISCOVERY,
                question_text="Do you have any timeline constraints or deadlines for this transformation?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Timeline constraints affect scope, risk, and resource allocation decisions."
            ),
            ConversationQuestion(
                id="budget_range",
                phase=ConversationPhase.DISCOVERY,
                question_text="What's your approximate budget range for this transformation?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Under $50K", "$50K - $200K", "$200K - $500K", "$500K - $1M", "Over $1M", "Not sure yet"],
                business_context="Budget constraints help scope the transformation and ROI calculations."
            ),
            ConversationQuestion(
                id="success_metrics",
                phase=ConversationPhase.DISCOVERY,
                question_text="How will you measure success for this transformation? What metrics matter most to your business?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Success metrics drive ROI calculations and implementation priorities."
            ),
            ConversationQuestion(
                id="pain_points",
                phase=ConversationPhase.DISCOVERY,
                question_text="What are the biggest pain points with your current system?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Pain points help quantify the cost of inaction and transformation benefits."
            )
        ]
        
        # Assessment Phase Questions
        assessment_questions = [
            ConversationQuestion(
                id="system_complexity",
                phase=ConversationPhase.ASSESSMENT,
                question_text="On a scale of 1-10, how would you rate the complexity of your current system?",
                question_type=QuestionType.SCALE,
                min_value=1,
                max_value=10,
                business_context="Complexity affects transformation timeline, risk, and required expertise."
            ),
            ConversationQuestion(
                id="technical_debt",
                phase=ConversationPhase.ASSESSMENT,
                question_text="How much technical debt does your current system have?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Minimal", "Moderate", "Significant", "Overwhelming", "Not sure"],
                business_context="Technical debt affects transformation complexity and long-term maintenance costs."
            ),
            ConversationQuestion(
                id="performance_issues",
                phase=ConversationPhase.ASSESSMENT,
                question_text="Are you experiencing performance issues with your current system?",
                question_type=QuestionType.BOOLEAN,
                follow_up_questions=["performance_impact"],
                business_context="Performance issues can justify transformation through productivity and user experience gains."
            ),
            ConversationQuestion(
                id="performance_impact",
                phase=ConversationPhase.ASSESSMENT,
                question_text="How do these performance issues impact your business? (e.g., lost sales, developer productivity)",
                question_type=QuestionType.OPEN_ENDED,
                required=False,
                business_context="Performance impact quantification for ROI calculations."
            ),
            ConversationQuestion(
                id="maintenance_effort",
                phase=ConversationPhase.ASSESSMENT,
                question_text="What percentage of your development time is spent on maintenance vs. new features?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"],
                business_context="Maintenance burden affects opportunity cost and productivity calculations."
            ),
            ConversationQuestion(
                id="skill_gaps",
                phase=ConversationPhase.ASSESSMENT,
                question_text="Does your team have experience with the target technologies, or will training be needed?",
                question_type=QuestionType.OPEN_ENDED,
                business_context="Skill gaps affect training costs, timeline, and implementation risks."
            )
        ]
        
        # Justification Phase Questions
        justification_questions = [
            ConversationQuestion(
                id="annual_revenue",
                phase=ConversationPhase.JUSTIFICATION,
                question_text="What's your approximate annual revenue? (This helps calculate business impact)",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Under $1M", "$1M - $10M", "$10M - $50M", "$50M - $200M", "Over $200M", "Prefer not to say"],
                business_context="Revenue scale affects the business impact and ROI of productivity improvements."
            ),
            ConversationQuestion(
                id="developer_costs",
                phase=ConversationPhase.JUSTIFICATION,
                question_text="What's the approximate average salary/cost per developer on your team?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["$50K - $80K", "$80K - $120K", "$120K - $160K", "$160K - $200K", "Over $200K"],
                business_context="Developer costs are used to calculate productivity savings and training costs."
            ),
            ConversationQuestion(
                id="risk_tolerance",
                phase=ConversationPhase.JUSTIFICATION,
                question_text="What's your organization's risk tolerance for this transformation?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Very Conservative", "Somewhat Conservative", "Moderate", "Somewhat Aggressive", "Very Aggressive"],
                business_context="Risk tolerance affects approach selection and confidence intervals."
            ),
            ConversationQuestion(
                id="strategic_importance",
                phase=ConversationPhase.JUSTIFICATION,
                question_text="How strategically important is this transformation to your business goals?",
                question_type=QuestionType.SCALE,
                min_value=1,
                max_value=10,
                business_context="Strategic importance affects investment justification and priority."
            )
        ]
        
        # Planning Phase Questions
        planning_questions = [
            ConversationQuestion(
                id="preferred_approach",
                phase=ConversationPhase.PLANNING,
                question_text="Do you prefer a phased migration approach or a complete rewrite?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Phased Migration", "Complete Rewrite", "Hybrid Approach", "Not Sure - Recommend Best Option"],
                business_context="Approach selection affects risk, timeline, and resource requirements."
            ),
            ConversationQuestion(
                id="downtime_tolerance",
                phase=ConversationPhase.PLANNING,
                question_text="How much downtime can your business tolerate during the transformation?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["No downtime acceptable", "Minimal (< 1 hour)", "Limited (few hours)", "Moderate (< 1 day)", "Flexible"],
                business_context="Downtime tolerance affects migration strategy and infrastructure requirements."
            ),
            ConversationQuestion(
                id="resource_allocation",
                phase=ConversationPhase.PLANNING,
                question_text="What percentage of your team can be dedicated to this transformation?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["25% or less", "25-50%", "50-75%", "75-100%", "Need to hire additional resources"],
                business_context="Resource allocation affects timeline and parallel development capacity."
            )
        ]
        
        # Add all questions to the dictionary
        all_questions = discovery_questions + assessment_questions + justification_questions + planning_questions
        for question in all_questions:
            questions[question.id] = question
            
        return questions
    
    def _initialize_phase_requirements(self) -> Dict[ConversationPhase, List[str]]:
        """Initialize the requirements for each phase."""
        
        return {
            ConversationPhase.DISCOVERY: [
                "business_challenge",
                "current_system_overview",
                "team_size",
                "success_metrics"
            ],
            ConversationPhase.ASSESSMENT: [
                "system_complexity",
                "technical_debt",
                "maintenance_effort"
            ],
            ConversationPhase.JUSTIFICATION: [
                "annual_revenue",
                "developer_costs",
                "risk_tolerance"
            ],
            ConversationPhase.PLANNING: [
                "preferred_approach",
                "downtime_tolerance"
            ]
        }
    
    def get_next_question(self, state: ConversationState) -> Optional[ConversationQuestion]:
        """
        Get the next question based on conversation state.
        
        Args:
            state: Current conversation state
            
        Returns:
            Next question to ask, or None if phase is complete
        """
        
        # Get required questions for current phase
        required_questions = self.phase_requirements.get(state.current_phase, [])
        
        # Find unanswered required questions
        for question_id in required_questions:
            if question_id not in state.answers:
                return self.questions[question_id]
        
        # Check for follow-up questions
        for answer in state.answers.values():
            question = self.questions[answer.question_id]
            
            # If this was a boolean question answered as True, ask follow-ups
            if (question.question_type == QuestionType.BOOLEAN and 
                answer.answer is True and 
                question.follow_up_questions):
                
                for follow_up_id in question.follow_up_questions:
                    if follow_up_id not in state.answers:
                        return self.questions[follow_up_id]
        
        # All required questions answered for this phase
        return None
    
    def can_advance_phase(self, state: ConversationState) -> bool:
        """
        Check if we can advance to the next phase.
        
        Args:
            state: Current conversation state
            
        Returns:
            True if all required questions are answered
        """
        
        required_questions = self.phase_requirements.get(state.current_phase, [])
        
        for question_id in required_questions:
            if question_id not in state.answers:
                return False
        
        return True
    
    def advance_phase(self, state: ConversationState) -> ConversationPhase:
        """
        Advance to the next phase.
        
        Args:
            state: Current conversation state
            
        Returns:
            New phase
        """
        
        if not self.can_advance_phase(state):
            raise ValueError(f"Cannot advance phase - missing required answers for {state.current_phase}")
        
        # Mark current phase as completed
        if state.current_phase not in state.completed_phases:
            state.completed_phases.append(state.current_phase)
        
        # Determine next phase
        phase_order = [
            ConversationPhase.INITIAL,
            ConversationPhase.DISCOVERY,
            ConversationPhase.ASSESSMENT,
            ConversationPhase.JUSTIFICATION,
            ConversationPhase.PLANNING,
            ConversationPhase.COMPLETE
        ]
        
        current_index = phase_order.index(state.current_phase)
        if current_index < len(phase_order) - 1:
            state.current_phase = phase_order[current_index + 1]
        else:
            state.current_phase = ConversationPhase.COMPLETE
        
        state.updated_at = datetime.now()
        
        logger.info(f"Advanced to phase: {state.current_phase}")
        
        return state.current_phase
    
    def record_answer(self, state: ConversationState, question_id: str, answer: Any, confidence: float = 1.0) -> None:
        """
        Record an answer to a question.
        
        Args:
            state: Current conversation state
            question_id: ID of the question being answered
            answer: The answer value
            confidence: Confidence level of the answer (0.0-1.0)
        """
        
        if question_id not in self.questions:
            raise ValueError(f"Unknown question ID: {question_id}")
        
        conversation_answer = ConversationAnswer(
            question_id=question_id,
            answer=answer,
            timestamp=datetime.now(),
            confidence=confidence,
            source="user"
        )
        
        state.answers[question_id] = conversation_answer
        state.updated_at = datetime.now()
        
        logger.info(f"Recorded answer for {question_id}: {answer}")
    
    def get_phase_summary(self, state: ConversationState, phase: ConversationPhase) -> Dict[str, Any]:
        """
        Get a summary of answers for a specific phase.
        
        Args:
            state: Current conversation state
            phase: Phase to summarize
            
        Returns:
            Summary of phase answers
        """
        
        phase_questions = [q for q in self.questions.values() if q.phase == phase]
        summary = {
            "phase": phase.value,
            "completed": phase in state.completed_phases,
            "answers": {},
            "business_context": {}
        }
        
        for question in phase_questions:
            if question.id in state.answers:
                answer = state.answers[question.id]
                summary["answers"][question.id] = {
                    "question": question.question_text,
                    "answer": answer.answer,
                    "confidence": answer.confidence,
                    "timestamp": answer.timestamp.isoformat()
                }
                
                if question.business_context:
                    summary["business_context"][question.id] = question.business_context
        
        return summary
    
    def get_conversation_progress(self, state: ConversationState) -> Dict[str, Any]:
        """
        Get overall conversation progress.
        
        Args:
            state: Current conversation state
            
        Returns:
            Progress summary
        """
        
        total_required = sum(len(questions) for questions in self.phase_requirements.values())
        answered_required = 0
        
        for phase, required_questions in self.phase_requirements.items():
            for question_id in required_questions:
                if question_id in state.answers:
                    answered_required += 1
        
        progress_percentage = (answered_required / total_required) * 100 if total_required > 0 else 0
        
        return {
            "current_phase": state.current_phase.value,
            "completed_phases": [p.value for p in state.completed_phases],
            "progress_percentage": round(progress_percentage, 1),
            "total_questions_answered": len(state.answers),
            "required_questions_answered": answered_required,
            "total_required_questions": total_required,
            "can_advance": self.can_advance_phase(state) if state.current_phase != ConversationPhase.COMPLETE else False
        }
    
    def infer_missing_information(self, state: ConversationState) -> Dict[str, Any]:
        """
        Infer missing information based on provided answers.
        
        Args:
            state: Current conversation state
            
        Returns:
            Inferred information with confidence scores
        """
        
        inferred = {}
        
        # Infer team experience level from complexity and technical debt
        if "system_complexity" in state.answers and "technical_debt" in state.answers:
            complexity = state.answers["system_complexity"].answer
            debt = state.answers["technical_debt"].answer
            
            debt_scores = {"Minimal": 1, "Moderate": 2, "Significant": 3, "Overwhelming": 4}
            debt_score = debt_scores.get(debt, 2)
            
            # High complexity + high debt suggests experienced team dealing with legacy
            if complexity >= 7 and debt_score >= 3:
                inferred["team_experience_level"] = {
                    "value": "experienced_with_legacy",
                    "confidence": 0.7,
                    "reasoning": "High system complexity with significant technical debt suggests experienced team managing legacy systems"
                }
            elif complexity <= 4 and debt_score <= 2:
                inferred["team_experience_level"] = {
                    "value": "modern_practices",
                    "confidence": 0.6,
                    "reasoning": "Lower complexity with minimal technical debt suggests team follows modern practices"
                }
        
        # Infer transformation urgency from pain points and business challenges
        if "pain_points" in state.answers and "business_challenge" in state.answers:
            pain_text = str(state.answers["pain_points"].answer).lower()
            challenge_text = str(state.answers["business_challenge"].answer).lower()
            
            urgency_keywords = {
                "high": ["critical", "urgent", "blocking", "losing", "competitive", "asap"],
                "medium": ["important", "necessary", "should", "planning", "considering"],
                "low": ["eventually", "future", "nice to have", "when possible"]
            }
            
            combined_text = pain_text + " " + challenge_text
            
            for level, keywords in urgency_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    inferred["transformation_urgency"] = {
                        "value": level,
                        "confidence": 0.6,
                        "reasoning": f"Text analysis suggests {level} urgency based on language used"
                    }
                    break
        
        return inferred