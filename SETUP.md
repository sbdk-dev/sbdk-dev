# SBDK Development Setup

This guide is for developers contributing to SBDK.dev. For user installation, see [README.md](README.md).

## Development Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sbdk-dev/sbdk-dev.git
   cd sbdk-dev
   ```

2. **Install with development dependencies:**
   ```bash
   # Using uv (recommended - 11x faster)
   uv sync --extra dev

   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Verify CLI installation:**
   ```bash
   uv run sbdk --help
   # Or if installed with pip: sbdk --help
   ```

## Running Tests

### Run Full Test Suite
```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=sbdk --cov-report=html

# Specific test file
uv run pytest tests/test_phase1_exceptions.py -v
```

### Run Phase 1 Tests (Architecture)
```bash
uv run pytest tests/test_phase1_*.py -v
```

### Run End-to-End Tests
```bash
# Create test project and run pipeline
uv run sbdk init test_project
cd test_project
uv run sbdk run
```

## Development Workflow

### 1. Make Changes
Edit files in the `sbdk/` package:
- `sbdk/cli/` - CLI commands
- `sbdk/core/` - Core functionality
- `sbdk/exceptions.py` - Error handling
- `sbdk/context.py` - Context management
- `sbdk/validators.py` - Pydantic schemas
- `sbdk/formatters.py` - Output formatting

### 2. Run Tests
```bash
# Run relevant tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=sbdk
```

### 3. Code Quality
```bash
# Format code
uv run black sbdk/ tests/

# Lint code
uv run ruff check sbdk/ tests/

# Type checking
uv run mypy sbdk/
```

### 4. Test CLI Manually
```bash
# Test version command
uv run sbdk version --verbose

# Test with different formats
uv run sbdk version --format json
uv run sbdk version --format minimal

# Test init command
uv run sbdk init test_project --help
```

## Building the Package

### Build Distribution
```bash
# Install build tools
uv pip install build

# Build wheel and sdist
python -m build

# Output in dist/
ls -lh dist/
```

### Install Local Build
```bash
# Install from wheel
pip install dist/sbdk_dev-1.1.0-py3-none-any.whl

# Or install in development mode
pip install -e .
```

## Project Structure

```
sbdk-dev/
├── sbdk/                  # Main package
│   ├── cli/              # CLI commands
│   │   ├── main.py       # Entry point with global options
│   │   ├── base.py       # Base command classes
│   │   └── commands/     # Command implementations
│   ├── core/             # Core functionality
│   ├── exceptions.py     # Exception hierarchy
│   ├── context.py        # Context management
│   ├── validators.py     # Pydantic schemas
│   └── formatters.py     # Output formatting
├── tests/                # Test suite
│   ├── test_phase1_*.py  # Phase 1 architecture tests
│   └── test_*.py         # Other tests
├── docs/                 # Documentation
├── examples/             # Example projects
├── pyproject.toml        # Package configuration
└── README.md             # User documentation
```

## Contributing Guidelines

1. **Branch Naming:**
   - Feature: `feature/description`
   - Fix: `fix/description`
   - Release: `release-x.y.z`

2. **Commit Messages:**
   - Follow conventional commits
   - Include issue numbers if applicable

3. **Testing:**
   - Add tests for new features
   - Ensure all tests pass
   - Maintain 100% coverage for new code

4. **Documentation:**
   - Update README.md for user-facing changes
   - Update CHANGELOG.md
   - Add docstrings to new functions/classes

## Security Scanning

```bash
# Install safety
uv pip install safety

# Run security scan
uv run safety check

# Expected: 0 vulnerabilities
```

## Release Process

See [GITHUB_RELEASE_WORKFLOW.md](docs/GITHUB_RELEASE_WORKFLOW.md) for detailed release instructions.

```bash
# 1. Update version in pyproject.toml and sbdk/__init__.py
# 2. Update CHANGELOG.md
# 3. Run tests
uv run pytest tests/ -v

# 4. Build and publish (maintainers only)
python -m build
twine upload dist/*
```

## Getting Help

- **Issues:** https://github.com/sbdk-dev/sbdk-dev/issues
- **Discussions:** https://github.com/sbdk-dev/sbdk-dev/discussions
- **Docs:** https://docs.sbdk.dev (coming soon)
