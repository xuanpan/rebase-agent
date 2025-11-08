"""
Response generator for creating contextual AI responses in conversations.

This module generates intelligent responses based on conversation context,
user intent, and transformation domain knowledge.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from loguru import logger

from .message_processor import MessageIntent, ProcessedMessage
from .conversation_flow import ConversationState, ConversationPhase, ConversationQuestion


@dataclass
class GeneratedResponse:
    """A generated response with metadata."""
    content: str
    response_type: str  # question, answer, summary, business_case, etc.
    confidence: float
    follow_up_questions: List[str] = None
    business_insights: List[str] = None
    next_steps: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.follow_up_questions is None:
            self.follow_up_questions = []
        if self.business_insights is None:
            self.business_insights = []
        if self.next_steps is None:
            self.next_steps = []
        if self.metadata is None:
            self.metadata = {}


class ResponseGenerator:
    """Generates contextual responses for transformation conversations."""
    
    def __init__(self):
        """Initialize the response generator."""
        self.response_templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize response templates."""
        
        return {
            "greeting": """Hello! I'm here to help you plan and justify your transformation project. I specialize in analyzing legacy systems, calculating ROI, and creating business cases that get executive approval.

Let's start by understanding your specific situation. What kind of transformation are you considering? For example:
- Migrating between frameworks (React → Vue, Django → FastAPI)
- Converting languages (Python → Go, JavaScript → TypeScript)  
- Modernizing legacy systems
- Performance optimization
- Architecture redesign
- Dependency upgrades

What's driving your need for change?""",

            "domain_detection": """Based on what you've told me, this sounds like a **{domain}** project. I can help you with:

🎯 **Business Case Development**: Calculate ROI, costs, and timeline
📊 **Risk Assessment**: Identify and mitigate transformation risks
📈 **Success Metrics**: Define measurable outcomes
🗺️  **Implementation Planning**: Step-by-step roadmap

{domain_specific_info}

To create the most accurate business case, I'll need to understand your current situation better. Let me ask you a few key questions.""",

            "discovery_question": """{business_context}

**{question_text}**

{question_guidance}""",

            "assessment_insight": """Based on your answers, here are some key insights:

{insights}

{next_question}""",

            "roi_preview": """## Preliminary Business Impact Analysis

Based on the information you've provided, here's an initial assessment:

### 💰 **Potential Benefits**
{benefits}

### ⏱️ **Estimated Timeline**
{timeline}

### 🎯 **Success Probability**
{probability}

{continue_conversation}""",

            "business_case_summary": """# Transformation Business Case

## Executive Summary
{executive_summary}

## Business Justification
{justification}

## Implementation Plan
{implementation}

## Risk Assessment
{risks}

## ROI Analysis
{roi_analysis}

Would you like me to dive deeper into any of these sections or help you present this to stakeholders?""",

            "clarification_request": """I want to make sure I understand correctly. {clarification_point}

Could you clarify: {specific_question}

This will help me provide more accurate {accuracy_benefit}.""",

            "phase_transition": """Great! We've completed the **{completed_phase}** phase. 

## Summary of {completed_phase}:
{phase_summary}

Now let's move to **{next_phase}** where we'll focus on {next_phase_focus}.

{transition_question}""",

            "error_recovery": """I apologize, but I didn't quite understand that. Let me rephrase my question:

{rephrased_question}

{helpful_context}"""
        }
    
    def generate_initial_response(self, processed_message: ProcessedMessage) -> GeneratedResponse:
        """
        Generate an initial response to start the conversation.
        
        Args:
            processed_message: The processed user message
            
        Returns:
            Generated response
        """
        
        logger.info(f"Generating initial response for intent: {processed_message.intent}")
        
        if processed_message.intent == MessageIntent.GREETING:
            content = self.response_templates["greeting"]
            response_type = "greeting"
            confidence = 0.9
            
        elif processed_message.intent == MessageIntent.START_TRANSFORMATION:
            # Detect domain and provide domain-specific guidance
            if processed_message.domain_hints:
                primary_domain = processed_message.domain_hints[0]
                domain_info = self._get_domain_info(primary_domain)
                
                content = self.response_templates["domain_detection"].format(
                    domain=domain_info["display_name"],
                    domain_specific_info=domain_info["description"]
                )
                response_type = "domain_detection"
                confidence = 0.8
            else:
                # Generic transformation request
                content = """I can help you plan and justify your transformation project! To provide the most accurate business case and ROI analysis, I need to understand your specific situation better.

What type of system or technology are you looking to transform? The more details you can share, the more precise my analysis will be."""
                response_type = "clarification"
                confidence = 0.7
                
        else:
            # Default response for unclear intent
            content = """I'm here to help you plan and justify your transformation project with data-driven business cases and ROI analysis.

Could you tell me more about:
- What system or technology you want to transform
- What's driving this need for change
- Any specific goals or challenges you're trying to address

This will help me provide the most relevant guidance for your situation."""
            response_type = "clarification"
            confidence = 0.5
        
        # Generate follow-up questions based on extracted entities
        follow_ups = self._generate_follow_up_questions(processed_message)
        
        return GeneratedResponse(
            content=content,
            response_type=response_type,
            confidence=confidence,
            follow_up_questions=follow_ups,
            metadata={"intent": processed_message.intent.value, "domains": processed_message.domain_hints}
        )
    
    def generate_question_response(self, question: ConversationQuestion, state: ConversationState) -> GeneratedResponse:
        """
        Generate a response that asks a specific question.
        
        Args:
            question: The question to ask
            state: Current conversation state
            
        Returns:
            Generated response
        """
        
        logger.info(f"Generating question response for: {question.id}")
        
        # Add business context explanation
        business_context = ""
        if question.business_context:
            business_context = f"*{question.business_context}*\n\n"
        
        # Add question guidance based on type
        guidance = self._get_question_guidance(question)
        
        content = self.response_templates["discovery_question"].format(
            business_context=business_context,
            question_text=question.question_text,
            question_guidance=guidance
        )
        
        return GeneratedResponse(
            content=content,
            response_type="question",
            confidence=0.9,
            metadata={
                "question_id": question.id,
                "question_type": question.question_type.value,
                "phase": question.phase.value
            }
        )
    
    def generate_insight_response(self, state: ConversationState, new_insights: List[str]) -> GeneratedResponse:
        """
        Generate a response that provides insights based on answers.
        
        Args:
            state: Current conversation state
            new_insights: New insights to share
            
        Returns:
            Generated response
        """
        
        logger.info("Generating insight response")
        
        insights_text = "\n".join([f"• {insight}" for insight in new_insights])
        
        # Check if there are more questions in this phase
        from .conversation_flow import ConversationFlow
        flow = ConversationFlow()
        next_question = flow.get_next_question(state)
        
        if next_question:
            next_question_text = f"\nLet me ask you another important question:\n\n**{next_question.question_text}**"
        else:
            next_question_text = "\nI have all the information I need for this phase. Let me analyze what you've told me..."
        
        content = self.response_templates["assessment_insight"].format(
            insights=insights_text,
            next_question=next_question_text
        )
        
        return GeneratedResponse(
            content=content,
            response_type="insight",
            confidence=0.8,
            business_insights=new_insights
        )
    
    def generate_roi_preview(self, state: ConversationState, preliminary_analysis: Dict[str, Any]) -> GeneratedResponse:
        """
        Generate a preview of ROI analysis.
        
        Args:
            state: Current conversation state
            preliminary_analysis: Preliminary analysis results
            
        Returns:
            Generated response
        """
        
        logger.info("Generating ROI preview response")
        
        benefits = preliminary_analysis.get("benefits", [])
        timeline = preliminary_analysis.get("timeline", "To be determined")
        probability = preliminary_analysis.get("success_probability", "Moderate")
        
        benefits_text = "\n".join([f"• {benefit}" for benefit in benefits])
        
        continue_text = "Let me ask a few more questions to refine this analysis and create your complete business case."
        
        content = self.response_templates["roi_preview"].format(
            benefits=benefits_text,
            timeline=timeline,
            probability=probability,
            continue_conversation=continue_text
        )
        
        return GeneratedResponse(
            content=content,
            response_type="roi_preview",
            confidence=0.7,
            business_insights=benefits
        )
    
    def generate_phase_transition(self, completed_phase: ConversationPhase, next_phase: ConversationPhase, 
                                 phase_summary: Dict[str, Any]) -> GeneratedResponse:
        """
        Generate a response for transitioning between phases.
        
        Args:
            completed_phase: Phase that was just completed
            next_phase: Next phase to begin
            phase_summary: Summary of completed phase
            
        Returns:
            Generated response
        """
        
        logger.info(f"Generating phase transition from {completed_phase} to {next_phase}")
        
        phase_names = {
            ConversationPhase.DISCOVERY: "Discovery",
            ConversationPhase.ASSESSMENT: "Assessment", 
            ConversationPhase.JUSTIFICATION: "Justification",
            ConversationPhase.PLANNING: "Planning"
        }
        
        phase_focus = {
            ConversationPhase.ASSESSMENT: "evaluating technical complexity and risks",
            ConversationPhase.JUSTIFICATION: "calculating ROI and building the business case",
            ConversationPhase.PLANNING: "creating the implementation roadmap",
            ConversationPhase.COMPLETE: "finalizing your transformation plan"
        }
        
        # Create summary text
        summary_points = []
        for key, value in phase_summary.get("answers", {}).items():
            summary_points.append(f"• {value['question']}: {value['answer']}")
        
        summary_text = "\n".join(summary_points) if summary_points else "Key information collected and analyzed."
        
        # Next phase question
        transition_question = "Let's continue with the next set of questions."
        if next_phase == ConversationPhase.COMPLETE:
            transition_question = "I now have enough information to create your complete business case!"
        
        content = self.response_templates["phase_transition"].format(
            completed_phase=phase_names.get(completed_phase, completed_phase.value),
            phase_summary=summary_text,
            next_phase=phase_names.get(next_phase, next_phase.value),
            next_phase_focus=phase_focus.get(next_phase, "completing the analysis"),
            transition_question=transition_question
        )
        
        return GeneratedResponse(
            content=content,
            response_type="phase_transition",
            confidence=0.9,
            metadata={
                "completed_phase": completed_phase.value,
                "next_phase": next_phase.value
            }
        )
    
    def generate_business_case(self, state: ConversationState, analysis_results: Dict[str, Any]) -> GeneratedResponse:
        """
        Generate a complete business case response.
        
        Args:
            state: Current conversation state with all answers
            analysis_results: Complete analysis results
            
        Returns:
            Generated business case
        """
        
        logger.info("Generating complete business case")
        
        # Extract key components from analysis
        executive_summary = analysis_results.get("executive_summary", "Business case for transformation project.")
        justification = analysis_results.get("business_justification", "Transformation addresses key business needs.")
        implementation = analysis_results.get("implementation_plan", "Phased approach recommended.")
        risks = analysis_results.get("risk_assessment", "Risks identified and mitigation strategies provided.")
        roi_analysis = analysis_results.get("roi_analysis", "Positive ROI expected.")
        
        content = self.response_templates["business_case_summary"].format(
            executive_summary=executive_summary,
            justification=justification,
            implementation=implementation,
            risks=risks,
            roi_analysis=roi_analysis
        )
        
        next_steps = [
            "Review the business case with stakeholders",
            "Refine timeline and resource estimates",
            "Get executive approval for the project",
            "Begin planning the implementation phases"
        ]
        
        return GeneratedResponse(
            content=content,
            response_type="business_case",
            confidence=0.9,
            next_steps=next_steps,
            metadata={"analysis_results": analysis_results}
        )
    
    def generate_clarification_request(self, unclear_point: str, suggested_question: str) -> GeneratedResponse:
        """
        Generate a clarification request when something is unclear.
        
        Args:
            unclear_point: What needs clarification
            suggested_question: Specific question to ask
            
        Returns:
            Clarification request response
        """
        
        content = self.response_templates["clarification_request"].format(
            clarification_point=unclear_point,
            specific_question=suggested_question,
            accuracy_benefit="recommendations and ROI calculations"
        )
        
        return GeneratedResponse(
            content=content,
            response_type="clarification",
            confidence=0.8
        )
    
    def _get_domain_info(self, domain: str) -> Dict[str, str]:
        """Get display information for a domain."""
        
        domain_info = {
            "framework_migration": {
                "display_name": "Framework Migration",
                "description": """This involves migrating from one framework to another (e.g., React to Vue, Django to FastAPI). I'll help you:

• **Assess Migration Complexity**: Component count, custom integrations, team experience
• **Calculate Business Impact**: Developer productivity gains, maintenance cost reduction
• **Plan Migration Strategy**: Phased approach vs. complete rewrite
• **Risk Mitigation**: Compatibility issues, training needs, timeline risks"""
            },
            "language_conversion": {
                "display_name": "Language Conversion",
                "description": """Converting from one programming language to another. I'll analyze:

• **Code Compatibility**: Language feature mapping and conversion complexity
• **Performance Impact**: Runtime performance changes and optimization opportunities  
• **Team Readiness**: Skills gap analysis and training requirements
• **Business Justification**: Long-term maintainability and ecosystem benefits"""
            },
            "performance_optimization": {
                "display_name": "Performance Optimization",
                "description": """Improving system performance and scalability. I'll evaluate:

• **Current Bottlenecks**: Database, API, frontend performance issues
• **Optimization Opportunities**: Caching, database optimization, code improvements
• **Business Impact**: User experience improvements, operational cost savings
• **Implementation Strategy**: High-impact optimizations with minimal risk"""
            },
            "architecture_redesign": {
                "display_name": "Architecture Redesign",
                "description": """Restructuring system architecture (e.g., monolith to microservices). I'll help with:

• **Architecture Assessment**: Current limitations and scalability constraints
• **Target Architecture Design**: Microservices, serverless, cloud-native patterns
• **Migration Complexity**: Service boundaries, data migration, operational changes
• **Business Value**: Scalability, team productivity, operational efficiency"""
            },
            "dependency_upgrade": {
                "display_name": "Dependency Upgrade",
                "description": """Upgrading libraries, frameworks, or runtime versions. I'll analyze:

• **Security Impact**: Vulnerability fixes and compliance requirements
• **Breaking Changes**: Code modifications and compatibility issues
• **Performance Benefits**: Speed improvements and new features
• **Risk Assessment**: Regression risks and rollback strategies"""
            },
            "modernization": {
                "display_name": "Legacy System Modernization",
                "description": """Comprehensive modernization of legacy systems. I'll provide:

• **Legacy Assessment**: Technical debt analysis and modernization opportunities
• **Technology Strategy**: Modern stack recommendations and migration paths
• **Business Case**: Cost of inaction vs. modernization investment
• **Phased Approach**: Risk-managed modernization with measurable milestones"""
            }
        }
        
        return domain_info.get(domain, {
            "display_name": "System Transformation",
            "description": "I'll help you analyze and plan your transformation project with a focus on business value and ROI."
        })
    
    def _get_question_guidance(self, question: ConversationQuestion) -> str:
        """Get guidance text for different question types."""
        
        if question.question_type.value == "multiple_choice" and question.options:
            options_text = "\n".join([f"• {option}" for option in question.options])
            return f"Please choose from:\n{options_text}"
        
        elif question.question_type.value == "scale":
            return f"Please rate from {question.min_value} to {question.max_value} (where {question.min_value} is lowest and {question.max_value} is highest)."
        
        elif question.question_type.value == "boolean":
            return "Please answer yes or no."
        
        elif question.question_type.value == "numeric":
            if question.min_value and question.max_value:
                return f"Please provide a number between {question.min_value} and {question.max_value}."
            else:
                return "Please provide a number."
        
        else:  # open_ended
            return "Please provide as much detail as you're comfortable sharing."
    
    def _generate_follow_up_questions(self, processed_message: ProcessedMessage) -> List[str]:
        """Generate relevant follow-up questions based on the processed message."""
        
        follow_ups = []
        
        # Based on extracted entities
        if "frameworks" in processed_message.extracted_entities:
            follow_ups.append("What's your current framework and what do you want to migrate to?")
        
        if "legacy_system" in processed_message.extracted_entities:
            follow_ups.append("How old is your current system and what technologies does it use?")
        
        if "has_team_context" in processed_message.extracted_entities:
            follow_ups.append("What's your team size and their experience level?")
        
        # Based on domain hints
        if "performance_optimization" in processed_message.domain_hints:
            follow_ups.append("What specific performance issues are you experiencing?")
        
        if "architecture_redesign" in processed_message.domain_hints:
            follow_ups.append("What architectural limitations are you facing?")
        
        # Generic business questions if no specific context
        if not follow_ups:
            follow_ups.extend([
                "What's driving this transformation need?",
                "Do you have any timeline or budget constraints?",
                "How will you measure success?"
            ])
        
        return follow_ups[:3]  # Limit to 3 follow-ups