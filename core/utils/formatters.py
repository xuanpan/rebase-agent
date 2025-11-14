"""Formatters for conversation data and prompts."""

from typing import Dict, Any, List
from ..models.discovery import CollectedBusinessData


class ConversationFormatter:
    """Utilities for formatting conversation and discovery data."""
    
    @staticmethod
    def format_conversation_history(history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt inclusion."""
        
        formatted = []
        for msg in history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_collected_data_summary(collected_data: CollectedBusinessData) -> str:
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
    
    @staticmethod
    def format_detailed_data_summary(collected_data: CollectedBusinessData) -> str:
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