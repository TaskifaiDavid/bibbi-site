#!/usr/bin/env python3
"""
Consolidated test runner for all backend tests
Replaces multiple individual test files with organized test suite
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run all tests"""
    print("🚀 Starting Backend Test Suite")
    print("=" * 60)
    
    try:
        # Import and run consolidated chat tests
        from tests.test_chat_system import run_tests
        run_tests()
        
    except ImportError as e:
        print(f"❌ Failed to import tests: {e}")
        print("Make sure all dependencies are installed")
        return 1
    
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1
    
    print("\n✅ All tests completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())