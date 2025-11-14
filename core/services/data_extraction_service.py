"""Data extraction service for processing conversations and extracting business data."""

import json
import re
from typing import Dict, Any, List

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..models.discovery import CollectedBusinessData
from ..prompts.discovery_prompts import DiscoveryPrompts


class DataExtractionService:
    """Service for extracting business data from conversations using LLM intelligence."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def extract_data_from_conversation(
        self, 
        conversation_history: List[Dict[str, str]], 
        collected_data: CollectedBusinessData
    ) -> Dict[str, Any]:
        """Extract business data from conversation using LLM intelligence."""
        if not conversation_history:
            return {}
        
        extraction_prompt = DiscoveryPrompts.build_data_extraction_prompt(
            conversation_history, collected_data
        )

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
            
            # Remove markdown code block markers if present
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            # Try to parse as JSON
            try:
                extracted_data = json.loads(content)
                logger.info(f"Successfully extracted LLM data: {extracted_data}")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed. Content: '{content}'. Error: {e}")
                # Try to clean up common JSON issues
                try:
                    # Remove any trailing commas
                    import re
                    cleaned_content = re.sub(r',\s*}', '}', content)
                    cleaned_content = re.sub(r',\s*]', ']', cleaned_content)
                    extracted_data = json.loads(cleaned_content)
                    logger.info(f"Successfully extracted LLM data after cleanup: {extracted_data}")
                    return extracted_data
                except json.JSONDecodeError as e2:
                    logger.warning(f"Even after cleanup, JSON parsing failed: {e2}")
                    return {}
                
        except Exception as e:
            logger.error(f"LLM data extraction failed: {e}")
            # Only fall back to minimal extraction if LLM completely fails
            return self._minimal_fallback_extraction(conversation_history[-3:])
    
    def _minimal_fallback_extraction(self, recent_messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Minimal fallback extraction for when LLM is unavailable."""
        # Only extract very obvious things like explicit budget numbers
        extracted = {}
        
        last_message = ""
        for msg in reversed(recent_messages):
            # Handle both dict and string message formats defensively
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_message = msg.get("content", "").lower()
                break
            elif isinstance(msg, str):
                # If message is just a string, treat as user message
                last_message = msg.lower()
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
    
    def process_extracted_data(self, extracted: Dict[str, Any], collected_data: CollectedBusinessData):
        """Process incremental extracted data into hierarchical categories."""
        logger.info(f"Processing extracted data: {extracted}")
        
        # Handle business_goals - map to exact model structure
        if "business_goals" in extracted:
            logger.info("Processing business goals")
            goals_data = extracted["business_goals"]
            if isinstance(goals_data, dict):
                # Map primary_objectives
                if "primary_objectives" in goals_data and goals_data["primary_objectives"]:
                    collected_data.update_category_field("business_goals", "primary_objectives", goals_data["primary_objectives"], "future_state")
                    logger.info(f"Added business objectives: {goals_data['primary_objectives']}")
                
                # Map success_criteria
                if "success_criteria" in goals_data and goals_data["success_criteria"]:
                    collected_data.update_category_field("business_goals", "success_criteria", goals_data["success_criteria"], "future_state")
                    logger.info(f"Added success criteria: {goals_data['success_criteria']}")
                
                # Map KPIs
                if "kpis" in goals_data and goals_data["kpis"]:
                    collected_data.update_category_field("business_goals", "kpis", goals_data["kpis"], "future_state")
                    logger.info(f"Added KPIs: {goals_data['kpis']}")
        
        # Handle current_problems - map to exact model structure
        if "current_problems" in extracted:
            logger.info("Processing current problems")
            problems_data = extracted["current_problems"]
            if isinstance(problems_data, dict):
                # Map each problem type to correct field
                field_mapping = {
                    "technical_issues": "technical_issues",
                    "performance_issues": "reliability_issues",  # Map performance to reliability
                    "operational_issues": "operational_risks",
                    "security_risks": "security_risks", 
                    "cost_drains": "cost_drains"
                }
                
                for extracted_field, model_field in field_mapping.items():
                    if extracted_field in problems_data and problems_data[extracted_field]:
                        collected_data.update_category_field("current_problems", model_field, problems_data[extracted_field], "current_state")
                        logger.info(f"Added {model_field}: {problems_data[extracted_field]}")
        
        # Handle key_metrics - map to exact model structure
        if "key_metrics" in extracted:
            logger.info("Processing key metrics")
            metrics_data = extracted["key_metrics"]
            if isinstance(metrics_data, dict):
                # Map operational costs
                if "operational_costs" in metrics_data and metrics_data["operational_costs"]:
                    collected_data.update_category_field("key_metrics", "operational_costs", metrics_data["operational_costs"], "current_state")
                    logger.info(f"Added operational costs: {metrics_data['operational_costs']}")
                
                # Map user metrics
                if "user_metrics" in metrics_data and metrics_data["user_metrics"]:
                    collected_data.update_category_field("key_metrics", "user_metrics", metrics_data["user_metrics"], "current_state")
                    logger.info(f"Added user metrics: {metrics_data['user_metrics']}")
                
                # Map performance metrics
                if "performance_metrics" in metrics_data and metrics_data["performance_metrics"]:
                    collected_data.update_category_field("key_metrics", "performance_metrics", metrics_data["performance_metrics"], "current_state")
                    logger.info(f"Added performance metrics: {metrics_data['performance_metrics']}")
                
                # Map business metrics
                if "business_metrics" in metrics_data and metrics_data["business_metrics"]:
                    collected_data.update_category_field("key_metrics", "business_metrics", metrics_data["business_metrics"], "current_state")
                    logger.info(f"Added business metrics: {metrics_data['business_metrics']}")
        
        # Handle stakeholders - map to exact model structure
        if "stakeholders" in extracted:
            logger.info("Processing stakeholders")
            stakeholders_data = extracted["stakeholders"]
            if isinstance(stakeholders_data, dict):
                # Map decision makers
                if "decision_makers" in stakeholders_data and stakeholders_data["decision_makers"]:
                    collected_data.update_category_field("stakeholders", "decision_makers", stakeholders_data["decision_makers"], "current_state")
                    logger.info(f"Added decision makers: {stakeholders_data['decision_makers']}")
                
                # Map technical team
                if "technical_team" in stakeholders_data and stakeholders_data["technical_team"]:
                    collected_data.update_category_field("stakeholders", "technical_team", stakeholders_data["technical_team"], "current_state")
                    logger.info(f"Added technical team: {stakeholders_data['technical_team']}")
                
                # Map business users
                if "business_users" in stakeholders_data and stakeholders_data["business_users"]:
                    collected_data.update_category_field("stakeholders", "business_users", stakeholders_data["business_users"], "current_state")
                    logger.info(f"Added business users: {stakeholders_data['business_users']}")
        
        # Handle implementation_context - map to exact model structure
        if "implementation_context" in extracted:
            logger.info("Processing implementation context")
            context_data = extracted["implementation_context"]
            if isinstance(context_data, dict):
                # Map current technology to current_state
                if "current_technology" in context_data and context_data["current_technology"]:
                    collected_data.update_category_field("implementation_context", "technical_constraints", context_data["current_technology"], "current_state")
                    logger.info(f"Added current technology: {context_data['current_technology']}")
                
                # Map project budget to future_state
                if "project_budget" in context_data and context_data["project_budget"]:
                    collected_data.update_category_field("implementation_context", "project_budget", context_data["project_budget"], "future_state")
                    logger.info(f"Added project budget: {context_data['project_budget']}")
                
                # Map timeline requirements to future_state
                if "timeline_requirements" in context_data and context_data["timeline_requirements"]:
                    collected_data.update_category_field("implementation_context", "timeline_requirements", context_data["timeline_requirements"], "future_state")
                    logger.info(f"Added timeline requirements: {context_data['timeline_requirements']}")
                
                # Map technical constraints to current_state
                if "technical_constraints" in context_data and context_data["technical_constraints"]:
                    existing_constraints = collected_data.implementation_context.current_state.get("technical_constraints", [])
                    existing_constraints.extend(context_data["technical_constraints"])
                    collected_data.update_category_field("implementation_context", "technical_constraints", existing_constraints, "current_state")
                    logger.info(f"Added technical constraints: {context_data['technical_constraints']}")
                
                # Map project type as business constraint
                if "project_type" in context_data and context_data["project_type"]:
                    collected_data.update_category_field("implementation_context", "business_constraints", [f"Project Type: {context_data['project_type']}"], "future_state")
                    logger.info(f"Added project type: {context_data['project_type']}")