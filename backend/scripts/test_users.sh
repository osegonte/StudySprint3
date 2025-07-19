#!/bin/bash
# Script to run users module tests

echo "🧪 Running Users Module Tests..."

# Navigate to backend directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Run tests with coverage
python -m pytest modules/users/tests/ \
    -v \
    --cov=modules.users \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=90 \
    --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report: htmlcov/index.html"
else
    echo "❌ Some tests failed!"
    exit 1
fi
