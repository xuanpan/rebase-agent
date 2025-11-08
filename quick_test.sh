#!/bin/bash
# Quick test script for Rebase Agent

echo "🚀 REBASE AGENT - QUICK TEST SUITE"
echo "=================================="
echo

# Test 1: Health Check
echo "🏥 1. Health Check"
curl -s "http://localhost:8000/health" | python -m json.tool
echo
echo

# Test 2: Start Chat - React to Vue Migration  
echo "💬 2. Start Chat (React → Vue)"
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/chat/start" \
  -H "Content-Type: application/json" \
  -d '{"initial_message": "I want to migrate my React app to Vue.js"}')

echo "$RESPONSE" | python -m json.tool

# Extract session ID for next test
SESSION_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)
echo
echo "📝 Session ID: $SESSION_ID"
echo

# Test 3: Continue Conversation
if [ ! -z "$SESSION_ID" ]; then
    echo "💬 3. Continue Chat (Add Details)"
    curl -s -X POST "http://localhost:8000/api/v1/chat/message" \
      -H "Content-Type: application/json" \
      -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"We have 5 developers and maintenance takes 40% of our time.\"}" | python -m json.tool
    echo
    echo
    
    # Test 4: Session Summary
    echo "📊 4. Session Summary"
    curl -s "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/summary" | python -m json.tool
    echo
fi

echo "✅ Basic tests completed!"
echo
echo "🌐 For interactive testing, visit: http://localhost:8000/docs"