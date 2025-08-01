#!/usr/bin/env python3
"""
Demonstration script showing the before and after of the dbt CLI fix.
This script shows how the fix handles various scenarios.
"""

import subprocess
import sys
import os
from pathlib import Path

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def test_original_approach():
    """Test the original problematic approach."""
    print_section("Testing Original Approach (run_dbt.py)")
    
    try:
        result = subprocess.run(
            [sys.executable, "run_dbt.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        print("Exit code:", result.returncode)
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        
        if result.returncode != 0:
            print("\n❌ Original approach failed (as expected)")
        else:
            print("\n✅ Original approach succeeded (unexpected)")
            
    except Exception as e:
        print(f"Error running original script: {e}")

def test_fixed_approach():
    """Test the fixed approach with various scenarios."""
    print_section("Testing Fixed Approach (run_dbt_fixed.py)")
    
    # Test 1: Basic usage
    print("\n--- Test 1: Basic Usage ---")
    try:
        result = subprocess.run(
            [sys.executable, "run_dbt_fixed.py", "--debug", "--version"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        print("Exit code:", result.returncode)
        if result.returncode == 0:
            print("✅ Fixed approach handles dbt path resolution")
        else:
            print("❌ Fixed approach failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With project directory
    print("\n--- Test 2: Project Directory Handling ---")
    try:
        result = subprocess.run(
            [sys.executable, "run_dbt_fixed.py", "--project-dir", "dbt", "--debug", "--version"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        print("Exit code:", result.returncode)
        if result.returncode == 0:
            print("✅ Correctly handles project directory")
        else:
            print("❌ Project directory handling failed")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Error handling
    print("\n--- Test 3: Error Handling ---")
    try:
        result = subprocess.run(
            [sys.executable, "run_dbt_fixed.py", "--project-dir", "/nonexistent", "run"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        print("Exit code:", result.returncode)
        if result.returncode != 0:
            print("✅ Properly handles missing project directory")
            print("Error message:", result.stdout.strip())
        else:
            print("❌ Should have failed for missing directory")
            
    except Exception as e:
        print(f"Error: {e}")

def compare_approaches():
    """Compare the two approaches side by side."""
    print_section("Comparison: Original vs Fixed")
    
    print("""
Original Approach Problems:
- ❌ Assumes 'dbt' is in PATH
- ❌ Doesn't handle virtual environments
- ❌ No project directory validation
- ❌ Poor error messages
- ❌ No debug information

Fixed Approach Solutions:
- ✅ Searches for dbt in multiple locations
- ✅ Properly handles virtual environments
- ✅ Validates project structure
- ✅ Comprehensive error handling
- ✅ Debug mode for troubleshooting
- ✅ Supports dbt as Python module
- ✅ Handles nested dbt directories
- ✅ Configures profiles directory
""")

def show_usage_examples():
    """Show how to use the fixed script."""
    print_section("Usage Examples")
    
    print("""
# Basic usage (runs dbt in current directory)
python run_dbt_fixed.py

# Run specific dbt command
python run_dbt_fixed.py compile

# Specify project directory
python run_dbt_fixed.py --project-dir /path/to/dbt/project run

# Debug mode to see configuration
python run_dbt_fixed.py --debug --version

# Run multiple dbt commands
python run_dbt_fixed.py run
python run_dbt_fixed.py test

# Use as a library in Python code:
from run_dbt_fixed import DBTRunner

runner = DBTRunner(project_dir="./dbt")
runner.run_dbt_command(["run", "--models", "staging"])
""")

def main():
    """Run all demonstrations."""
    print("DBT CLI Fix Demonstration")
    print("=" * 60)
    
    # Show current environment
    print(f"Python: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Virtual Env: {os.environ.get('VIRTUAL_ENV', 'Not active')}")
    
    # Run tests
    test_original_approach()
    test_fixed_approach()
    compare_approaches()
    show_usage_examples()
    
    print_section("Summary")
    print("""
The fixed version (run_dbt_fixed.py) provides a robust solution for running dbt
from Python scripts by:

1. Automatically finding dbt in various locations
2. Properly configuring the environment
3. Handling edge cases and errors gracefully
4. Supporting both CLI and library usage

This ensures dbt commands work reliably across different environments and setups.
""")

if __name__ == "__main__":
    main()