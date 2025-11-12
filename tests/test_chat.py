#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from core.conversation.chat_engine import ChatEngine
from core.llm_client import LLMClient
from core.context_manager import ContextManager

async def test_chat_engine():
    """Test the unified chat engine functionality."""
    
    print("🧪 Testing Unified Chat Engine...")
    
    try:
        # Initialize simplified components
        llm_client = LLMClient()
        context_manager = ContextManager()
        
        # Create unified chat engine
        chat_engine = ChatEngine(
            llm_client=llm_client,
            context_manager=context_manager
        )
        
        print("✅ Chat engine initialized successfully")
        
        # Test session creation and basic conversation
        test_session = "test_session_123"
        print(f"\n🗣️  Testing conversation with session: {test_session}")
        
        # Start a conversation
        response = await chat_engine.start_conversation(
            initial_message="I want to modernize my legacy Java application to use microservices"
        )
        
        print(f"Session ID: {response['session_id']}")
        print(f"Response: {response['response'][:200]}...")
        
        # Test follow-up message using process_message
        followup = await chat_engine.process_message(
            session_id=response['session_id'],
            user_message="What are the main benefits of this transformation?"
        )
        
        print(f"Follow-up response: {followup.message[:200]}...")
        
        # Test discovery summary using the session from response
        summary = await chat_engine.get_discovery_summary(response['session_id'])
        print(f"\n📊 Discovery Summary:")
        if 'categories' in summary:
            for category_name, category in summary['categories'].items():
                print(f"  {category_name}: {category['status']} ({category['progress']*100:.1f}%)")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_engine())
    exit(0 if success else 1)