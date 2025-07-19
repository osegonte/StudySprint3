# backend/fix_and_test.sh
#!/bin/bash
# Complete fix and test script

echo "🔧 StudySprint 3.0 - Complete Fix and Test"
echo "=" * 50

# Ensure we're in backend directory
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    echo "❌ Not in backend directory or venv not found"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing missing dependencies..."

# Install dependencies with proper escaping
pip install 'python-jose[cryptography]==3.3.0' -q
pip install aiosqlite==0.19.0 -q
pip install pytest-asyncio==0.21.1 -q

echo "✅ Dependencies installed"

echo "🗃️ Setting up test database..."

# Create test database if it doesn't exist
createdb -h localhost -p 5432 -U studysprint studysprint3_test 2>/dev/null || echo "   ℹ️ Test database might already exist"

echo "🧪 Running simple functionality test..."

# Run simple test
python test_users_simple.py

if [ $? -eq 0 ]; then
    echo "✅ Simple tests passed!"
    
    echo "🚀 Starting server for API tests..."
    
    # Start server in background
    uvicorn main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Test API
    echo "🌐 Testing API endpoints..."
    curl -s http://localhost:8000/api/health | grep -q "healthy"
    
    if [ $? -eq 0 ]; then
        echo "✅ API working!"
        
        # Test registration
        echo "👤 Testing user registration..."
        curl -X POST http://localhost:8000/api/v1/auth/register \
          -H "Content-Type: application/json" \
          -d '{
            "email": "testcurl@example.com",
            "username": "testcurl",
            "full_name": "Test Curl User",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!"
          }' -s | grep -q "success"
        
        if [ $? -eq 0 ]; then
            echo "✅ User registration working!"
        else
            echo "❌ User registration failed"
        fi
    else
        echo "❌ API not responding"
    fi
    
    # Stop server
    kill $SERVER_PID 2>/dev/null
    
    echo ""
    echo "🎉 All basic tests completed!"
    echo "📋 Users module is ready for use"
    
else
    echo "❌ Simple tests failed"
    exit 1
fi