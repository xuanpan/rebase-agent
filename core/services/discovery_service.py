"""Discovery service for managing conversation flow and discovery decisions."""

import json
from typing import Dict, Any, List, Tuple, Optional

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..models.discovery import CollectedBusinessData
from ..prompts.discovery_prompts import DiscoveryPrompts
from .data_extraction_service import DataExtractionService


class DiscoveryService:
    """Service for managing LLM-driven discovery decisions and completion responses."""
    
    def __init__(self, llm_client: LLMClient, data_extraction_service: DataExtractionService):
        self.llm_client = llm_client
        self.data_extraction = data_extraction_service
    
    async def get_llm_discovery_decision(
        self,
        conversation_history: List[Dict[str, str]],
        collected_data: CollectedBusinessData,
        context
    ) -> Dict[str, Any]:
        """
        Single LLM call to decide: continue discovery or complete discovery.
        This matches your exact requirements for the interactive discovery loop.
        """
        
        discovery_prompt = DiscoveryPrompts.build_discovery_decision_prompt(
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
                # Ensure decision is a dict before calling .get()
                if isinstance(decision, dict) and decision.get("status") == "complete":
                    return decision
                # If it's not a dict, treat as simple string response
                elif not isinstance(decision, dict):
                    logger.info(f"LLM returned non-dict JSON: {type(decision)} - {decision}")
                    # Fall through to string handling
                    pass
            except json.JSONDecodeError:
                pass
            
            # If not JSON, treat as simple next_question string
            # But also try to extract data from the latest user message
            extracted_data = await self.data_extraction.extract_data_from_conversation(conversation_history, collected_data)
            
            return {
                "next_question": content,
                "reasoning": "Continuing discovery process",
                "progress_percentage": self._calculate_progress_from_data(collected_data, extracted_data),
                "confidence": 0.8,
                "extracted_data": extracted_data
            }
            
        except Exception as e:
            try:
                logger.warning(f"LLM discovery decision failed at line, using fallback: {e}")
                logger.warning(f"Exception type: {type(e)}, Args: {e.args}")
                import traceback
                logger.warning(f"Full traceback: {traceback.format_exc()}")
            except:
                print(f"LLM discovery decision failed, using fallback: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
            
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
                # Map category names to readable text
                category_names = {
                    "business_goals": "your business goals and objectives",
                    "stakeholders": "key stakeholders and decision makers", 
                    "current_problems": "current challenges and problems",
                    "key_metrics": "key metrics and performance indicators",
                    "implementation_context": "implementation context and constraints"
                }
                
                readable_category = category_names.get(missing[0], "your current situation") if missing else "your current situation"
                
                return {
                    "next_question": f"Could you tell me more about {readable_category}?",
                    "reasoning": "Need more information for complete business case",
                    "progress_percentage": completeness * 25,
                    "confidence": 0.6
                }
    
    async def generate_completion_response(
        self,
        llm_decision: Dict[str, Any],
        collected_data: CollectedBusinessData,
        context
    ) -> Tuple[str, str, float, Optional[str]]:
        """Generate response when discovery is complete and ready for next phase."""
        
        response_content = DiscoveryPrompts.build_completion_response_prompt(
            llm_decision, collected_data, context
        )
        
        return response_content, "assessment", 30.0, "proceed_to_assessment"
    
    def _calculate_progress_from_data(self, collected_data: CollectedBusinessData, new_extracted_data: Dict[str, Any]) -> float:
        """Calculate progress percentage based on collected data."""
        # Simulate updating data to calculate what the progress would be
        temp_data = collected_data
        if new_extracted_data:
            self.data_extraction.process_extracted_data(new_extracted_data, temp_data)
        
        # Calculate overall completeness
        return temp_data.get_overall_completeness_score() * 100