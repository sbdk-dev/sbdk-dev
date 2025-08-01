#!/usr/bin/env python
"""
Robust dbt CLI runner that handles common subprocess execution issues.
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys
import json


class DbtRunner:
    """Handles dbt CLI execution with proper environment setup and error handling."""
    
    def __init__(self, project_dir: Optional[str] = None, profiles_dir: Optional[str] = None):
        """
        Initialize the dbt runner.
        
        Args:
            project_dir: Path to dbt project directory. Defaults to current directory.
            profiles_dir: Path to dbt profiles directory. Defaults to ~/.dbt
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path.home() / ".dbt"
        
        # Ensure paths exist
        if not self.project_dir.exists():
            raise ValueError(f"Project directory does not exist: {self.project_dir}")
            
        # Expand paths to absolute
        self.project_dir = self.project_dir.resolve()
        self.profiles_dir = self.profiles_dir.resolve()
        
        # Find dbt executable
        self.dbt_path = self._find_dbt_executable()
        
    def _find_dbt_executable(self) -> str:
        """Find the dbt executable in PATH or virtual environment."""
        # First check if dbt is in the current virtual environment
        venv_dbt = None
        if hasattr(sys, 'prefix'):
            venv_bin = Path(sys.prefix) / 'bin' / 'dbt'
            if venv_bin.exists():
                venv_dbt = str(venv_bin)
        
        # Use shutil.which to find dbt in PATH
        system_dbt = shutil.which('dbt')
        
        # Prefer venv dbt over system dbt
        dbt_path = venv_dbt or system_dbt
        
        if not dbt_path:
            raise RuntimeError(
                "dbt executable not found. Please ensure dbt is installed and in PATH."
            )
            
        return dbt_path
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for dbt execution."""
        env = os.environ.copy()
        
        # Ensure HOME is set (important for ~ expansion)
        if 'HOME' not in env:
            env['HOME'] = str(Path.home())
            
        # Add Python path if in virtual environment
        if hasattr(sys, 'prefix'):
            env['VIRTUAL_ENV'] = sys.prefix
            
        # Ensure profiles directory is accessible
        env['DBT_PROFILES_DIR'] = str(self.profiles_dir)
        
        return env
    
    def run_command(
        self, 
        command: List[str], 
        check: bool = True,
        capture_output: bool = True,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a dbt command with proper error handling.
        
        Args:
            command: List of command arguments (e.g., ['run', '--select', 'model_name'])
            check: Whether to raise exception on non-zero exit code
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds
            
        Returns:
            CompletedProcess instance with command results
        """
        # Build full command
        full_command = [self.dbt_path] + command
        
        # Add project and profiles directory flags if not already present
        if '--project-dir' not in command:
            full_command.extend(['--project-dir', str(self.project_dir)])
        if '--profiles-dir' not in command:
            full_command.extend(['--profiles-dir', str(self.profiles_dir)])
            
        # Prepare environment
        env = self._prepare_environment()
        
        # Debug output
        print(f"Running command: {' '.join(full_command)}")
        print(f"Working directory: {self.project_dir}")
        print(f"Profiles directory: {self.profiles_dir}")
        
        try:
            # Run the command
            result = subprocess.run(
                full_command,
                cwd=str(self.project_dir),  # Set working directory
                env=env,  # Use prepared environment
                check=check,
                capture_output=capture_output,
                text=True,  # Return stdout/stderr as strings
                timeout=timeout
            )
            
            if capture_output:
                print("STDOUT:", result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                    
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            if capture_output:
                print(f"STDOUT: {e.stdout}")
                print(f"STDERR: {e.stderr}")
            raise
        except subprocess.TimeoutExpired as e:
            print(f"Command timed out after {timeout} seconds")
            raise
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            raise
    
    def debug(self) -> Dict[str, Any]:
        """Run dbt debug command and return parsed results."""
        result = self.run_command(['debug'], check=False)
        
        debug_info = {
            'exit_code': result.returncode,
            'dbt_path': self.dbt_path,
            'project_dir': str(self.project_dir),
            'profiles_dir': str(self.profiles_dir),
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        return debug_info
    
    def run(self, select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
        """Run dbt run command."""
        command = ['run']
        if select:
            command.extend(['--select', select])
        return self.run_command(command, **kwargs)
    
    def test(self, select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
        """Run dbt test command."""
        command = ['test']
        if select:
            command.extend(['--select', select])
        return self.run_command(command, **kwargs)
    
    def build(self, select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
        """Run dbt build command."""
        command = ['build']
        if select:
            command.extend(['--select', select])
        return self.run_command(command, **kwargs)
    
    def clean(self, **kwargs) -> subprocess.CompletedProcess:
        """Run dbt clean command."""
        return self.run_command(['clean'], **kwargs)
    
    def deps(self, **kwargs) -> subprocess.CompletedProcess:
        """Run dbt deps command."""
        return self.run_command(['deps'], **kwargs)


def main():
    """Example usage of DbtRunner."""
    try:
        # Initialize runner with explicit paths
        runner = DbtRunner(
            project_dir="/Users/mattstrautmann/Documents/GitHub/sbdk-dev/my_project/dbt",
            profiles_dir=None  # Will use ~/.dbt
        )
        
        # Run debug first to check configuration
        print("=== Running dbt debug ===")
        debug_info = runner.debug()
        print(f"Debug exit code: {debug_info['exit_code']}")
        
        # Run dbt commands
        print("\n=== Running dbt run ===")
        result = runner.run()
        print(f"Run exit code: {result.returncode}")
        
        print("\n=== Running dbt test ===")
        result = runner.test()
        print(f"Test exit code: {result.returncode}")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())