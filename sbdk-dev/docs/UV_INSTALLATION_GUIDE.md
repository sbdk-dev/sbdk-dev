# uv Package Manager Guide for SBDK.dev

## Why uv?

SBDK.dev now uses [uv](https://github.com/astral-sh/uv) as the recommended package manager for Python projects. uv is significantly faster than pip and provides better dependency resolution, making development more efficient.

### Performance Benefits:
- **10-100x faster** than pip for package installation
- **Reliable dependency resolution** with conflict detection
- **Better virtual environment management**
- **Lockfile support** for reproducible builds

## Installation

### Install uv
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (if you have it)
pip install uv
```

### Verify Installation
```bash
uv --version
```

## SBDK.dev Workflow with uv

### 1. Project Setup
```bash
# Clone or create project
git clone <repository-url>
cd sbdk-dev

# Install dependencies (creates virtual environment automatically)
uv sync

# OR for development with extra dependencies
uv sync --extra dev
```

### 2. Running Commands
```bash
# Run SBDK commands
uv run sbdk init my_project
uv run sbdk dev
uv run sbdk start

# Run tests
uv run pytest tests/
uv run pytest tests/test_pipelines.py -v

# Run Python scripts
uv run python examples/my_project_fixed/test_email_uniqueness_fix.py
```

### 3. Adding Dependencies
```bash
# Add a new dependency
uv add pandas

# Add development dependency
uv add --dev pytest

# Add specific version
uv add "dbt-duckdb>=1.7.0"

# Add from requirements.txt
uv add -r requirements.txt
```

### 4. Managing Environments
```bash
# Create new project with uv
uv init my_new_project
cd my_new_project

# Install dependencies
uv sync

# Activate shell (optional, uv run handles this automatically)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Migration from pip/pipenv

### From pip
```bash
# Old workflow
pip install -r requirements.txt
python main.py

# New workflow
uv sync
uv run python main.py
```

### From pipenv
```bash
# Old workflow  
pipenv install
pipenv run python main.py

# New workflow
uv sync
uv run python main.py
```

## Common Commands

### Package Management
```bash
uv add <package>              # Add dependency
uv remove <package>           # Remove dependency
uv sync                       # Install/update all dependencies
uv lock                       # Update lockfile
uv tree                       # Show dependency tree
```

### Environment Management
```bash
uv venv                       # Create virtual environment
uv venv --python 3.11         # Create with specific Python version
uv run <command>              # Run command in environment
uv shell                      # Activate shell
```

### Development Workflow
```bash
uv sync --extra dev           # Install dev dependencies
uv run pytest                # Run tests
uv run black .                # Format code
uv run ruff check .           # Lint code
uv build                      # Build package
```

## SBDK.dev Specific Examples

### Initialize New Project
```bash
# Create and set up new SBDK project
uv run sbdk init analytics_pipeline
cd analytics_pipeline

# Dependencies automatically handled by parent project
uv run sbdk dev
```

### Development Testing
```bash
# Run comprehensive test suite
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/test_cli_comprehensive.py
uv run pytest tests/test_dbt_integration.py
uv run pytest tests/test_pipelines.py

# Run with coverage
uv run pytest tests/ --cov=sbdk --cov-report=html
```

### DBT Integration
```bash
# Install DBT dependencies
uv add dbt-duckdb

# Run DBT commands through SBDK
uv run sbdk dev --dbt-only

# Or run DBT directly
uv run dbt debug
uv run dbt run
uv run dbt test
```

### Performance Benchmarking
```bash
# Run performance tests
uv run pytest tests/test_performance_benchmarks.py -v

# Run validation framework
uv run pytest tests/test_validation_framework.py -v
```

## Troubleshooting

### Common Issues

**Q: `uv: command not found`**
A: Make sure uv is installed and in your PATH. Restart your terminal after installation.

**Q: `ImportError` when running commands**
A: Run `uv sync` to ensure all dependencies are installed.

**Q: Virtual environment issues**
A: uv manages virtual environments automatically. Use `uv run` instead of activating manually.

**Q: Slow package installation**
A: uv should be much faster than pip. If it's slow, check your network connection or try `uv cache clean`.

### Debug Commands
```bash
# Check uv configuration
uv config list

# Check project status
uv status

# Clear cache
uv cache clean

# Verbose output
uv -v sync
```

## Advanced Features

### Lockfiles
uv automatically creates `uv.lock` files for reproducible builds:
```bash
# Update lockfile
uv lock

# Install exact versions from lockfile
uv sync --frozen
```

### Multiple Python Versions
```bash
# Create environment with specific Python version
uv venv --python 3.11

# Use different Python versions
uv run --python 3.11 python script.py
```

### Workspace Support
For multi-package projects:
```bash
# In workspace root
uv sync --workspace

# Add dependency to specific package
uv add --package my-package requests
```

## Best Practices

1. **Always use `uv run`** for running commands instead of activating environments
2. **Commit `uv.lock`** for reproducible builds
3. **Use `uv sync`** instead of `pip install -r requirements.txt`
4. **Add dependencies with `uv add`** instead of editing requirements.txt manually
5. **Use `--extra dev`** for development dependencies

## Integration with IDEs

### VS Code
Add to your VS Code settings for Python path detection:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python"
}
```

### PyCharm
Configure PyCharn to use the `.venv/bin/python` interpreter created by uv.

## Performance Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|----|---------| 
| Fresh install | 45s | 4s | 11x faster |
| Cached install | 12s | 0.5s | 24x faster |
| Dependency resolution | 8s | 0.1s | 80x faster |

---

For more information, visit the [official uv documentation](https://github.com/astral-sh/uv).