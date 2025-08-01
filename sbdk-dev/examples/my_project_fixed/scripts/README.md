# DBT CLI Execution Scripts

This directory contains Python scripts that provide robust solutions for executing dbt commands from Python code, addressing common subprocess execution issues.

## Problem Solved

When executing dbt commands via Python's `subprocess` module, common issues include:
- Path expansion problems with `~` (home directory)
- Missing environment variables
- Incorrect working directories  
- Virtual environment path resolution
- Profile directory configuration

## Files

### `dbt_utils.py`
**Main utility module** - Import this in your Python scripts for robust dbt execution.

Key functions:
- `run_dbt(dbt_args, ...)` - Execute any dbt command with proper setup
- `dbt_run(select=None, ...)` - Run dbt run command
- `dbt_test(select=None, ...)` - Run dbt test command
- `dbt_debug()` - Run dbt debug command
- `dbt_build()`, `dbt_clean()`, `dbt_deps()` - Other common commands

### `dbt_runner.py`
**Class-based runner** - Object-oriented approach for dbt execution.

Usage:
```python
runner = DbtRunner(project_dir="path/to/dbt")
result = runner.run()
debug_info = runner.debug()
```

### `run_dbt.py`
**Simple CLI wrapper** - Standalone script for quick dbt execution.

Usage:
```bash
python run_dbt.py debug
python run_dbt.py run --select my_model
```

### `example_dbt_usage.py`
**Complete examples** - Shows all usage patterns and error handling.

## Key Features

### Automatic Path Resolution
- Finds dbt executable in virtual environment or system PATH
- Expands `~` to full home directory path
- Resolves relative paths to absolute paths

### Environment Setup
- Properly sets `HOME` environment variable
- Configures `DBT_PROFILES_DIR` with path expansion
- Preserves virtual environment variables

### Error Handling
- Captures and displays stdout/stderr
- Provides clear error messages
- Supports timeout handling
- Optional exception raising

### Flexibility
- Works with any dbt command
- Customizable project and profiles directories
- Debug mode for troubleshooting
- Both functional and object-oriented APIs

## Usage Examples

### Basic Usage (Recommended)
```python
from scripts.dbt_utils import dbt_run, dbt_test, dbt_debug

# Run dbt debug
result = dbt_debug(project_dir="./dbt")

# Run specific model
result = dbt_run(select="my_model", project_dir="./dbt")

# Run all tests
result = dbt_test(project_dir="./dbt")
```

### Advanced Usage
```python
from scripts.dbt_utils import run_dbt

# Custom command with extra environment variables
result = run_dbt(
    ['run', '--select', 'tag:daily'],
    project_dir="./dbt",
    extra_env={"DBT_PROFILES_DIR": "/custom/profiles"},
    timeout=300,
    debug=True
)
```

### Object-Oriented Approach  
```python
from scripts.dbt_runner import DbtRunner

runner = DbtRunner(project_dir="./dbt")

# Get diagnostic information
debug_info = runner.debug()
print(f"dbt version info: {debug_info['stdout']}")

# Run commands
runner.deps()  # Install dependencies
runner.run()   # Run models
runner.test()  # Run tests
```

### Error Handling
```python
from scripts.dbt_utils import dbt_run
import subprocess

try:
    result = dbt_run(select="my_model", check=False)
    if result.returncode != 0:
        print(f"dbt failed: {result.stderr}")
except subprocess.TimeoutExpired:
    print("dbt command timed out")
except FileNotFoundError:
    print("dbt executable not found - install with: pip install dbt-duckdb")
```

## Testing the Fix

Run the example script to verify everything works:

```bash
cd /Users/mattstrautmann/Documents/GitHub/sbdk-dev/my_project
python scripts/example_dbt_usage.py
```

This will test:
1. Finding the dbt executable
2. Running dbt debug
3. Running dbt commands with different parameters
4. Error handling scenarios

## Common Issues Fixed

1. **FileNotFoundError**: Script finds dbt in virtual environment or PATH
2. **Path expansion**: `~` is properly expanded to full home directory
3. **Working directory**: Commands run from correct dbt project directory
4. **Environment variables**: Proper setup of HOME, DBT_PROFILES_DIR, etc.
5. **Profile directory**: Handles custom profiles directory configuration
6. **Virtual environment**: Works correctly within activated venv

## Integration

To use these utilities in your existing Python scripts:

```python
import sys
from pathlib import Path

# Add scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from dbt_utils import dbt_run, dbt_test

# Now use the utilities
dbt_run(project_dir="./dbt")
```

## Requirements

- Python 3.7+
- dbt-core and appropriate adapter (e.g., dbt-duckdb)
- Valid dbt project with `dbt_project.yml`
- Configured dbt profiles in `~/.dbt/profiles.yml`

## Troubleshooting

If you encounter issues:

1. Run `python scripts/dbt_utils.py` to test basic functionality
2. Check that dbt works from command line: `dbt debug`
3. Verify virtual environment is activated if using one
4. Ensure `~/.dbt/profiles.yml` is properly configured
5. Use `debug=True` parameter to see detailed execution information