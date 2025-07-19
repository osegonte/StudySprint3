# backend/scripts/init_users_module.py
"""Script to initialize users module and run migration"""

import asyncio
import subprocess
import sys
from pathlib import Path

async def main():
    """Initialize users module"""
    
    print("🔧 Initializing Users Module...")
    
    # Get backend directory
    backend_dir = Path(__file__).parent.parent
    
    print(f"📂 Backend directory: {backend_dir}")
    
    # Run Alembic migration
    print("📊 Creating database migration...")
    
    try:
        # Create migration
        result = subprocess.run([
            sys.executable, "-m", "alembic", "revision", "--autogenerate", 
            "-m", "Add users module"
        ], cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Migration creation failed: {result.stderr}")
            return False
        
        print("✅ Migration created successfully")
        
        # Apply migration
        print("🔄 Applying migration...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd=backend_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Migration failed: {result.stderr}")
            return False
        
        print("✅ Migration applied successfully")
        
        # Run tests
        print("🧪 Running module tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", "modules/users/tests/", "-v"
        ], cwd=backend_dir)
        
        if result.returncode != 0:
            print("❌ Some tests failed")
            return False
        
        print("✅ All tests passed!")
        
        print("\n" + "="*50)
        print("🎉 Users Module Initialization Complete!")
        print("="*50)
        print("\n📋 Next Steps:")
        print("   1. Start the backend server:")
        print("      uvicorn main:app --reload")
        print("   2. Test the endpoints at:")
        print("      http://localhost:8000/api/docs")
        print("   3. Try registering a user:")
        print("      POST /api/v1/auth/register")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)