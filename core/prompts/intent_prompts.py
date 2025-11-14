"""Intent classification prompts."""

from typing import Dict, Any, List


class IntentPrompts:
    """Centralized intent classification prompt management."""
    
    @staticmethod
    def build_intent_classification_prompt(message: str, context) -> str:
        """Build intelligent intent classification prompt with semantic understanding."""
        
        # Get conversation context
        phase = getattr(context, 'current_phase', 'unknown')
        history_length = len(getattr(context, 'conversation_history', []))
        
        # Get recent conversation for context
        recent_context = ""
        if hasattr(context, 'conversation_history') and context.conversation_history:
            last_few = context.conversation_history[-2:] if len(context.conversation_history) >= 2 else context.conversation_history
            recent_context = "\n".join([f"{msg.role}: {msg.content[:100]}" for msg in last_few])
        
        return f"""
You are an expert at understanding user intent in business conversations about system transformations.

CURRENT MESSAGE: "{message}"

CONVERSATION CONTEXT:
Phase: {phase}
Messages exchanged: {history_length}
Recent conversation:
{recent_context if recent_context else "No previous context"}

INTENT CATEGORIES:

1. START_TRANSFORMATION
   - User wants to begin a modernization/migration project
   - Examples: "We need to migrate our system", "Looking to modernize our app", "Want to upgrade from React 16"
   - Key: Expresses desire to change/improve existing system

2. ANSWER_QUESTION  
   - User is providing information in response to agent questions
   - Examples: "We have 50 developers", "Our budget is $500k", "The main problem is performance"
   - Key: Giving factual information, especially in discovery phase

3. REQUEST_CLARIFICATION
   - User wants explanation about something the agent said
   - Examples: "What do you mean by technical debt?", "Can you explain that approach?", "How does that work?"
   - Key: Asking for understanding/explanation

4. APPROVE_BUSINESS_CASE
   - User accepts/approves a proposed plan or recommendation  
   - Examples: "That sounds good", "Let's proceed", "I approve this approach", "Yes, move forward"
   - Key: Expressing agreement/approval to continue

5. REQUEST_MORE_INFO
   - User wants additional details or information
   - Examples: "Tell me more about the timeline", "What are the risks?", "Show me the costs"
   - Key: Asking for additional details on a topic

6. GENERAL_CHAT
   - General conversation, greetings, or off-topic discussion
   - Examples: "Hello", "How are you?", "Thanks", "Goodbye"
   - Key: Social interaction, not business-focused

ANALYSIS INSTRUCTIONS:
- Focus on semantic meaning, not keywords
- Consider the conversation flow and context
- Understand implied meaning and cultural variations
- Look at the user's actual goal/need behind the message
- Consider follow-up vs. new topic patterns

Respond with only the intent category name (e.g., "ANSWER_QUESTION").
"""