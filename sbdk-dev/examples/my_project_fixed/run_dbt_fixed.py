#!/usr/bin/env python3
"""
Fixed version of the dbt runner script that properly handles:
1. Virtual environment detection and dbt path resolution
2. Working directory management
3. Environment variable configuration
4. Comprehensive error handling
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
import json

class DBTRunner:
    def __init__(self, project_dir=None):
        """
        Initialize DBT Runner with proper path resolution.
        
        Args:
            project_dir: Path to the dbt project directory (containing dbt_project.yml)
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.dbt_path = self._find_dbt_executable()
        self.profiles_dir = self._find_profiles_dir()
        
    def _find_dbt_executable(self):
        """Find the dbt executable, checking virtual environment first."""
        # Check if we're in a virtual environment
        venv_path = os.environ.get('VIRTUAL_ENV')
        
        if venv_path:
            # Look for dbt in the virtual environment
            venv_dbt = Path(venv_path) / 'bin' / 'dbt'
            if venv_dbt.exists():
                print(f"Found dbt in virtual environment: {venv_dbt}")
                return str(venv_dbt)
        
        # Check if dbt is in the current Python environment
        python_prefix = Path(sys.prefix)
        prefix_dbt = python_prefix / 'bin' / 'dbt'
        if prefix_dbt.exists():
            print(f"Found dbt in Python prefix: {prefix_dbt}")
            return str(prefix_dbt)
        
        # Check common UV installation paths
        uv_paths = [
            Path.home() / '.local' / 'bin' / 'dbt',
            Path.home() / '.cargo' / 'bin' / 'dbt',
            Path('/usr/local/bin/dbt'),
        ]
        
        for uv_dbt in uv_paths:
            if uv_dbt.exists():
                print(f"Found dbt at: {uv_dbt}")
                return str(uv_dbt)
        
        # Fall back to system PATH
        dbt_in_path = shutil.which('dbt')
        if dbt_in_path:
            print(f"Found dbt in system PATH: {dbt_in_path}")
            return dbt_in_path
        
        # Last resort: try to run with python -m dbt
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'dbt', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("dbt available as Python module")
                return None  # Will use python -m dbt
        except:
            pass
        
        raise FileNotFoundError(
            "dbt not found. Please install dbt using one of:\n"
            "  - pip install dbt-duckdb\n"
            "  - uv pip install dbt-duckdb\n"
            "  - conda install -c conda-forge dbt-duckdb"
        )
    
    def _find_profiles_dir(self):
        """Find the dbt profiles directory."""
        # Check environment variable first
        profiles_dir = os.environ.get('DBT_PROFILES_DIR')
        if profiles_dir and Path(profiles_dir).exists():
            return Path(profiles_dir)
        
        # Check default location
        default_profiles = Path.home() / '.dbt'
        if default_profiles.exists():
            return default_profiles
        
        # Check project directory
        project_profiles = self.project_dir / 'profiles'
        if project_profiles.exists():
            return project_profiles
        
        # Create default if none exists
        default_profiles.mkdir(parents=True, exist_ok=True)
        return default_profiles
    
    def _validate_project_dir(self):
        """Validate that the project directory contains a dbt project."""
        dbt_project_file = self.project_dir / 'dbt_project.yml'
        if not dbt_project_file.exists():
            # Try to find dbt directory
            dbt_dir = self.project_dir / 'dbt'
            if dbt_dir.exists() and (dbt_dir / 'dbt_project.yml').exists():
                self.project_dir = dbt_dir
                return True
            
            raise FileNotFoundError(
                f"No dbt_project.yml found in {self.project_dir}\n"
                "Please ensure you're in a dbt project directory or specify the correct path."
            )
        return True
    
    def run_dbt_command(self, command, **kwargs):
        """
        Run a dbt command with proper environment setup.
        
        Args:
            command: The dbt command to run (e.g., "run", "test", "compile")
            **kwargs: Additional arguments to pass to subprocess.run
        
        Returns:
            subprocess.CompletedProcess object
        """
        self._validate_project_dir()
        
        # Prepare command
        if isinstance(command, str):
            command_parts = command.split()
        else:
            command_parts = list(command)
        
        # Build the full command
        if self.dbt_path:
            full_command = [self.dbt_path] + command_parts
        else:
            # Use python -m dbt
            full_command = [sys.executable, '-m', 'dbt'] + command_parts
        
        # Set up environment
        env = os.environ.copy()
        env['DBT_PROFILES_DIR'] = str(self.profiles_dir)
        
        # Add virtual environment to PATH if active
        if 'VIRTUAL_ENV' in os.environ:
            venv_bin = Path(os.environ['VIRTUAL_ENV']) / 'bin'
            env['PATH'] = f"{venv_bin}:{env.get('PATH', '')}"
        
        # Default kwargs
        default_kwargs = {
            'capture_output': True,
            'text': True,
            'env': env,
            'cwd': str(self.project_dir)
        }
        default_kwargs.update(kwargs)
        
        print(f"Running command: {' '.join(full_command)}")
        print(f"Working directory: {self.project_dir}")
        print(f"Profiles directory: {self.profiles_dir}")
        
        try:
            result = subprocess.run(full_command, **default_kwargs)
            
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, full_command, result.stdout, result.stderr
                )
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"\nError running dbt command: {e}")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            raise
        except Exception as e:
            print(f"\nUnexpected error: {type(e).__name__}: {e}")
            raise
    
    def debug_info(self):
        """Print debug information about the dbt setup."""
        print("=== DBT Runner Debug Info ===")
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not active')}")
        print(f"DBT executable: {self.dbt_path}")
        print(f"DBT profiles directory: {self.profiles_dir}")
        print(f"Project directory: {self.project_dir}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"PATH: {os.environ.get('PATH', '')}")
        print("============================\n")


def main():
    """Main function demonstrating proper dbt execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run dbt commands with proper path handling')
    parser.add_argument('--project-dir', help='Path to dbt project directory')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    parser.add_argument('command', nargs='*', default=['run'], help='dbt command to execute')
    parser.add_argument('--version', action='store_true', help='Show dbt version')
    
    args = parser.parse_args()
    
    try:
        # Initialize the runner
        runner = DBTRunner(project_dir=args.project_dir)
        
        if args.debug:
            runner.debug_info()
        
        # Handle version flag
        if args.version:
            print("Checking dbt version...")
            runner.run_dbt_command(['--version'])
            return
        
        # Run dbt version first
        print("Checking dbt version...")
        runner.run_dbt_command(['--version'])
        
        # Run the requested command
        if args.command and args.command != ['run']:
            print(f"\nRunning dbt {' '.join(args.command)}...")
            runner.run_dbt_command(args.command)
            print("\nCommand completed successfully!")
        elif args.command == ['run']:
            print(f"\nRunning dbt run...")
            runner.run_dbt_command(['run'])
            print("\nCommand completed successfully!")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()