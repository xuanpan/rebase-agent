#!/usr/bin/env python3
"""
Comprehensive test script for Rebase Agent API.

Tests all major endpoints and conversation flows.
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class RebaseAgentTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = None
        
    def test_health(self) -> bool:
        """Test health endpoint."""
        print("🏥 Testing Health Endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data['status']}")
                print(f"   ✅ Version: {data['version']}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    def test_chat_start(self, message: str) -> bool:
        """Test starting a chat conversation."""
        print(f"💬 Testing Chat Start: '{message[:50]}...'")
        try:
            payload = {"initial_message": message}
            response = requests.post(
                f"{self.base_url}/api/v1/chat/start",
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data['session_id']
                print(f"   ✅ Session ID: {self.session_id}")
                print(f"   ✅ Phase: {data['phase']}")
                print(f"   ✅ Progress: {data['progress']}%")
                print(f"   💡 Response: {data['response'][:100]}...")
                return True
            else:
                print(f"   ❌ Chat start failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Chat start error: {e}")
            return False
    
    def test_chat_continue(self, message: str) -> bool:
        """Test continuing a chat conversation."""
        if not self.session_id:
            print("   ⚠️  No session ID available. Run test_chat_start first.")
            return False
            
        print(f"💬 Testing Chat Continue: '{message[:50]}...'")
        try:
            payload = {
                "session_id": self.session_id,
                "message": message
            }
            response = requests.post(
                f"{self.base_url}/api/v1/chat/message",
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Phase: {data['current_phase']}")
                print(f"   ✅ Progress: {data['progress_percentage']}%")
                print(f"   ✅ Confidence: {data['confidence_level']}")
                print(f"   💡 Response: {data['message'][:100]}...")
                print(f"   🎯 Suggestions: {data['suggested_responses'][:2]}")
                return True
            else:
                print(f"   ❌ Chat continue failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Chat continue error: {e}")
            return False
    
    def test_session_summary(self) -> bool:
        """Test getting session summary."""
        if not self.session_id:
            print("   ⚠️  No session ID available.")
            return False
            
        print("📊 Testing Session Summary...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/chat/sessions/{self.session_id}/summary",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Domain: {data.get('domain_type', 'unknown')}")
                print(f"   ✅ Phase: {data['current_phase']}")
                print(f"   ✅ Messages: {data['conversation_length']}")
                print(f"   ✅ Facts: {len(data['discovered_facts'])} discovered")
                return True
            else:
                print(f"   ❌ Summary failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Summary error: {e}")
            return False
    
    def test_system_status(self) -> bool:
        """Test system status endpoint."""
        print("🔍 Testing System Status...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/analysis/system-status",
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ AI Provider: {data['ai_provider']['status']}")
                print(f"   ✅ Context Manager: {data['context_manager']['status']}")
                print(f"   ✅ Domains: {data['domain_registry']['registered_domains']} registered")
                return True
            else:
                print(f"   ❌ System status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ System status error: {e}")
            return False

def run_comprehensive_tests():
    """Run all tests in sequence."""
    print("🚀 REBASE AGENT API TESTING")
    print("=" * 50)
    print()
    
    tester = RebaseAgentTester()
    results = []
    
    # Test 1: Health Check
    results.append(tester.test_health())
    print()
    
    # Test 2: System Status
    results.append(tester.test_system_status())
    print()
    
    # Test 3: Start React to Vue Migration Chat
    results.append(tester.test_chat_start(
        "I want to migrate my React application to Vue.js. It has 50,000 lines of code."
    ))
    print()
    
    # Test 4: Continue conversation with team details
    results.append(tester.test_chat_continue(
        "We have 5 developers and spend 40% of our time on maintenance issues."
    ))
    print()
    
    # Test 5: Continue with business impact
    results.append(tester.test_chat_continue(
        "The maintenance costs us about $50,000 per month in developer time."
    ))
    print()
    
    # Test 6: Session summary
    results.append(tester.test_session_summary())
    print()
    
    # Test 7: New conversation - Python modernization
    results.append(tester.test_chat_start(
        "We need to modernize our legacy Python 2.7 system to Python 3.11."
    ))
    print()
    
    # Results summary
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

def run_quick_test():
    """Run a quick smoke test."""
    print("⚡ QUICK SMOKE TEST")
    print("=" * 20)
    
    tester = RebaseAgentTester()
    
    if not tester.test_health():
        print("❌ Service is not running or unhealthy!")
        return False
    
    if not tester.test_chat_start("I want to migrate from Angular to React."):
        print("❌ Chat functionality failed!")
        return False
    
    print("🎉 Quick test passed! Service is working.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_quick_test()
    else:
        success = run_comprehensive_tests()
    
    sys.exit(0 if success else 1)