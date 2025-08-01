"""
Utility functions for executing dbt commands from Python scripts.
Handles common issues with subprocess execution, path expansion, and environment setup.
"""
import os
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import shutil


def find_dbt_executable() -> str:
    """
    Find the dbt executable, preferring virtual environment over system installation.
    
    Returns:
        Path to dbt executable
        
    Raises:
        RuntimeError: If dbt executable cannot be found
    """
    # Check virtual environment first
    if hasattr(sys, 'prefix'):
        venv_dbt = Path(sys.prefix) / 'bin' / 'dbt'
        if venv_dbt.exists():
            return str(venv_dbt)
    
    # Fall back to system dbt
    system_dbt = shutil.which('dbt')
    if system_dbt:
        return system_dbt
    
    raise RuntimeError(
        "dbt executable not found. Install with: pip install dbt-duckdb"
    )


def prepare_dbt_env(extra_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Prepare environment variables for dbt execution.
    
    Args:
        extra_env: Additional environment variables to include
        
    Returns:
        Dictionary of environment variables
    """
    env = os.environ.copy()
    
    # Ensure HOME is set for proper ~ expansion
    if 'HOME' not in env:
        env['HOME'] = str(Path.home())
    
    # Handle DBT_PROFILES_DIR with proper path expansion
    profiles_dir = env.get('DBT_PROFILES_DIR', '~/.dbt')
    expanded_profiles_dir = str(Path(profiles_dir).expanduser().resolve())
    env['DBT_PROFILES_DIR'] = expanded_profiles_dir
    
    # Add virtual environment to PATH if active
    if hasattr(sys, 'prefix'):
        env['VIRTUAL_ENV'] = sys.prefix
        bin_dir = str(Path(sys.prefix) / 'bin')
        if 'PATH' in env:
            env['PATH'] = f"{bin_dir}:{env['PATH']}"
        else:
            env['PATH'] = bin_dir
    
    # Add any extra environment variables
    if extra_env:
        env.update(extra_env)
    
    return env


def build_dbt_command(
    dbt_args: List[str],
    project_dir: Optional[Union[str, Path]] = None,
    profiles_dir: Optional[Union[str, Path]] = None,
    dbt_executable: Optional[str] = None
) -> Tuple[List[str], Path]:
    """
    Build a complete dbt command with proper paths.
    
    Args:
        dbt_args: List of dbt arguments (e.g., ['run', '--select', 'model'])
        project_dir: Path to dbt project directory
        profiles_dir: Path to dbt profiles directory
        dbt_executable: Path to dbt executable (auto-detected if not provided)
        
    Returns:
        Tuple of (command list, working directory path)
    """
    # Find dbt executable
    if not dbt_executable:
        dbt_executable = find_dbt_executable()
    
    # Determine project directory
    if project_dir:
        project_path = Path(project_dir).resolve()
    else:
        # Try to find dbt directory relative to script
        script_dir = Path(__file__).parent
        potential_paths = [
            script_dir.parent / 'dbt',
            script_dir.parent.parent / 'dbt',
            Path.cwd() / 'dbt',
            Path.cwd()
        ]
        
        project_path = None
        for path in potential_paths:
            if path.exists() and (path / 'dbt_project.yml').exists():
                project_path = path
                break
        
        if not project_path:
            project_path = Path.cwd()
    
    # Build command
    cmd = [dbt_executable] + dbt_args
    
    # Add project directory if not specified
    if '--project-dir' not in dbt_args:
        cmd.extend(['--project-dir', str(project_path)])
    
    # Add profiles directory if not specified and provided
    if profiles_dir and '--profiles-dir' not in dbt_args:
        profiles_path = Path(profiles_dir).expanduser().resolve()
        cmd.extend(['--profiles-dir', str(profiles_path)])
    
    return cmd, project_path


def run_dbt(
    dbt_args: List[str],
    project_dir: Optional[Union[str, Path]] = None,
    profiles_dir: Optional[Union[str, Path]] = None,
    extra_env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    check: bool = True,
    timeout: Optional[int] = None,
    debug: bool = True
) -> subprocess.CompletedProcess:
    """
    Execute a dbt command with robust error handling.
    
    Args:
        dbt_args: List of dbt arguments (e.g., ['run', '--select', 'model'])
        project_dir: Path to dbt project directory
        profiles_dir: Path to dbt profiles directory  
        extra_env: Additional environment variables
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        timeout: Command timeout in seconds
        debug: Whether to print debug information
        
    Returns:
        subprocess.CompletedProcess object
        
    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        subprocess.TimeoutExpired: If command times out
    """
    # Build command and get working directory
    cmd, work_dir = build_dbt_command(dbt_args, project_dir, profiles_dir)
    
    # Prepare environment
    env = prepare_dbt_env(extra_env)
    
    if debug:
        print(f"Command: {' '.join(cmd)}")
        print(f"Working directory: {work_dir}")
        print(f"DBT_PROFILES_DIR: {env.get('DBT_PROFILES_DIR')}")
    
    try:
        # Execute command
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            env=env,
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout
        )
        
        if debug and capture_output:
            if result.stdout:
                print("=== STDOUT ===")
                print(result.stdout)
            if result.stderr:
                print("=== STDERR ===")
                print(result.stderr)
        
        return result
        
    except subprocess.CalledProcessError as e:
        if debug:
            print(f"Command failed with exit code: {e.returncode}")
            if capture_output:
                print("=== STDOUT ===")
                print(e.stdout or "(empty)")
                print("=== STDERR ===")
                print(e.stderr or "(empty)")
        raise
    except subprocess.TimeoutExpired as e:
        if debug:
            print(f"Command timed out after {timeout} seconds")
        raise


# Convenience functions for common dbt commands
def dbt_debug(**kwargs) -> subprocess.CompletedProcess:
    """Run dbt debug command."""
    return run_dbt(['debug'], **kwargs)


def dbt_run(select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
    """Run dbt run command."""
    args = ['run']
    if select:
        args.extend(['--select', select])
    return run_dbt(args, **kwargs)


def dbt_test(select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
    """Run dbt test command."""
    args = ['test']
    if select:
        args.extend(['--select', select])
    return run_dbt(args, **kwargs)


def dbt_build(select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
    """Run dbt build command."""
    args = ['build']
    if select:
        args.extend(['--select', select])
    return run_dbt(args, **kwargs)


def dbt_clean(**kwargs) -> subprocess.CompletedProcess:
    """Run dbt clean command."""
    return run_dbt(['clean'], **kwargs)


def dbt_deps(**kwargs) -> subprocess.CompletedProcess:
    """Run dbt deps command."""
    return run_dbt(['deps'], **kwargs)


def dbt_compile(select: Optional[str] = None, **kwargs) -> subprocess.CompletedProcess:
    """Run dbt compile command."""
    args = ['compile']
    if select:
        args.extend(['--select', select])
    return run_dbt(args, **kwargs)


# Example usage
if __name__ == "__main__":
    print("Testing dbt utilities...")
    
    try:
        # Test finding dbt
        dbt_path = find_dbt_executable()
        print(f"Found dbt at: {dbt_path}")
        
        # Test debug command
        print("\n=== Running dbt debug ===")
        result = dbt_debug(
            project_dir="/Users/mattstrautmann/Documents/GitHub/sbdk-dev/my_project/dbt"
        )
        print(f"Exit code: {result.returncode}")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")