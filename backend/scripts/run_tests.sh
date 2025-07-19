
# backend/scripts/run_tests.sh
#!/bin/bash
# Simple script to run tests with proper setup

echo "🧪 Running Users Module Tests..."

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Install missing dependencies if needed
echo "📦 Installing missing dependencies..."
pip install aiosqlite python-jose[cryptography] -q

# Setup test database
echo "🗃️ Setting up test database..."
python scripts/setup_test_db.py

# Run tests
echo "🔍 Running tests..."
python -m pytest modules/users/tests/ -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi

