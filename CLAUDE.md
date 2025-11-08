# CLAUDE.md - Guide for AI-Assisted SBDK Development

**Version**: 1.0
**Last Updated**: January 2025
**Purpose**: Context and guidelines for Claude AI when working on SBDK platform development

---

## 🎯 Project Overview

**SBDK (Sandbox Development Kit)** is a local-first data development sandbox that enables rapid iteration, safe experimentation, and modern data pipeline development practices.

### Core Identity

**SBDK is NOT**:
- ❌ An all-in-one AI analytics platform
- ❌ A production data warehouse
- ❌ A BI/visualization tool
- ❌ A cloud service

**SBDK IS**:
- ✅ The foundational local-first data development sandbox
- ✅ A rapid iteration platform for data pipelines
- ✅ The best place to build, test, and iterate before production
- ✅ A foundation that other tools build upon

### Mission Statement

> **"SBDK provides the fastest, safest, and most cost-effective way to develop data pipelines locally, enabling data professionals to iterate rapidly and build with confidence."**

---

## 📚 Essential Reading

Before working on SBDK, Claude should familiarize with these documents:

### 1. Platform Vision (REQUIRED)
- **File**: [SBDK_PLATFORM_VISION.md](./SBDK_PLATFORM_VISION.md)
- **Purpose**: Comprehensive platform strategy and roadmap
- **Key Sections**:
  - Section 2: SBDK's Core Mission (principles and boundaries)
  - Section 4: Platform Architecture (technical design)
  - Section 7: Roadmap (implementation phases)

### 2. Swarm Builder (FOR COMPLEX TASKS)
- **File**: [CLAUDE_SWARM_BUILDER.md](./CLAUDE_SWARM_BUILDER.md)
- **Purpose**: Multi-agent orchestration for accelerated development
- **When to Use**: Complex features requiring multiple specialized agents

### 3. Current Codebase
- **Location**: `src/sbdk/`
- **Tests**: `tests/`
- **Configuration**: `pyproject.toml`, `sbdk_config.json`

---

## 🏗️ Architecture Principles

### 1. Local-First Development
```python
# ✅ GOOD - Local execution, no cloud dependencies
def load_data_from_local_source():
    return duckdb.sql("SELECT * FROM local_file.csv")

# ❌ BAD - Cloud dependency for core features
def load_data_from_cloud():
    return bigquery_client.query("SELECT ...")  # Only for optional deployment
```

### 2. Rapid Iteration (30-Second Cycle)
```python
# ✅ GOOD - Instant feedback
@click.command()
def run_pipeline():
    """Execute pipeline with instant feedback"""
    with Progress() as progress:
        task = progress.add_task("Running...", total=3)
        # Fast execution, immediate results
        progress.advance(task)

# ❌ BAD - Slow feedback loops
def run_with_slow_setup():
    initialize_heavy_dependencies()  # 30+ seconds
    setup_complex_environment()      # Slow
```

### 3. Production Parity
```python
# ✅ GOOD - Local mirrors production patterns
# DuckDB locally → BigQuery in production
# dbt locally → dbt Cloud in production

# ❌ BAD - Different patterns locally vs production
# Custom SQL locally → dbt in production (patterns don't match)
```

### 4. Developer Experience First
```python
# ✅ GOOD - Clear, helpful errors
class ValidationError(SBDKError):
    """Clear error with actionable suggestion"""
    def __init__(self, message: str, suggestion: str):
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"{message}\n💡 Suggestion: {suggestion}")

# ❌ BAD - Cryptic errors
raise Exception("Error")  # No context, no help
```

### 5. Foundation, Not Platform
```python
# ✅ GOOD - Clean API for integration
@mcp_tool
def execute_query(sql: str) -> dict:
    """Execute SQL - other tools can use this"""
    return sbdk.query(sql)

# ❌ BAD - Monolithic, hard to integrate
class AllInOneAnalyticsPlatform:
    # Tries to do everything, hard to use as foundation
```

---

## 🎨 Code Style & Standards

### Python Style
- **Python Version**: 3.9+ (target 3.11+)
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public APIs
- **Formatting**: `black` (line length 88)
- **Linting**: `ruff` (strict mode)
- **Import Order**: `isort` (configured in pyproject.toml)

