# backend/modules/users/run_tests.py
"""Script to run user module tests"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests for the users module"""
    
    # Get the current directory (users module)
    current_dir = Path(__file__).parent
    
    # Change to backend directory
    backend_dir = current_dir.parent.parent
    
    print("🧪 Running Users Module Tests...")
    print(f"📂 Backend directory: {backend_dir}")
    print(f"📁 Tests directory: {current_dir / 'tests'}")
    print("=" * 50)
    
    # Test command
    cmd = [
        sys.executable, "-m", "pytest",
        str(current_dir / "tests"),
        "-v",
        "--cov=modules.users",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=90"
    ]
    
    try:
        # Run tests
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Print results
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/")
        else:
            print("❌ Some tests failed!")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)