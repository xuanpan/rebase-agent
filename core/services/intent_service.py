"""Intent classification service for understanding user messages."""

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..llm_client import LLMClient
from ..models.chat import ConversationIntent
from ..prompts.intent_prompts import IntentPrompts


class IntentService:
    """Service for classifying user intent using LLM with fallback to rule-based approach."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def classify_intent(self, message: str, context) -> ConversationIntent:
        """Classify user intent using LLM with fallback to rule-based approach."""
        
        intent_prompt = IntentPrompts.build_intent_classification_prompt(message, context)

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
                return self.fallback_intent_classification(message, context)
                
        except Exception as e:
            try:
                logger.warning(f"LLM intent classification failed, using fallback: {e}")
            except:
                print(f"LLM intent classification failed, using fallback: {e}")
            
            # Fallback to rule-based approach
            return self.fallback_intent_classification(message, context)
    
    def fallback_intent_classification(self, message: str, context) -> ConversationIntent:
        """Minimal fallback classification - only for when LLM completely fails."""
        
        # Only use the most obvious signals as last resort
        message_lower = message.lower().strip()
        
        # Very basic patterns for emergency fallback only
        if message_lower in ["yes", "no", "ok", "okay"]:
            return ConversationIntent.ANSWER_QUESTION
        
        if message_lower.endswith("?"):
            return ConversationIntent.REQUEST_CLARIFICATION
            
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return ConversationIntent.GENERAL_CHAT
            
        # Default to answering question if we're in discovery phase
        if hasattr(context, 'current_phase') and context.current_phase == "discovery":
            return ConversationIntent.ANSWER_QUESTION
        
        # Assume they're providing information if we can't tell
        return ConversationIntent.ANSWER_QUESTION