### Example: Perfect Function
```python
from pathlib import Path
from typing import Optional

def create_environment(
    name: str,
    template: Optional[str] = None,
    target: str = "duckdb"
) -> Path:
    """Create a new SBDK environment.

    Args:
        name: Environment name (e.g., 'dev', 'staging')
        template: Template to use (e.g., 'analytics', 'ml')
        target: Target database (default: 'duckdb')

    Returns:
        Path to the created environment directory

    Raises:
        ValidationError: If name is invalid or environment exists
        PipelineError: If environment creation fails

    Example:
        >>> env_path = create_environment("dev", template="analytics")
        >>> print(env_path)
        /home/user/.sbdk/environments/dev
    """
    # Validate inputs
    if not name or not name.replace("-", "").replace("_", "").isalnum():
        raise ValidationError(
            f"Invalid environment name: {name}",
            "Use alphanumeric characters, hyphens, and underscores only"
        )

    # Create environment
    env_path = Path.home() / ".sbdk" / "environments" / name
    if env_path.exists():
        raise ValidationError(
            f"Environment '{name}' already exists",
            f"Use a different name or delete existing: {env_path}"
        )

    env_path.mkdir(parents=True, exist_ok=True)
    return env_path
```

### Testing Requirements
```python
# Every function needs comprehensive tests
import pytest
from sbdk.environment import create_environment
from sbdk.exceptions import ValidationError

def test_create_environment_success(tmp_path, monkeypatch):
    """Test successful environment creation"""
    monkeypatch.setenv("HOME", str(tmp_path))
    env_path = create_environment("dev", template="analytics")
    assert env_path.exists()
    assert env_path.name == "dev"

def test_create_environment_invalid_name():
    """Test environment creation with invalid name"""
    with pytest.raises(ValidationError) as exc_info:
        create_environment("dev@123")
    assert "Invalid environment name" in str(exc_info.value)
    assert "alphanumeric" in str(exc_info.value)

def test_create_environment_already_exists(tmp_path, monkeypatch):
    """Test environment creation when name already exists"""
    monkeypatch.setenv("HOME", str(tmp_path))
    create_environment("dev")
    with pytest.raises(ValidationError) as exc_info:
        create_environment("dev")
    assert "already exists" in str(exc_info.value)
```

---

## 🛠️ Development Workflow

### 1. Understanding the Task
```markdown
Before coding, always:
1. Check if task aligns with Platform Vision (Section 2.3)
2. Identify which roadmap phase it belongs to (Section 7)
3. Understand integration points (Section 6)
4. Review existing code patterns in src/sbdk/
```

### 2. Implementation Checklist
```markdown
For every feature:
- [ ] Follows local-first principle
- [ ] Achieves <30s iteration cycle
- [ ] Includes comprehensive type hints
- [ ] Has Google-style docstrings
- [ ] Includes unit tests (95%+ coverage target)
- [ ] Includes integration tests
- [ ] Has error handling with helpful messages
- [ ] Includes CLI integration (if user-facing)
- [ ] Has documentation and examples
- [ ] Backward compatible (or migration guide)
```

### 3. Quality Gates
```bash
# Before committing, ensure all pass:
pytest tests/ --cov=sbdk --cov-report=term-missing --cov-fail-under=95
mypy src/sbdk --strict
ruff check src/sbdk tests/
black --check src/sbdk tests/
```

### 4. Git Workflow
```bash
# Work on feature branch
git checkout -b claude/feature-name-[session-id]

# Commit with conventional commits
git commit -m "feat: add environment switching"
git commit -m "fix: handle missing config file"
git commit -m "docs: update environment management guide"

# Push to remote
git push -u origin claude/feature-name-[session-id]
```

---

## 🧩 Common Development Patterns

