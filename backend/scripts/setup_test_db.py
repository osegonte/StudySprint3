# backend/scripts/setup_test_db.py
"""Script to setup test database"""

import asyncio
import subprocess
import sys
from pathlib import Path

async def create_test_database():
    """Create test database for testing"""
    
    print("🗃️ Setting up test database...")
    
    try:
        # Create test database
        result = subprocess.run([
            "createdb", "-h", "localhost", "-p", "5432", 
            "-U", "studysprint", "studysprint3_test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test database created successfully")
        else:
            # Database might already exist
            print("ℹ️ Test database might already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test database: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_test_database())
