#!/usr/bin/env python3
"""
Original problematic script that fails to run dbt commands.
This script demonstrates the issue where dbt CLI is not found.
"""

import subprocess
import sys
import os

def run_dbt_command(command):
    """Run a dbt command and return the result."""
    try:
        print(f"Running: dbt {command}")
        result = subprocess.run(
            ["dbt"] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running dbt command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: dbt command not found. Please ensure dbt is installed and in your PATH.")
        sys.exit(1)

if __name__ == "__main__":
    # This is the problematic approach - assumes dbt is in PATH
    # and doesn't handle virtual environments properly
    
    print("Current working directory:", os.getcwd())
    print("Python executable:", sys.executable)
    print("PATH:", os.environ.get("PATH", ""))
    
    # Try to run dbt
    run_dbt_command("--version")
    run_dbt_command("run")