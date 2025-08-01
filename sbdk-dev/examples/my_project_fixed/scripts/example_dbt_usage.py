#!/usr/bin/env python
"""
Example script showing how to use dbt utilities to run dbt commands from Python.
"""
import sys
from pathlib import Path

# Add scripts directory to path to import our utilities
sys.path.insert(0, str(Path(__file__).parent))

from dbt_utils import (
    dbt_debug, dbt_run, dbt_test, dbt_build, 
    run_dbt, find_dbt_executable
)
from dbt_runner import DbtRunner


def example_using_utilities():
    """Example using the utility functions."""
    print("=== Example 1: Using utility functions ===\n")
    
    # Define project directory
    project_dir = Path(__file__).parent.parent / "dbt"
    
    try:
        # Run dbt debug
        print("1. Running dbt debug...")
        result = dbt_debug(project_dir=project_dir, debug=True)
        print(f"   Debug completed with exit code: {result.returncode}\n")
        
        # Run specific models
        print("2. Running specific model...")
        result = dbt_run(select="stg_users", project_dir=project_dir, debug=True)
        print(f"   Run completed with exit code: {result.returncode}\n")
        
        # Run tests
        print("3. Running tests...")
        result = dbt_test(project_dir=project_dir, debug=True)
        print(f"   Tests completed with exit code: {result.returncode}\n")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


def example_using_runner_class():
    """Example using the DbtRunner class."""
    print("\n=== Example 2: Using DbtRunner class ===\n")
    
    try:
        # Initialize runner
        runner = DbtRunner(
            project_dir=Path(__file__).parent.parent / "dbt"
        )
        
        # Get debug information
        print("1. Getting debug info...")
        debug_info = runner.debug()
        print(f"   dbt executable: {debug_info['dbt_path']}")
        print(f"   project_dir: {debug_info['project_dir']}")
        print(f"   exit_code: {debug_info['exit_code']}\n")
        
        # Run models
        print("2. Running all models...")
        result = runner.run()
        print(f"   Run completed with exit code: {result.returncode}\n")
        
        # Clean artifacts
        print("3. Cleaning artifacts...")
        result = runner.clean()
        print(f"   Clean completed with exit code: {result.returncode}\n")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


def example_custom_command():
    """Example running custom dbt command."""
    print("\n=== Example 3: Custom dbt command ===\n")
    
    try:
        # Run dbt list command
        print("Running dbt list...")
        result = run_dbt(
            ['list', '--resource-type', 'model'],
            project_dir=Path(__file__).parent.parent / "dbt",
            debug=False  # Disable debug output for cleaner results
        )
        
        print("Models in project:")
        for line in result.stdout.strip().split('\n'):
            print(f"  - {line}")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


def example_error_handling():
    """Example showing error handling."""
    print("\n=== Example 4: Error handling ===\n")
    
    try:
        # Try to run a non-existent model
        print("Attempting to run non-existent model...")
        result = dbt_run(
            select="non_existent_model",
            project_dir=Path(__file__).parent.parent / "dbt",
            check=False,  # Don't raise exception
            debug=False
        )
        
        if result.returncode != 0:
            print(f"Command failed as expected with exit code: {result.returncode}")
            print("Error output:", result.stderr[:200], "...")
        
    except Exception as e:
        print(f"Caught error: {type(e).__name__}: {e}")


def main():
    """Run all examples."""
    print("DBT Python Integration Examples")
    print("=" * 50)
    
    # Check if dbt is available
    try:
        dbt_path = find_dbt_executable()
        print(f"Found dbt at: {dbt_path}\n")
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please install dbt with: pip install dbt-duckdb")
        return 1
    
    # Run examples
    example_using_utilities()
    example_using_runner_class()
    example_custom_command()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())