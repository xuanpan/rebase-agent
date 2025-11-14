"""Discovery-related prompts for business data collection and conversation flow."""

from typing import Dict, Any, List
from ..models.discovery import CollectedBusinessData
from ..utils.formatters import ConversationFormatter


class DiscoveryPrompts:
    """Centralized discovery prompt management."""
    
    @staticmethod
    def build_initial_response_prompt(initial_message: str) -> str:
        """Build prompt for generating contextual initial responses."""
        return f"""
You are a business transformation consultant. A user has just started a conversation with this message:

"{initial_message}"

Based on their message, provide a warm, professional initial response that:
1. Acknowledges their specific situation/needs mentioned
2. Shows you understand their transformation goal
3. Asks ONE strategic follow-up question to gather critical business context
4. Keeps the tone conversational and helpful

Be specific to their message, don't use generic responses. Focus on what they mentioned and ask about business impact, stakeholders, or current pain points.

Response should be 2-3 sentences maximum.
"""
    
    @staticmethod
    def build_discovery_decision_prompt(
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
{ConversationFormatter.format_conversation_history(conversation_history)}

CURRENT DISCOVERY STATE:
Completeness: {completeness:.1%}
Categories with data: {len([cat for cat in discovery_summary['categories'] if discovery_summary['categories'][cat]['progress'] > 0])}/5
Missing critical categories: {', '.join(missing_categories) if missing_categories else 'None'}

DATA COLLECTED SO FAR:
{ConversationFormatter.format_detailed_data_summary(collected_data)}

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
    
    @staticmethod
    def build_data_extraction_prompt(
        conversation_history: List[Dict[str, str]], 
        collected_data: CollectedBusinessData
    ) -> str:
        """Build prompt for LLM data extraction."""
        
        # Get the last few messages for context
        recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        
        # Build context of what we already know
        current_data_summary = ConversationFormatter.format_collected_data_summary(collected_data)
        
        return f"""
You are a business data extraction expert. Analyze the conversation and extract structured business information.

RECENT CONVERSATION:
{ConversationFormatter.format_conversation_history(recent_messages)}

ALREADY COLLECTED:
{current_data_summary}

EXTRACT DATA IN JSON FORMAT:
Based on the conversation, extract any new business information that matches our exact data model:

{{
  "business_goals": {{
    "primary_objectives": ["list of business goals/objectives mentioned"],
    "success_criteria": ["how success will be measured"],
    "kpis": ["key performance indicators mentioned"]
  }},
  "current_problems": {{
    "technical_issues": ["technical problems, legacy issues, technical debt"],
    "performance_issues": ["performance problems, slowness, bottlenecks"],
    "operational_issues": ["maintenance issues, support problems"],
    "security_risks": ["security vulnerabilities, compliance gaps"],
    "cost_drains": ["areas causing financial loss or inefficiency"]
  }},
  "key_metrics": {{
    "operational_costs": {{"maintenance": "cost if mentioned", "infrastructure": "cost if mentioned", "total_annual": "total costs if mentioned"}},
    "user_metrics": {{"total_users": "user count if mentioned", "satisfaction": "user satisfaction if mentioned"}},
    "performance_metrics": {{"response_time": "performance data if mentioned", "uptime": "reliability metrics if mentioned"}},
    "business_metrics": {{"revenue_impact": "business impact if mentioned"}}
  }},
  "stakeholders": {{
    "decision_makers": ["names and roles of decision makers like 'John Smith (CTO)', 'Jane Doe (Product Lead)']
    "technical_team": ["engineering team members mentioned"],
    "business_users": ["end users and business stakeholders"]
  }},
  "implementation_context": {{
    "current_technology": ["current tech stack like 'React 16', 'Node.js', etc"],
    "project_type": "type of transformation (e.g., 'Framework Migration', 'Modernization')",
    "technical_constraints": ["current system limitations"],
    "project_budget": {{"max_investment": "budget amount if mentioned", "funding_source": "budget source if mentioned"}},
    "timeline_requirements": {{"preferred_timeline": "timeline if mentioned", "hard_deadline": "deadline if mentioned"}}
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

    @staticmethod
    def build_completion_response_prompt(
        llm_decision: Dict[str, Any],
        collected_data: CollectedBusinessData,
        context
    ) -> str:
        """Build prompt for generating completion responses."""
        
        completeness = llm_decision.get("completeness_score", 0.0)
        
        # Get some basic stats from the hierarchical categories
        goals_count = len(collected_data.business_goals.future_state.get("primary_objectives", [])) if collected_data.business_goals else 0
        problems_count = len(collected_data.current_problems.current_state.get("technical_issues", [])) + len(collected_data.current_problems.current_state.get("security_risks", [])) if collected_data.current_problems else 0
        stakeholder_count = (
            len(collected_data.stakeholders.current_state.get("decision_makers", [])) +
            len(collected_data.stakeholders.current_state.get("technical_team", [])) +
            len(collected_data.stakeholders.current_state.get("business_users", []))
        ) if collected_data.stakeholders else 0
        
        return f"""
Perfect! I've gathered enough information to move forward. Based on our conversation, I can see we have {completeness:.0%} of the key information needed.

Here's what I've captured:
• Business Goals: {goals_count} objectives identified
• Current Problems: {problems_count} issues documented  
• Stakeholders: {stakeholder_count} stakeholders mapped
• Discovery Status: {len([cat for cat in ['business_goals', 'stakeholders', 'current_problems', 'key_metrics', 'implementation_context'] if getattr(collected_data, cat) and getattr(collected_data, cat).progress > 0])}/5 categories started

Let me now analyze your current system to provide accurate ROI calculations and recommendations. This will take a moment...
        """.strip()