### Pattern 1: CLI Command
```python
# src/sbdk/cli/env.py
import typer
from rich.console import Console
from sbdk.environment import EnvironmentManager
from sbdk.exceptions import ValidationError

app = typer.Typer(help="Environment management commands")
console = Console()

@app.command()
def create(
    name: str = typer.Argument(..., help="Environment name"),
    template: str = typer.Option(None, "--template", "-t", help="Template to use"),
    target: str = typer.Option("duckdb", "--target", help="Target database"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
) -> None:
    """Create a new SBDK environment.

    Example:
        sbdk env create dev --template analytics
    """
    try:
        manager = EnvironmentManager()
        env_path = manager.create(name, template=template, target=target)

        console.print(f"✅ Environment '{name}' created at {env_path}", style="green")
        if verbose:
            console.print(f"Template: {template or 'default'}", style="dim")
            console.print(f"Target: {target}", style="dim")

    except ValidationError as e:
        console.print(f"❌ {e}", style="red")
        raise typer.Exit(4)
```

### Pattern 2: Configuration Management
```python
# src/sbdk/config.py
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, validator

class EnvironmentConfig(BaseModel):
    """Environment configuration with validation"""

    name: str = Field(..., description="Environment name")
    target: str = Field("duckdb", description="Target database")
    template: Optional[str] = Field(None, description="Template used")

    @validator("name")
    def validate_name(cls, v):
        """Validate environment name"""
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Name must contain only alphanumeric, hyphens, underscores")
        return v

    @validator("target")
    def validate_target(cls, v):
        """Validate target database"""
        valid_targets = ["duckdb", "postgres", "bigquery"]
        if v not in valid_targets:
            raise ValueError(f"Target must be one of: {', '.join(valid_targets)}")
        return v

    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"  # Reject unknown fields
```

### Pattern 3: Error Handling
```python
# src/sbdk/exceptions.py
class SBDKError(Exception):
    """Base exception for SBDK"""
    exit_code = 1

class ValidationError(SBDKError):
    """Validation error with helpful suggestions"""
    exit_code = 4

    def __init__(self, message: str, suggestion: str):
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"{message}\n💡 Suggestion: {suggestion}")

class PipelineError(SBDKError):
    """Pipeline execution error"""
    exit_code = 3

# Usage
try:
    validate_environment(name)
except ValidationError as e:
    console.print(f"❌ {e.message}", style="red")
    console.print(f"💡 {e.suggestion}", style="yellow")
    raise typer.Exit(e.exit_code)
```

### Pattern 4: Testing
```python
# tests/test_environment.py
import pytest
from pathlib import Path
from sbdk.environment import EnvironmentManager
from sbdk.exceptions import ValidationError

class TestEnvironmentManager:
    """Test suite for EnvironmentManager"""

    @pytest.fixture
    def manager(self, tmp_path, monkeypatch):
        """Create manager with temp directory"""
        monkeypatch.setenv("HOME", str(tmp_path))
        return EnvironmentManager()

    def test_create_environment_success(self, manager):
        """Test successful environment creation"""
        env_path = manager.create("dev", template="analytics")
        assert env_path.exists()
        assert (env_path / "config.json").exists()

    def test_create_environment_invalid_name(self, manager):
        """Test creation with invalid name"""
        with pytest.raises(ValidationError) as exc:
            manager.create("dev@123")
        assert "Invalid" in str(exc.value)

    @pytest.mark.parametrize("name,valid", [
        ("dev", True),
        ("staging-env", True),
        ("prod_2", True),
        ("test@env", False),
        ("", False),
    ])
    def test_name_validation(self, manager, name, valid):
        """Test name validation with various inputs"""
        if valid:
            env_path = manager.create(name)
            assert env_path.exists()
        else:
            with pytest.raises(ValidationError):
                manager.create(name)
```

---

## 🚀 Using the Swarm Builder

### When to Use Swarms

**Use swarms for**:
- ✅ Complex multi-component features (e.g., environment management system)
- ✅ New subsystems (e.g., MCP server, quality framework)
- ✅ Major refactoring across multiple files
- ✅ Performance optimization requiring analysis + implementation

**Don't use swarms for**:
- ❌ Simple bug fixes
- ❌ Single-function additions
- ❌ Documentation updates
- ❌ Minor CLI improvements

### Swarm Launch Template

