#!/bin/bash
# backend/fix_topics.sh
# Quick fix for Topics module import error

echo "🔧 Fixing Topics Module Import Error..."

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "📝 The issue was importing 'Decimal' from SQLAlchemy instead of Python's decimal module"
echo "✅ Fixed in the updated models file"

echo "🗃️ Now running database migration..."

# Create and run migration
alembic revision --autogenerate -m "Add topics module - fixed imports"
alembic upgrade head

echo "🧪 Testing Topics module..."
python test_topics_simple.py

if [ $? -eq 0 ]; then
    echo "✅ Topics module is working correctly!"
    echo "🚀 Starting server..."
    echo "   uvicorn main:app --reload"
else
    echo "❌ There are still issues to resolve"
fi