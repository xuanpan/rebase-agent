#!/bin/bash
# Rebase Agent Manual Testing Guide
# Copy and paste these commands one by one in your terminal

echo "🚀 REBASE AGENT MANUAL TESTING GUIDE"
echo "===================================="
echo
echo "📋 Prerequisites:"
echo "   1. Make sure you're in the project directory:"
echo "      cd /Users/XPAN17/Dev/mine/rebase/rebase-agent"
echo
echo "   2. Make sure the service is running:"
echo "      ps aux | grep uvicorn"
echo
echo "   3. If not running, start it:"
echo "      source .venv/bin/activate"
echo "      python -m uvicorn app.main:app --reload --port 8000"
echo
echo "🧪 STEP-BY-STEP TESTS:"
echo "======================"
echo
echo "📍 Step 1: Health Check"
echo "Copy and paste this command:"
echo
echo 'curl -s "http://localhost:8000/health" | python -m json.tool'
echo
echo "Expected output: {\"status\": \"healthy\", \"version\": \"0.1.0\"}"
echo
echo "📍 Step 2: Start Chat Conversation"
echo "Copy and paste this command:"
echo
echo 'curl -X POST "http://localhost:8000/api/v1/chat/start" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"initial_message": "I want to migrate my React app to Vue.js"}'\'' | python -m json.tool'
echo
echo "Expected: You'll get a session_id and initial response"
echo "📝 IMPORTANT: Save the session_id for the next steps!"
echo
echo "📍 Step 3: Continue Conversation"
echo "Replace SESSION_ID with the actual ID from Step 2:"
echo
echo 'curl -X POST "http://localhost:8000/api/v1/chat/message" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{
echo '    "session_id": "SESSION_ID", 
echo '    "message": "We have 5 developers and spend 40% of our time on maintenance"
echo '  }'\'' | python -m json.tool'
echo
echo "📍 Step 4: Get Session Summary"
echo "Replace SESSION_ID with your actual session ID:"
echo
echo 'curl -s "http://localhost:8000/api/v1/chat/sessions/SESSION_ID/summary" | python -m json.tool'
echo
echo "📍 Step 5: Test Different Scenarios"
echo "Try these different initial messages:"
echo
echo "🔄 Language Modernization:"
echo 'curl -X POST "http://localhost:8000/api/v1/chat/start" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"initial_message": "We need to upgrade from Python 2 to Python 3"}'\'' | python -m json.tool'
echo
echo "🏗️  System Modernization:"
echo 'curl -X POST "http://localhost:8000/api/v1/chat/start" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"initial_message": "Our legacy Java monolith needs modernization"}'\'' | python -m json.tool'
echo
echo "⚡ Performance Optimization:"
echo 'curl -X POST "http://localhost:8000/api/v1/chat/start" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{"initial_message": "Our application is too slow and needs optimization"}'\'' | python -m json.tool'
echo
echo "🌐 Web Interface Testing:"
echo "   Open your browser to: http://localhost:8000/docs"
echo "   This gives you an interactive API testing interface!"
echo
echo "✅ TESTING COMPLETE!"
echo "   You should see the AI responding to your transformation requests"
echo "   and asking intelligent follow-up questions to gather business data."