```bash
/swarm "Implement [FEATURE] for SBDK:

REFERENCE: SBDK_PLATFORM_VISION.md Section [X.Y]
ALIGNMENT: [Local-first / Rapid Iteration / Production Parity]

AGENTS:
1. Architect: Design system architecture and APIs
2. Implementation: Implement core functionality
3. Testing: TDD with 95%+ coverage
4. CLI: Add CLI commands with rich output
5. Documentation: User guide and examples

REQUIREMENTS:
- Follow SBDK code style (see CLAUDE.md)
- Type hints required
- Google-style docstrings
- Comprehensive error handling
- Integration tests included
- Backward compatible

DELIVERABLES:
- [List specific files and features]

QUALITY GATES:
- pytest tests/ --cov-fail-under=95
- mypy src/sbdk --strict
- ruff check passes
- Manual testing with example use cases
"
```

---

## 📋 Quick Reference

### Project Structure
```
sbdk-dev/
├── src/sbdk/              # Main package
│   ├── cli/              # CLI commands
│   ├── core/             # Core functionality
│   ├── environment/      # Environment management
│   ├── pipeline/         # Pipeline engine
│   ├── sources/          # Data source connectors
│   ├── quality/          # Quality framework
│   ├── testing/          # Testing framework
│   ├── mcp/              # MCP server
│   └── utils/            # Utilities
├── tests/                # Test suite
├── docs/                 # Documentation
├── templates/            # Project templates
└── examples/             # Example projects
```

### Key Files
- `pyproject.toml` - Project configuration
- `src/sbdk/__init__.py` - Package initialization
- `src/sbdk/cli/main.py` - CLI entry point
- `src/sbdk/config.py` - Configuration models
- `src/sbdk/exceptions.py` - Exception hierarchy

### Common Tasks
```bash
# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=sbdk --cov-report=html

# Type checking
mypy src/sbdk

# Linting
ruff check src/sbdk tests/

# Format code
black src/sbdk tests/

# Run SBDK
uv run sbdk --help
```

---

## 🎯 Decision Making Guide

### Should This Feature Be in SBDK?

Ask these questions:

1. **Is it core to local data pipeline development?**
   - ✅ Yes → Implement in SBDK
   - ❌ No → Consider as integration/plugin

2. **Does it require cloud dependencies?**
   - ✅ Required → Not core SBDK (maybe optional)
   - ❌ Optional → Can be core feature

3. **Can specialized tools do it better?**
   - ✅ Yes → Provide integration, not implementation
   - ❌ No → Implement in SBDK

4. **Does it align with the 30-second iteration goal?**
   - ✅ Yes → Good fit for SBDK
   - ❌ No → Reconsider or optimize

### Examples

**Environment Management**:
- ✅ Core to development workflow
- ✅ No cloud dependencies
- ✅ Not better done by others
- ✅ Enables fast iteration
- **Decision: Implement in SBDK**

**Data Visualization**:
- ❌ Not core to pipeline development
- ⚠️ Observable/Tableau do it better
- **Decision: Provide data export, let viz tools handle display**

**AI Data Analysis**:
- ❌ Not core to pipeline development
- ✅ knowDB does it better
- **Decision: Provide MCP server for integration**

---

## 🔍 Debugging SBDK

### Common Issues

**Issue**: Pipeline fails with cryptic error
```python
# Bad
raise Exception("Pipeline failed")

# Good
raise PipelineError(
    "dbt model 'user_metrics' failed to compile",
    "Check model syntax: dbt/models/marts/user_metrics.sql:15"
)
```

**Issue**: Slow startup time
```python
# Bad - Heavy imports at module level
import heavy_library

# Good - Lazy imports
def feature_using_heavy_lib():
    import heavy_library  # Import only when needed
```

**Issue**: Test failures in CI
```bash
# Ensure deterministic behavior
pytest tests/ --randomly-dont-reorganize

# Check for environment-specific issues
pytest tests/ -v --capture=no
```

---

## 📖 Documentation Standards

### Docstring Template
```python
def function_name(param1: str, param2: Optional[int] = None) -> ReturnType:
    """One-line summary (imperative mood).

    More detailed description if needed. Explain what the function does,
    not how it does it. Focus on the contract and guarantees.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: None)

    Returns:
        Description of return value and its format

    Raises:
        ValidationError: When param1 is invalid
        PipelineError: When execution fails

    Example:
        >>> result = function_name("example")
        >>> print(result)
        ExpectedOutput

    Note:
        Any important notes or caveats
    """
```

