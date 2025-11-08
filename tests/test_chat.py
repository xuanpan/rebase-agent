#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from core.conversation.chat_engine import ChatEngine
from core.llm_client import LLMClient
from core.prompt_engine import PromptEngine
from core.context_manager import ContextManager
from core.question_engine import QuestionEngine
from core.transformation_engine import UniversalTransformationEngine
from domains.domain_registry import DomainRegistry

async def test_chat_engine():
    """Test the chat engine functionality directly."""
    
    print("🧪 Testing Chat Engine Components...")
    
    try:
        # Initialize components
        llm_client = LLMClient()
        prompt_engine = PromptEngine()
        context_manager = ContextManager()
        domain_registry = DomainRegistry()
        question_engine = QuestionEngine(llm_client, prompt_engine)
        
        transformation_engine = UniversalTransformationEngine(
            llm_client=llm_client,
            prompt_engine=prompt_engine,
            context_manager=context_manager,
            question_engine=question_engine
        )
        transformation_engine.set_domain_registry(domain_registry)
        
        chat_engine = ChatEngine(
            llm_client=llm_client,
            prompt_engine=prompt_engine,
            context_manager=context_manager,
            question_engine=question_engine,
            transformation_engine=transformation_engine
        )
        
        print("✅ All components initialized successfully")
        
        # Test conversation start
        print("\n🚀 Testing conversation start...")
        result = await chat_engine.start_conversation(
            "I want to migrate my React application to Vue.js"
        )
        
        print(f"✅ Conversation started: {result['session_id']}")
        print(f"📝 Response: {result['response'][:100]}...")
        
        # Test message processing
        print("\n💬 Testing message processing...")
        response = await chat_engine.process_message(
            result['session_id'],
            "My React app has become difficult to maintain and our team prefers Vue syntax"
        )
        
        print(f"✅ Message processed successfully")
        print(f"📝 Response: {response.message[:100]}...")
        print(f"🎯 Phase: {response.current_phase}")
        print(f"📊 Progress: {response.progress_percentage}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_engine())
    exit(0 if success else 1)