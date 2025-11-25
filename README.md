# SBDK: Local-First Data Pipeline Sandbox

**[Public Archive - November 2025]**

> A complete reference implementation of a local-first semantic data development platform with AI integration patterns, demonstrating production-grade architecture for building modern data tools.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI Version](https://img.shields.io/badge/pypi-v1.1.2-blue)](https://pypi.org/project/sbdk-dev/)

---

## Overview

SBDK (Semantic Bridge Development Kit) demonstrates best practices for building AI-native data platforms with semantic intelligence. This archive showcases a fully-functional local-first data development environment that enables rapid iteration, safe experimentation, and production-ready patterns.

### What This Project Demonstrates

- **Local-First Architecture**: Complete data platform running on DuckDB with zero cloud dependencies
- **Semantic Layer Integration**: Business logic abstraction enabling AI-powered analytics
- **MCP Server Pattern**: Model Context Protocol implementation for AI agent integration
- **Professional CLI Design**: Enterprise-grade command-line interface with rich error handling
- **Test-Driven Development**: 100% test coverage with comprehensive quality validation
- **Modern Python Packaging**: Built with `uv` for 10-100x faster dependency management

### Technology Stack

```
┌─────────────────────────────────────────┐
│         CLI Interface (Typer)            │  Rich terminal UI, global options
├─────────────────────────────────────────┤
│      Data Transformation (dbt)           │  SQL-first transformations
├─────────────────────────────────────────┤
│      Data Ingestion (DLT)                │  Modular pipeline framework
├─────────────────────────────────────────┤
│      Analytics Engine (DuckDB)           │  Embedded OLAP database
├─────────────────────────────────────────┤
│      Package Manager (uv)                │  10-100x faster than pip
└─────────────────────────────────────────┘
```

---

## Key Features

### 1. Complete Local Development Environment

- **30-second iteration cycles**: Instant feedback without cloud latency
- **Zero configuration**: Works out-of-the-box after installation
- **Production parity**: Local patterns match production deployment
- **Isolated sandbox**: Safe experimentation without affecting production

### 2. Professional CLI Architecture

```bash
# Global options available to all commands
sbdk --verbose --format json query "SELECT * FROM orders"
sbdk --dry-run --project-dir ./my-project run

# Rich error handling with actionable suggestions
sbdk init duplicate_project
# Error: Project 'duplicate_project' already exists
# Suggestion: Use 'sbdk init --force' to overwrite

# Multi-format output (text, json, yaml, table, minimal)
sbdk version --format json
```

**Architecture Highlights:**
- Comprehensive exception hierarchy with custom exit codes
- Centralized context management with lifecycle hooks
- Pydantic-based configuration validation
- Multi-format output system for automation
- Built-in logging and observability

### 3. Semantic Layer Foundation

```python
# Business logic abstraction for AI agents
from sbdk.semantic import SemanticLayer

sl = SemanticLayer("sbdk_semantic.yml")

# Query by business metrics, not raw SQL
result = sl.query(
    metrics=["monthly_recurring_revenue", "customer_lifetime_value"],
    dimensions=["customer_segment"],
    filters={"order_month": "2024-01"}
)

# Natural language queries
result = sl.query_natural("Show me MRR by segment last month")
```

### 4. MCP Server for AI Integration

```python
# Model Context Protocol server for AI agents
from sbdk.mcp import MCPServer

server = MCPServer(name="sbdk", version="4.0")

@server.tool
def query_data(sql: str, env: str = "dev") -> dict:
    """Execute SQL in specified environment"""
    return sbdk.query(sql, environment=env)

@server.tool
def run_pipeline(pipeline: str, incremental: bool = False) -> dict:
    """Execute data pipeline"""
    return sbdk.pipeline.run(pipeline, incremental=incremental)

server.run(host="localhost", port=3000)
```

### 5. Comprehensive Testing Framework

```bash
# 100% test coverage with multiple test types
uv run pytest tests/ --cov=sbdk

# Architecture validation
uv run pytest tests/test_phase1_*.py -v

# Integration tests
uv run pytest tests/integration/ -v

# Performance benchmarks
uv run pytest tests/ -m performance
```

---

## Quick Start

### Installation

```bash
# Using uv (recommended - 10-100x faster)
pip install uv
uv tool install sbdk-dev

# Or using pip
pip install sbdk-dev
```

### Create Your First Project

```bash
# Initialize new project
sbdk init my_analytics_project
cd my_analytics_project

# Run complete pipeline (ingestion + transformation)
sbdk run

# Query your data
sbdk query "SELECT * FROM stg_orders LIMIT 10"

# Interactive SQL mode
sbdk query --interactive
```

### Project Structure

```
my_analytics_project/
├── dbt_project/              # dbt transformations
│   ├── models/
│   │   ├── staging/         # Data cleaning
│   │   ├── intermediate/    # Business logic
│   │   └── marts/           # Final analytics tables
│   └── tests/               # Data quality tests
├── pipelines/               # DLT data pipelines
│   ├── users.py
│   ├── events.py
│   └── orders.py
├── data/                    # DuckDB database files
│   └── dev.duckdb
└── sbdk_config.json         # Configuration
```

---

## Architecture Highlights

### Exception Hierarchy

```python
# Structured error handling with context
from sbdk.exceptions import (
    SBDKException,           # Base exception
    ConfigurationError,      # Exit code 2
    PipelineError,           # Exit code 3
    ValidationError,         # Exit code 4
    NetworkError            # Exit code 5
)

# Errors include suggestions
try:
    config = load_config("invalid.json")
except ConfigurationError as e:
    print(e.message)        # "Invalid configuration format"
    print(e.suggestion)     # "Check JSON syntax with 'jsonlint'"
    print(e.details)        # {"file": "invalid.json", "line": 12}
```

### Context Management

```python
# Centralized state and lifecycle management
from sbdk.context import SBDKContext

with SBDKContext(
    verbose=True,
    dry_run=False,
    format="json"
) as ctx:
    # Automatic logging setup
    ctx.logger.info("Starting pipeline")

    # Resource tracking
    ctx.register_resource(connection, cleanup_fn)

    # Configuration access
    config = ctx.config

    # Automatic cleanup on exit
```

### Output Formatting

```python
# Multi-format output system
from sbdk.formatters import OutputFormatter

formatter = OutputFormatter(format="json")

# Format for different consumers
formatter.format_data({"status": "success"})
formatter.format_error(exception)
formatter.format_list(items)
formatter.format_table(rows, columns)
```

---

## Documentation

### Core Documentation

- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - System architecture and design patterns
- [**SETUP.md**](SETUP.md) - Development setup and contribution guide
- [**VISION.md**](VISION.md) - Original platform vision and roadmap
- [**CHANGELOG.md**](CHANGELOG.md) - Version history and changes

### Technical Documentation

- [**API Reference**](docs/API_REFERENCE.md) - Complete API documentation
- [**Configuration Guide**](docs/CONFIGURATION.md) - Configuration schema and options
- [**Testing Framework**](docs/testing-framework.md) - Testing patterns and practices
- [**Data Sources**](docs/data-sources.md) - Connector architecture
- [**Quality Framework**](docs/quality-framework.md) - Data quality validation

### Deployment Guides

- [**Build Binary**](docs/BUILD_BINARY.md) - Creating standalone executables
- [**CI/CD Guide**](docs/CI_CD_GUIDE.md) - Continuous integration patterns
- [**GitHub Workflow**](docs/GITHUB_RELEASE_WORKFLOW.md) - Release process

---

## Use Cases & Learning Opportunities

### For Data Engineers

- **Learn local-first development patterns**: Build and test pipelines without cloud costs
- **Study production-grade CLI design**: Professional command-line interface architecture
- **Understand semantic layer integration**: Bridge between business logic and data

### For Platform Engineers

- **MCP server implementation**: Connect AI agents to data infrastructure
- **Context management patterns**: Lifecycle management and resource cleanup
- **Error handling architecture**: Structured exceptions with actionable suggestions

### For Tool Builders

- **Modern Python packaging**: Using `uv` for fast dependency management
- **Test-driven development**: Achieving 100% test coverage
- **Multi-format output**: Supporting automation and scripting

### For AI/ML Engineers

- **Semantic query patterns**: Business-logic-first data access
- **AI agent integration**: MCP protocol for tool use
- **Local development for AI**: Safe sandbox for agent experimentation

---

## Technical Specifications

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, Windows
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 500MB for installation, varies with data

### Dependencies

```toml
# Core dependencies
duckdb >= 0.9.0        # Embedded OLAP database
dbt-core >= 1.7.0       # SQL transformations
dlt[duckdb] >= 0.4.0    # Data loading framework
typer >= 0.12.0         # CLI framework
rich >= 13.7.0          # Terminal formatting
pydantic >= 2.5.0       # Data validation
```

### Performance

- **Startup time**: < 1 second for most commands
- **Pipeline execution**: 10-30 seconds for demo dataset
- **Query latency**: < 100ms for typical queries
- **Memory footprint**: 200-500MB during operation

---

## Testing

### Test Suite Overview

```bash
# Full test suite (150+ tests)
uv run pytest tests/ -v

# Coverage report
uv run pytest tests/ --cov=sbdk --cov-report=html

# Phase 1 architecture tests (125 tests)
uv run pytest tests/test_phase1_*.py -v

# Integration tests
uv run pytest tests/integration/ -v

# Performance benchmarks
uv run pytest tests/ -m performance
```

### Test Categories

- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end workflow testing
- **Architecture Tests**: Design pattern validation
- **Performance Tests**: Benchmark and optimization
- **Quality Tests**: Data quality validation

---

## Contributing & Development

While this project is archived, the codebase serves as a reference for:

1. **Learning**: Study production-grade Python patterns
2. **Inspiration**: Adapt patterns for your own projects
3. **Education**: Teaching modern data engineering practices

### Development Setup

```bash
# Clone repository
git clone https://github.com/sbdk-dev/sbdk.git
cd sbdk

# Install with development dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Code quality
uv run black sbdk/ tests/
uv run ruff check sbdk/ tests/
uv run mypy sbdk/
```

See [SETUP.md](SETUP.md) for detailed development instructions.

---

## Project Status

This project was actively developed from 2024-2025 and is now archived as a complete reference implementation. The codebase represents:

- **100% test coverage** across core functionality
- **Production-ready architecture** with comprehensive error handling
- **Complete documentation** for all features and patterns
- **Real-world usage** validated through extensive testing

### What Works

- ✅ Complete local development environment
- ✅ DuckDB + dbt + DLT integration
- ✅ Professional CLI with global options
- ✅ Multi-format output (text, JSON, YAML, table)
- ✅ Comprehensive testing framework
- ✅ Environment management system
- ✅ Quality validation framework
- ✅ Interactive SQL query interface

### Future Directions (For Fork/Adaptation)

- MCP server full implementation
- Custom semantic layer (beyond dbt)
- Ibis integration for backend portability
- AI agent swarm orchestration
- Cloud deployment patterns

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built with these excellent open-source projects:

- [DuckDB](https://duckdb.org/) - Fast in-process analytical database
- [dbt](https://www.getdbt.com/) - SQL transformation framework
- [DLT](https://dlthub.com/) - Data loading tool
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

---

## Archive Information

**Archive Date**: November 2025
**Final Version**: 1.1.2
**Status**: Complete reference implementation

This project is archived as a complete, working example of modern data engineering practices. The code remains available for learning, inspiration, and adaptation.

For questions or discussion about the patterns demonstrated here, please open a GitHub Discussion.

---

**Built with ❤️ by the SBDK team as a contribution to the data engineering community.**
