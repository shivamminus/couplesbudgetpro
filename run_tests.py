#!/usr/bin/env python3
"""Test runner script"""
import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_tests():
    """Discover and run all tests"""
    # Set testing environment
    os.environ['FLASK_CONFIG'] = 'testing'
    
    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