### README Template for Features
```markdown
# Feature Name

## Overview
Brief description of what the feature does and why it exists.

## Usage

### Basic Example
\`\`\`bash
sbdk feature-command --option value
\`\`\`

### Advanced Example
\`\`\`bash
sbdk feature-command --advanced --verbose
\`\`\`

## Configuration
How to configure the feature in sbdk_config.json

## API Reference
Link to detailed API docs

## Testing
How to test the feature

## Troubleshooting
Common issues and solutions
```

---

## 🎓 Learning Resources

### Understanding SBDK
1. Read [SBDK_PLATFORM_VISION.md](./SBDK_PLATFORM_VISION.md) - Understand the strategy
2. Read existing code in `src/sbdk/` - Learn patterns
3. Run tests: `pytest tests/ -v` - See how it works
4. Create test project: `sbdk init test-project` - Experience it

### Modern Data Stack
- **dbt**: https://docs.getdbt.com/
- **DuckDB**: https://duckdb.org/docs/
- **DLT**: https://dlthub.com/docs/

### Python Best Practices
- **Typer**: https://typer.tiangolo.com/
- **Rich**: https://rich.readthedocs.io/
- **Pydantic**: https://docs.pydantic.dev/
- **pytest**: https://docs.pytest.org/

---

## ✅ Pre-Commit Checklist

Before committing code:

```markdown
- [ ] Code follows SBDK architecture principles
- [ ] Type hints on all functions
- [ ] Google-style docstrings
- [ ] Tests added/updated (95%+ coverage)
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Type checking passes: `mypy src/sbdk`
- [ ] Linting passes: `ruff check src/sbdk`
- [ ] Formatting applied: `black src/sbdk`
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Backward compatible (or migration guide added)
- [ ] Commit message follows conventional commits
```

---

## 🚀 Getting Started with Development

### First-Time Setup
```bash
# 1. Clone and install
git clone https://github.com/sbdk-dev/sbdk-dev.git
cd sbdk-dev
uv sync --extra dev

# 2. Read the vision
cat SBDK_PLATFORM_VISION.md

# 3. Explore the code
ls -la src/sbdk/
cat src/sbdk/cli/main.py

# 4. Run tests
pytest tests/ -v

# 5. Try SBDK
uv run sbdk init test-project
cd test-project && uv run sbdk run
```

### Your First Contribution
1. Pick a small task from roadmap (Phase 1)
2. Create feature branch: `claude/task-name-[session-id]`
3. Implement with TDD (tests first!)
4. Ensure quality gates pass
5. Commit and push
6. Verify in clean environment

---

## 📞 Support & Questions

### While Developing
- **Platform Vision**: Check [SBDK_PLATFORM_VISION.md](./SBDK_PLATFORM_VISION.md)
- **Code Examples**: Look in `src/sbdk/` and `tests/`
- **Test Project**: Create one to test your changes

### Common Questions

**Q: Should this be a CLI command or Python API?**
A: Both! Implement core functionality as Python API, then add CLI wrapper.

**Q: Where should I add tests?**
A: Mirror source structure: `src/sbdk/foo/bar.py` → `tests/foo/test_bar.py`

**Q: How do I handle optional dependencies?**
A: Use lazy imports and clear error messages if missing.

**Q: What Python version should I target?**
A: Support 3.9+, optimize for 3.11+.

---

## 🎯 Success Criteria

Claude is succeeding when:
- ✅ Code aligns with Platform Vision
- ✅ Follows all architecture principles
- ✅ Passes all quality gates
- ✅ Includes comprehensive tests
- ✅ Has clear documentation
- ✅ Provides excellent developer experience
- ✅ Maintains backward compatibility
- ✅ Enables 30-second iteration cycles

---

**Remember**: SBDK is a **foundation**, not a platform. Build core capabilities excellently, integrate with specialists, and always optimize for local-first rapid iteration.

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Next Review: After Phase 1 completion*
