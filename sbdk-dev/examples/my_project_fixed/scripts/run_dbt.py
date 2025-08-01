#!/usr/bin/env python
"""
Simple dbt runner script with common fixes for subprocess execution issues.
"""
import subprocess
import os
import sys
from pathlib import Path


def run_dbt_command(dbt_args, project_dir=None):
    """
    Run dbt command with proper environment setup.
    
    Args:
        dbt_args: List of dbt command arguments (e.g., ['run', '--select', 'model'])
        project_dir: Path to dbt project directory (optional)
    
    Returns:
        subprocess.CompletedProcess result
    """
    # Determine project directory
    if project_dir:
        project_dir = Path(project_dir).resolve()
    else:
        # Default to dbt directory in current project
        project_dir = Path(__file__).parent.parent / "dbt"
        if not project_dir.exists():
            project_dir = Path.cwd()
    
    # Prepare environment with expanded paths
    env = os.environ.copy()
    
    # Ensure HOME is set for ~ expansion
    if 'HOME' not in env:
        env['HOME'] = str(Path.home())
    
    # Expand profiles directory path
    profiles_dir = Path(env.get('DBT_PROFILES_DIR', '~/.dbt')).expanduser().resolve()
    env['DBT_PROFILES_DIR'] = str(profiles_dir)
    
    # Build command - use full path to dbt if available
    dbt_executable = 'dbt'
    
    # Check for dbt in virtual environment first
    if hasattr(sys, 'prefix'):
        venv_dbt = Path(sys.prefix) / 'bin' / 'dbt'
        if venv_dbt.exists():
            dbt_executable = str(venv_dbt)
    
    # Build full command
    cmd = [dbt_executable] + dbt_args
    
    # Add project directory if not specified
    if '--project-dir' not in dbt_args:
        cmd.extend(['--project-dir', str(project_dir)])
    
    # Add profiles directory if not specified
    if '--profiles-dir' not in dbt_args:
        cmd.extend(['--profiles-dir', str(profiles_dir)])
    
    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {project_dir}")
    print(f"Environment HOME: {env.get('HOME')}")
    print(f"DBT_PROFILES_DIR: {env.get('DBT_PROFILES_DIR')}")
    
    try:
        # Run with shell=False for better security and error handling
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("=== STDOUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== STDERR ===")
            print(result.stderr)
            
        return result
        
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code: {e.returncode}")
        print("=== STDOUT ===")
        print(e.stdout)
        print("=== STDERR ===") 
        print(e.stderr)
        raise
    except FileNotFoundError:
        print(f"Error: dbt executable not found at '{dbt_executable}'")
        print("Please ensure dbt is installed: pip install dbt-duckdb")
        raise


def main():
    """Run common dbt commands."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run dbt commands with proper environment setup')
    parser.add_argument('command', nargs='+', help='dbt command and arguments')
    parser.add_argument('--project-dir', help='Path to dbt project directory')
    
    args = parser.parse_args()
    
    try:
        run_dbt_command(args.command, args.project_dir)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Example: Run dbt debug
    print("=== Testing dbt debug command ===")
    try:
        run_dbt_command(['debug'])
    except Exception as e:
        print(f"Debug failed: {e}")
    
    print("\n=== Testing dbt run command ===")
    try:
        run_dbt_command(['run'])
    except Exception as e:
        print(f"Run failed: {e}")
    
    # For CLI usage
    # sys.exit(main())