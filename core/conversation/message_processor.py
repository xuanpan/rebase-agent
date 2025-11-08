"""
Message processor for handling and analyzing user messages.

This module processes incoming messages, detects intent, and prepares
them for the conversation engine.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import re
from dataclasses import dataclass

from loguru import logger


class MessageIntent(Enum):
    """Possible intents for user messages."""
    START_TRANSFORMATION = "start_transformation"
    PROVIDE_INFORMATION = "provide_information"
    ASK_QUESTION = "ask_question"
    REQUEST_ANALYSIS = "request_analysis"
    REQUEST_BUSINESS_CASE = "request_business_case"
    CLARIFICATION = "clarification"
    GREETING = "greeting"
    UNKNOWN = "unknown"


@dataclass
class ProcessedMessage:
    """Processed message with intent and extracted information."""
    original_message: str
    intent: MessageIntent
    confidence: float
    extracted_entities: Dict[str, Any]
    domain_hints: List[str]
    urgency_level: str = "medium"  # low, medium, high
    
    
class MessageProcessor:
    """Processes and analyzes user messages for intent and entities."""
    
    def __init__(self):
        """Initialize the message processor."""
        self.transformation_keywords = {
            "migrate", "migration", "upgrade", "modernize", "refactor",
            "rewrite", "convert", "transform", "transition", "move",
            "update", "revamp", "rearchitect"
        }
        
        self.framework_keywords = {
            "react", "vue", "angular", "svelte", "next", "nuxt",
            "express", "fastapi", "django", "flask", "spring",
            "laravel", "ruby on rails", "rails"
        }
        
        self.language_keywords = {
            "python", "javascript", "typescript", "java", "c#", "go",
            "rust", "php", "ruby", "swift", "kotlin", "dart"
        }
        
        self.business_keywords = {
            "roi", "cost", "budget", "timeline", "business case",
            "investment", "savings", "productivity", "efficiency",
            "revenue", "profit", "maintenance"
        }
        
        self.urgency_keywords = {
            "urgent": "high",
            "asap": "high", 
            "priority": "high",
            "critical": "high",
            "eventually": "low",
            "sometime": "low",
            "when possible": "low"
        }
    
    def process_message(self, message: str, context: Optional[Dict] = None) -> ProcessedMessage:
        """
        Process a user message and extract intent and entities.
        
        Args:
            message: The user's message
            context: Optional conversation context
            
        Returns:
            ProcessedMessage with analysis results
        """
        logger.info(f"Processing message: {message[:100]}...")
        
        message_lower = message.lower()
        
        # Detect intent
        intent = self._detect_intent(message_lower, context)
        confidence = self._calculate_confidence(intent, message_lower)
        
        # Extract entities
        entities = self._extract_entities(message_lower)
        
        # Detect domain hints
        domain_hints = self._detect_domains(message_lower)
        
        # Detect urgency
        urgency = self._detect_urgency(message_lower)
        
        processed = ProcessedMessage(
            original_message=message,
            intent=intent,
            confidence=confidence,
            extracted_entities=entities,
            domain_hints=domain_hints,
            urgency_level=urgency
        )
        
        logger.info(f"Processed message - Intent: {intent}, Confidence: {confidence}, Domains: {domain_hints}")
        
        return processed
    
    def _detect_intent(self, message: str, context: Optional[Dict] = None) -> MessageIntent:
        """Detect the intent of the message."""
        
        # Check for greetings
        greeting_patterns = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(pattern in message for pattern in greeting_patterns):
            return MessageIntent.GREETING
        
        # Check for transformation requests
        if any(keyword in message for keyword in self.transformation_keywords):
            return MessageIntent.START_TRANSFORMATION
        
        # Check for business case requests
        if any(keyword in message for keyword in self.business_keywords):
            if any(word in message for word in ["show", "give", "provide", "generate"]):
                return MessageIntent.REQUEST_BUSINESS_CASE
            return MessageIntent.REQUEST_ANALYSIS
        
        # Check for questions
        question_patterns = ["?", "how", "what", "when", "where", "why", "which"]
        if any(pattern in message for pattern in question_patterns):
            return MessageIntent.ASK_QUESTION
        
        # Check for information provision
        info_patterns = ["we have", "our system", "currently using", "built with"]
        if any(pattern in message for pattern in info_patterns):
            return MessageIntent.PROVIDE_INFORMATION
        
        # Check for clarification
        clarification_patterns = ["yes", "no", "exactly", "that's right", "correct"]
        if any(pattern in message for pattern in clarification_patterns):
            return MessageIntent.CLARIFICATION
        
        return MessageIntent.UNKNOWN
    
    def _calculate_confidence(self, intent: MessageIntent, message: str) -> float:
        """Calculate confidence score for detected intent."""
        
        base_confidence = 0.5
        
        if intent == MessageIntent.START_TRANSFORMATION:
            # Count transformation keywords
            keyword_count = sum(1 for keyword in self.transformation_keywords if keyword in message)
            base_confidence = min(0.9, 0.4 + (keyword_count * 0.2))
        
        elif intent == MessageIntent.REQUEST_BUSINESS_CASE:
            business_count = sum(1 for keyword in self.business_keywords if keyword in message)
            base_confidence = min(0.9, 0.5 + (business_count * 0.15))
        
        elif intent == MessageIntent.ASK_QUESTION:
            if "?" in message:
                base_confidence = 0.8
            else:
                base_confidence = 0.6
        
        elif intent == MessageIntent.GREETING:
            base_confidence = 0.9
            
        elif intent == MessageIntent.UNKNOWN:
            base_confidence = 0.3
        
        return round(base_confidence, 2)
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from the message."""
        
        entities = {}
        
        # Extract frameworks
        found_frameworks = [fw for fw in self.framework_keywords if fw in message]
        if found_frameworks:
            entities["frameworks"] = found_frameworks
        
        # Extract languages
        found_languages = [lang for lang in self.language_keywords if lang in message]
        if found_languages:
            entities["languages"] = found_languages
        
        # Extract numbers (for team size, timeline, etc.)
        numbers = re.findall(r'\b\d+\b', message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # Extract time references
        time_patterns = {
            "months": r'(\d+)\s*months?',
            "weeks": r'(\d+)\s*weeks?', 
            "years": r'(\d+)\s*years?',
            "days": r'(\d+)\s*days?'
        }
        
        for unit, pattern in time_patterns.items():
            matches = re.findall(pattern, message)
            if matches:
                entities[f"timeline_{unit}"] = [int(m) for m in matches]
        
        # Extract company/project context
        if "our" in message:
            entities["has_ownership_context"] = True
        
        if any(word in message for word in ["legacy", "old", "outdated"]):
            entities["legacy_system"] = True
            
        if any(word in message for word in ["team", "developers", "engineers"]):
            entities["has_team_context"] = True
        
        return entities
    
    def _detect_domains(self, message: str) -> List[str]:
        """Detect transformation domains from the message."""
        
        domains = []
        
        # Framework migration
        if (any(fw in message for fw in self.framework_keywords) or
            any(word in message for word in ["migrate", "migration", "framework"])):
            domains.append("framework_migration")
        
        # Language conversion  
        if (any(lang in message for lang in self.language_keywords) or
            any(word in message for word in ["convert", "rewrite", "port"])):
            domains.append("language_conversion")
        
        # Performance optimization
        if any(word in message for word in ["performance", "speed", "optimize", "slow", "fast"]):
            domains.append("performance_optimization")
        
        # Architecture redesign
        if any(word in message for word in ["architecture", "microservices", "monolith", "scalability"]):
            domains.append("architecture_redesign")
        
        # Dependency upgrade
        if any(word in message for word in ["upgrade", "update", "dependencies", "libraries", "packages"]):
            domains.append("dependency_upgrade")
        
        # Modernization (general)
        if any(word in message for word in ["modernize", "legacy", "outdated", "revamp"]):
            domains.append("modernization")
        
        return domains
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level from the message."""
        
        for keyword, level in self.urgency_keywords.items():
            if keyword in message:
                return level
        
        return "medium"  # default
    
    def extract_follow_up_context(self, message: str, previous_question: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract context for follow-up questions.
        
        Args:
            message: User's response
            previous_question: The question they're responding to
            
        Returns:
            Extracted context information
        """
        
        context = {}
        message_lower = message.lower()
        
        # Handle yes/no responses
        if any(word in message_lower for word in ["yes", "yeah", "yep", "correct", "right"]):
            context["confirmation"] = True
        elif any(word in message_lower for word in ["no", "nope", "incorrect", "wrong"]):
            context["confirmation"] = False
        
        # Extract specific answers based on question type
        if previous_question:
            prev_lower = previous_question.lower()
            
            # Team size questions
            if "team" in prev_lower and "size" in prev_lower:
                numbers = re.findall(r'\b(\d+)\b', message)
                if numbers:
                    context["team_size"] = int(numbers[0])
            
            # Timeline questions
            if "timeline" in prev_lower or "when" in prev_lower:
                # Extract timeline information
                time_patterns = {
                    "months": r'(\d+)\s*months?',
                    "weeks": r'(\d+)\s*weeks?',
                    "years": r'(\d+)\s*years?'
                }
                
                for unit, pattern in time_patterns.items():
                    matches = re.findall(pattern, message_lower)
                    if matches:
                        context[f"timeline_{unit}"] = int(matches[0])
            
            # Budget questions
            if "budget" in prev_lower or "cost" in prev_lower:
                # Extract monetary amounts
                money_patterns = [
                    r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $10,000.00
                    r'(\d+)k',  # 100k
                    r'(\d+)\s*thousand',  # 100 thousand
                    r'(\d+)\s*million'   # 1 million
                ]
                
                for pattern in money_patterns:
                    matches = re.findall(pattern, message_lower)
                    if matches:
                        context["budget_amount"] = matches[0]
                        break
        
        return context