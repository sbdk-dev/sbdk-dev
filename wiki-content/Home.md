# Welcome to SBDK.dev Wiki

**SBDK.dev** (Sandbox Development Kit) is a comprehensive sandbox framework for data pipeline development that provides a complete local-first environment.

[![PyPI version](https://img.shields.io/pypi/v/sbdk-dev.svg)](https://pypi.org/project/sbdk-dev/)
[![Python 3.9+](https://img.shields.io/pypi/pyversions/sbdk-dev.svg)](https://pypi.org/project/sbdk-dev/)
[![License: MIT](https://img.shields.io/pypi/l/sbdk-dev.svg)](https://github.com/sbdk-dev/sbdk-dev/blob/main/LICENSE)

## Quick Start

```bash
# Install SBDK
pip install sbdk-dev

# Create your first pipeline
sbdk init my_pipeline
cd my_pipeline

# Run the pipeline
sbdk run
```

**That's it!** Your DuckDB database now contains production-ready analytics data.

## What You Get

- **⚡ 11x Faster Installation** with uv package manager
- **🏠 100% Local** - no cloud dependencies
- **📦 Out-of-the-Box Ready** - complete pipeline in 30 seconds
- **🎯 Intelligent Guided UI** - interactive CLI experience

## Documentation

### Getting Started
- **[Getting Started](Getting-Started)** - Quick start guide
- **[User Guide](User-Guide)** - Complete feature walkthrough
- **[FAQ](FAQ)** - Frequently asked questions

### Architecture & Design
- **[Architecture](Architecture)** - System architecture overview
- **[DLT Pipeline Architecture](DLT-Pipeline-Architecture)** - Data loading architecture
- **[DBT Models](DBT-Models)** - Transformation models structure

### Configuration & Usage
- **[Configuration](Configuration)** - Configuration guide
- **[Configuration Schema](Configuration-Schema)** - Complete config reference
- **[API Reference](API-Reference)** - Complete command documentation
- **[Server CLI Guide](Server-CLI-Guide)** - Webhook server setup

### Advanced Topics
- **[Build Binary](Build-Binary)** - Create standalone executables
- **[CI/CD Guide](CI-CD-Guide)** - Continuous integration setup
- **[GitHub Release Workflow](GitHub-Release-Workflow)** - Release automation

## Key Features

### Complete Data Pipeline
```
Generate Data (DLT) → Load (DuckDB) → Transform (dbt) → Query (SQL)
```

### Tech Stack
- **DuckDB**: Lightning-fast embedded analytics database
- **DLT**: Modern data loading with schema evolution
- **dbt Core**: Industry-standard transformations
- **Typer + Rich**: Beautiful CLI interface

## Resources

- **[GitHub Repository](https://github.com/sbdk-dev/sbdk-dev)** - Source code
- **[PyPI Package](https://pypi.org/project/sbdk-dev/)** - Install package
- **[Report Issues](https://github.com/sbdk-dev/sbdk-dev/issues)** - Bug reports

## Quick Reference

```bash
# Core commands
sbdk init <project>      # Create new project
sbdk run                 # Run complete pipeline
sbdk run --visual        # Interactive mode
sbdk run --watch         # Auto-reload mode
sbdk query               # Query database
sbdk debug               # System diagnostics
sbdk version             # Show version
```

---

**Built with ❤️ for local-first data development**
