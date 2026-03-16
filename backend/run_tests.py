#!/usr/bin/env python3
"""
Test runner for SoloAnalyst backend
Usage: python run_tests.py
"""

import subprocess
import sys
import os

def run_tests():
    """Run all backend tests"""
    print("🧪 Running SoloAnalyst Backend Tests...")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Run pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)