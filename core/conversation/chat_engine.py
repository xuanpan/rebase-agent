"""
Chat Engine - LLM-driven conversational orchestrator with modular services.

Single unified system that combines intelligent data collection, conversation flow,
and business discovery with the universal transformation engine.
"""

from typing import Dict, Any, List, Optional

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..context_manager import ContextManager
from ..models import (
    CollectedBusinessData,
    ChatResponse,
    MessageAnalysis,
    ConversationIntent
)
from ..services import (
    DataExtractionService,
    IntentService,
    DiscoveryService
)
from ..prompts.discovery_prompts import DiscoveryPrompts


class ChatEngine:
    """Conversational orchestrator with modular services."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        context_manager: ContextManager
    ):
        self.llm_client = llm_client
        self.context_manager = context_manager
        
        # Initialize services with dependency injection
        self.data_extraction_service = DataExtractionService(llm_client)
        self.intent_service = IntentService(llm_client)
        self.discovery_service = DiscoveryService(llm_client, self.data_extraction_service)
        
        # In-memory storage for collected business data (in production, this would be persistent)
        self.session_business_data: Dict[str, CollectedBusinessData] = {}
        
        try:
            logger.info("ChatEngine initialized with modular services")
        except:
            print("ChatEngine initialized with modular services")
    
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
                # Try to load from persisted context first
                if context.discovered_facts:
                    self.session_business_data[session_id] = CollectedBusinessData.from_dict(context.discovered_facts)
                else:
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
            
            # Step 3: Use discovery service for LLM decision
            llm_decision = await self.discovery_service.get_llm_discovery_decision(
                conversation_history, collected_data, context
            )
            
            # Step 4: LLM returns either next question or completion
            if llm_decision.get("status") == "complete":
                # Discovery is complete - transition to next phase
                response_content, next_phase, progress, action_required = await self.discovery_service.generate_completion_response(
                    llm_decision, collected_data, context
                )
            else:
                # Continue discovery with next question
                response_content = llm_decision.get("next_question", "Could you tell me more about your current situation?")
                next_phase = "discovery"
                progress = llm_decision.get("progress_percentage", 15.0)
                action_required = None
                
                # Update collected data from LLM response using service
                if "extracted_data" in llm_decision:
                    logger.info(f"Processing extracted data: {llm_decision['extracted_data']}")
                    self.data_extraction_service.process_extracted_data(llm_decision["extracted_data"], collected_data)
                    self.session_business_data[session_id] = collected_data
                    
                    # Persist business data to context for permanence
                    self.context_manager.update_context(
                        session_id, 
                        discovered_facts=collected_data.to_dict()
                    )
                    
                    logger.info(f"Updated session data. New completeness: {collected_data.get_overall_completeness_score()}")
                else:
                    logger.info("No extracted_data found in LLM decision")
            
            # Add assistant response to conversation
            self.context_manager.add_message(session_id, "assistant", response_content)
            
            # Update context with new phase if changed
            if next_phase != context.current_phase:
                self.context_manager.update_context(session_id, current_phase=next_phase)
            
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
    
    async def _generate_initial_response(
        self,
        initial_message: str,
        session_id: str
    ) -> str:
        """Generate initial conversational response to start the transformation analysis."""
        
        try:
            # Use centralized prompt system
            initial_prompt = DiscoveryPrompts.build_initial_response_prompt(initial_message)
            
            response = await self.llm_client.chat_completion([
                {
                    "role": "system",
                    "content": "You are an expert business transformation consultant who asks insightful questions to understand the business context and ROI drivers."
                },
                {"role": "user", "content": initial_prompt}
            ])
            
            initial_response = response.content.strip()
            logger.info(f"Generated LLM initial response for session {session_id}")
            
            # Add the response to conversation history
            self.context_manager.add_message(session_id, "assistant", initial_response)
            
            return initial_response
            
        except Exception as e:
            logger.error(f"Error generating LLM initial response: {e}")
            # Only use fallback if LLM completely fails
            fallback_response = ("I'd love to help you explore this transformation! "
                               "Let me understand your current situation better. "
                               "What specific challenges are you facing that made you consider this change?")
            self.context_manager.add_message(session_id, "assistant", fallback_response)
            return fallback_response
    
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