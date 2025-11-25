# SBDK: Local-First Data Pipeline Sandbox

> Build and test complete data pipelines in 30 seconds. Zero cloud setup, zero configuration, zero cost.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v1.1.2-blue)](https://pypi.org/project/sbdk-dev/)
[![Tests](https://img.shields.io/badge/tests-150%2B%20passing-brightgreen)](tests/)

**[Archived November 2025]** — Complete, production-ready reference implementation.

---

## What is SBDK?

SBDK is a **local development sandbox** that gives you a complete data platform running on your laptop:

```bash
# Install
pip install sbdk-dev

# Create project
sbdk init my_project
cd my_project

# Run complete pipeline: data generation → ingestion → transformation
sbdk run

# Query your data
sbdk query "SELECT * FROM orders_daily LIMIT 10"
```

**You get a working data pipeline in under 60 seconds.**

No Docker. No Kubernetes. No cloud accounts. No configuration files to write.

---

## What Problem Does This Solve?

**Before SBDK:**
- Setting up a data pipeline development environment takes days
- Testing requires deploying to cloud infrastructure ($$$)
- Iteration cycles are slow (push → wait → test → repeat)
- Onboarding new team members is painful
- Breaking production is expensive

**With SBDK:**
- Full pipeline environment in 1 command (30 seconds)
- Test everything locally, safely (zero cost)
- Iteration cycles are instant (30-second feedback loops)
- New engineers productive in < 5 minutes
- Production patterns validated before deployment

---

## Who Is This For?

### Data Engineers
→ **Job-to-be-done:** Test dbt models and data pipelines without cloud infrastructure

```bash
# Edit your dbt model
vim dbt_project/models/marts/orders_daily.sql

# Test changes instantly
sbdk run --dbt-only

# Query results
sbdk query --interactive
```

### Platform Engineers
→ **Job-to-be-done:** Build and evaluate data tools on realistic infrastructure

SBDK demonstrates production patterns you can adapt:
- Professional CLI architecture (exception handling, context management)
- MCP server for AI agent integration
- Semantic layer for business logic abstraction
- 100% test coverage patterns

### Data Engineering Students
→ **Job-to-be-done:** Learn modern data stack without wrestling with deployment

Study working examples of:
- dbt transformations (staging → intermediate → marts)
- DLT data pipelines (extraction and loading)
- DuckDB OLAP queries
- Data quality frameworks
- Testing patterns

---

## How Does It Work?

### Architecture

```
┌─────────────────────────────────────────┐
│  CLI (Typer + Rich)                      │  ← Professional command-line interface
├─────────────────────────────────────────┤
│  dbt Transformations                     │  ← SQL models: staging → marts
├─────────────────────────────────────────┤
│  DLT Data Pipelines                      │  ← Extract & load synthetic data
├─────────────────────────────────────────┤
│  DuckDB Embedded Database                │  ← Local OLAP engine (no server)
└─────────────────────────────────────────┘
```

### What You Get

**Out of the box:**
- ✅ **DuckDB database** — Fast embedded OLAP engine
- ✅ **dbt project** — Pre-configured with staging/intermediate/marts layers
- ✅ **DLT pipelines** — Synthetic data generation (users, events, orders)
- ✅ **Quality framework** — Data validation and testing
- ✅ **CLI interface** — Professional commands with rich error handling

**Your data pipeline:**
1. **DLT pipelines** generate synthetic data → load into DuckDB
2. **dbt models** transform raw data → clean staging → business logic → analytical marts
3. **Quality tests** validate data integrity
4. **Interactive queries** explore results

---

## Quick Start

### Installation

```bash
# Using pip
pip install sbdk-dev

# Using uv (10-100x faster)
pip install uv
uv tool install sbdk-dev
```

### Create Your First Pipeline

```bash
# 1. Initialize project
sbdk init my_analytics_project
cd my_analytics_project

# 2. Run pipeline (generates data + runs dbt)
sbdk run

# Output:
# ✓ Generated 10,000 users
# ✓ Generated 50,000 events
# ✓ Generated 20,000 orders
# ✓ Loaded into DuckDB
# ✓ Running dbt models...
# ✓ 12 models completed
# ✓ All tests passed
```

### Query Your Data

```bash
# Interactive SQL mode
sbdk query --interactive

# Run specific query
sbdk query "
  SELECT
    order_date,
    COUNT(*) as order_count,
    SUM(order_total) as revenue
  FROM marts.orders_daily
  GROUP BY order_date
  ORDER BY order_date DESC
  LIMIT 7
"
```

### Iterate on Models

```bash
# Edit a dbt model
vim dbt_project/models/staging/stg_orders.sql

# Test just dbt (skip data generation)
sbdk run --dbt-only

# Verify changes
sbdk query "SELECT * FROM stg_orders LIMIT 5"
```

---

## Real-World Example

### Use Case: Building a Customer Analytics Pipeline

```bash
# 1. Generate test data
sbdk init customer_analytics
cd customer_analytics
sbdk run

# 2. Your dbt project structure
dbt_project/
├── models/
│   ├── staging/
│   │   ├── stg_users.sql       # Clean raw user data
│   │   ├── stg_events.sql      # Clean raw events
│   │   └── stg_orders.sql      # Clean raw orders
│   ├── intermediate/
│   │   ├── int_user_events.sql    # Join users + events
│   │   └── int_user_orders.sql    # Join users + orders
│   └── marts/
│       ├── customer_360.sql        # Complete customer view
│       ├── orders_daily.sql        # Daily order aggregates
│       └── user_activity.sql       # User engagement metrics

# 3. Query your mart
sbdk query "
  SELECT
    customer_segment,
    COUNT(DISTINCT customer_id) as customers,
    AVG(total_orders) as avg_orders,
    AVG(lifetime_value) as avg_ltv
  FROM marts.customer_360
  GROUP BY customer_segment
"

# Output:
# ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
# ┃ customer_segment ┃ customers ┃ avg_orders ┃ avg_ltv ┃
# ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
# │ enterprise       │ 127       │ 24.3       │ $45,230 │
# │ mid_market       │ 453       │ 12.1       │ $12,450 │
# │ smb              │ 2,341     │ 3.8        │ $1,240  │
# └──────────────────┴───────────┴────────────┴─────────┘
```

---

## When Would You Use This?

### Scenario 1: Learning dbt
**Problem:** You want to learn dbt but don't have a data warehouse
**Solution:** SBDK gives you instant dbt environment with real data

```bash
sbdk init learning_dbt
cd learning_dbt
# Explore pre-built models, modify them, see results instantly
```

### Scenario 2: Testing Pipeline Changes
**Problem:** Need to validate a complex transformation before production
**Solution:** Test locally, iterate fast, deploy with confidence

```bash
# Copy your production dbt model
cp ~/prod-repo/models/revenue_by_region.sql dbt_project/models/marts/

# Test it
sbdk run --dbt-only

# Verify output matches expectations
sbdk query "SELECT * FROM marts.revenue_by_region"
```

### Scenario 3: Building a Data Tool
**Problem:** You're building a data catalog/lineage/quality tool
**Solution:** SBDK provides realistic infrastructure to test against

```python
# Your tool can connect to SBDK's DuckDB
import duckdb

conn = duckdb.connect('data/dev.duckdb')
tables = conn.execute("SELECT * FROM information_schema.tables").fetchall()

# Test your catalog against real dbt lineage
```

### Scenario 4: Interview Prep / Demos
**Problem:** Need to demonstrate data engineering skills
**Solution:** Working pipeline you can run through in a 30-minute interview

---

## What's Included

### Professional CLI Architecture

```bash
# Global options on every command
sbdk --verbose query "SELECT 1"              # Debug logging
sbdk --format json version                    # JSON output for automation
sbdk --dry-run run                           # Preview without executing
sbdk --project-dir ../other-project run      # Run different project

# Rich error messages with suggestions
$ sbdk query "SELCT * FROM orders"
✗ Error: SQL syntax error

  SELCT * FROM orders
  ^^^^^
  Did you mean: SELECT?

  Suggestion: Check your SQL syntax
  Exit code: 3
```

### Comprehensive Testing Framework

```bash
# Run all tests (150+ tests)
pytest tests/ -v

# Test categories
pytest tests/test_phase1_*.py          # Architecture tests
pytest tests/integration/              # End-to-end tests
pytest tests/ -m performance           # Performance benchmarks

# Coverage report
pytest tests/ --cov=sbdk --cov-report=html
# 100% coverage on core functionality
```

### Quality Framework

```python
# Built-in data quality validation
from sbdk.quality import QualityFramework

qf = QualityFramework()

# Validate data quality
results = qf.validate_table(
    table="stg_orders",
    rules={
        "primary_key": "order_id",
        "not_null": ["order_id", "customer_id", "order_total"],
        "positive": ["order_total"],
        "valid_date": ["order_date"]
    }
)

# Automatic reporting
qf.generate_report(results)
```

### Environment Management

```bash
# Multiple environments (dev, staging, prod patterns)
sbdk env create staging --template analytics
sbdk env switch staging
sbdk env list

# Each environment has isolated:
# - DuckDB database
# - dbt profiles
# - Configuration
```

---

## Advanced Features

### Semantic Layer Foundation

```python
# Business logic abstraction (documented pattern, implementation in progress)
from sbdk.semantic import SemanticLayer

sl = SemanticLayer("sbdk_semantic.yml")

# Query by business metrics, not raw SQL
result = sl.query(
    metrics=["monthly_recurring_revenue", "customer_lifetime_value"],
    dimensions=["customer_segment"],
    filters={"month": "2024-01"}
)
```

### MCP Server for AI Integration

```python
# Model Context Protocol server pattern
from sbdk.mcp import MCPServer

server = MCPServer(name="sbdk")

@server.tool
def query_data(sql: str) -> dict:
    """AI agents can query your data"""
    return sbdk.query(sql)

@server.tool
def run_pipeline(incremental: bool = False) -> dict:
    """AI agents can execute pipelines"""
    return sbdk.pipeline.run(incremental=incremental)

server.run(port=3000)
```

---

## Documentation

### Getting Started
- [**Installation & Setup**](SETUP.md) — Development environment setup
- [**Quick Start Guide**](#quick-start) — Get running in 60 seconds (above)
- [**Architecture Overview**](docs/ARCHITECTURE.md) — System design and patterns

### Technical Deep Dives
- [**API Reference**](docs/API_REFERENCE.md) — Complete API documentation
- [**dbt Models**](docs/DBT_MODELS.md) — Pre-built transformation models
- [**DLT Pipelines**](docs/DLT_PIPELINE_ARCHITECTURE.md) — Data pipeline architecture
- [**Testing Framework**](docs/testing-framework.md) — Testing patterns and practices
- [**Quality Framework**](docs/quality-framework.md) — Data validation patterns

### Advanced Topics
- [**Data Sources**](docs/data-sources.md) — Connector architecture (Postgres, CSV)
- [**Incremental Processing**](docs/incremental-processing.md) — Efficient data loading
- [**Environment Management**](docs/environment-management.md) — Multi-environment workflows
- [**MCP Server**](docs/mcp-server.md) — AI agent integration patterns

### Build & Deploy
- [**Configuration**](docs/CONFIGURATION.md) — Configuration schema and options
- [**Build Binary**](docs/BUILD_BINARY.md) — Create standalone executables
- [**CI/CD Guide**](docs/CI_CD_GUIDE.md) — Continuous integration patterns
- [**Release Workflow**](docs/GITHUB_RELEASE_WORKFLOW.md) — Release process

---

## Comparison: SBDK vs. Alternatives

| | SBDK | dbt + Snowflake | Dagster + Postgres | Custom Scripts |
|---|---|---|---|---|
| **Setup time** | 30 seconds | Hours/Days | Hours | Hours |
| **Cost (dev)** | $0 | $$ | $ | $0 |
| **Iteration speed** | Instant | Minutes | Minutes | Varies |
| **Cloud required** | No | Yes | No | No |
| **Production-ready patterns** | Yes | Yes | Yes | No |
| **Learning curve** | Low | Medium | High | N/A |
| **Full pipeline** | ✅ | ✅ | ✅ | Partial |
| **Testing framework** | ✅ | Partial | ✅ | No |
| **Local OLAP** | ✅ DuckDB | ❌ | ❌ | ❌ |

**Use SBDK when:**
- ✅ You need instant local development environment
- ✅ You want to learn data engineering without cloud costs
- ✅ You're prototyping data pipelines
- ✅ You need to test dbt models locally
- ✅ You're building/testing data engineering tools

**Use cloud platforms when:**
- Production deployment at scale
- Team collaboration on shared infrastructure
- Processing petabyte-scale datasets

---

## Technical Specifications

### System Requirements
- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **OS**: Linux, macOS, Windows
- **Memory**: 4GB minimum, 8GB recommended
- **Disk**: 500MB installation + data storage

### Core Dependencies
```toml
duckdb >= 0.9.0        # Embedded OLAP database
dbt-core >= 1.7.0       # SQL transformation framework
dlt[duckdb] >= 0.4.0    # Data loading framework
typer >= 0.12.0         # CLI framework
rich >= 13.7.0          # Terminal formatting
pydantic >= 2.5.0       # Data validation
```

### Performance
- **Startup**: < 1 second (most commands)
- **Pipeline execution**: 10-30 seconds (10K users, 50K events, 20K orders)
- **Query latency**: < 100ms (typical analytical queries)
- **Memory footprint**: 200-500MB during operation

---

## Architecture Deep Dive

### Exception Hierarchy

Every error includes context and actionable suggestions:

```python
from sbdk.exceptions import PipelineError, ConfigurationError

try:
    pipeline.run()
except PipelineError as e:
    print(e.message)     # "DuckDB connection failed"
    print(e.suggestion)  # "Check that no other process is using dev.duckdb"
    print(e.details)     # {"file": "dev.duckdb", "locked_by": "process_123"}
    sys.exit(e.exit_code)  # Exit code 3
```

### Context Management

Centralized state and lifecycle management:

```python
from sbdk.context import SBDKContext

with SBDKContext(verbose=True, format="json") as ctx:
    # Automatic logging setup
    ctx.logger.info("Starting pipeline")

    # Resource tracking and cleanup
    ctx.register_resource(db_connection, cleanup_fn)

    # Configuration access
    config = ctx.config

    # Automatic cleanup on exit
```

### Multi-Format Output

Support for automation and scripting:

```bash
# Text (default) - human-readable
sbdk version
# SBDK v1.1.2

# JSON - machine-parseable
sbdk version --format json
# {"version": "1.1.2", "python": "3.11.5", "platform": "Darwin"}

# YAML - configuration-friendly
sbdk version --format yaml
# version: 1.1.2
# python: 3.11.5
# platform: Darwin

# Minimal - shell scripts
sbdk version --format minimal
# 1.1.2
```

---

## Project Status

**Archive Status:** Complete reference implementation (November 2025)

### What Works (Production-Ready)
- ✅ Complete local development environment
- ✅ DuckDB + dbt + DLT integration
- ✅ Professional CLI with global options
- ✅ Multi-format output (text, JSON, YAML, table, minimal)
- ✅ Comprehensive testing (150+ tests, 100% coverage on core)
- ✅ Environment management system
- ✅ Quality validation framework
- ✅ Interactive SQL query interface
- ✅ Exception handling with actionable suggestions
- ✅ Comprehensive documentation

### Architectural Patterns Demonstrated
- 🏗️ Professional CLI design (Typer + Rich + Pydantic)
- 🏗️ Context management and resource lifecycle
- 🏗️ Exception hierarchy with custom exit codes
- 🏗️ Multi-format output system
- 🏗️ Test-driven development (TDD)
- 🏗️ Configuration validation with Pydantic
- 🏗️ Modern Python packaging (uv support)

### Documented Patterns (Implementation varies)
- 📚 MCP server integration pattern
- 📚 Semantic layer architecture
- 📚 Ibis for backend portability
- 📚 AI agent integration strategies

---

## Contributing & Learning

While archived, this codebase serves as a **reference implementation** for:

### Data Engineers
Learn production patterns:
- How to structure dbt projects (staging → intermediate → marts)
- Testing strategies for data pipelines
- Quality framework implementation
- Local-first development workflows

### Platform Engineers
Study architectural patterns:
- Professional CLI design with Typer
- Exception handling with context and suggestions
- Multi-format output systems
- Context management and resource lifecycle
- Pydantic configuration validation

### Python Developers
See modern Python practices:
- Type hints throughout
- Pydantic for data validation
- Modern packaging with pyproject.toml
- uv for 10-100x faster dependency management
- Comprehensive testing with pytest

### Development Setup

```bash
# Clone and install
git clone https://github.com/sbdk-dev/sbdk.git
cd sbdk
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Code quality
uv run black sbdk/ tests/
uv run ruff check sbdk/
uv run mypy sbdk/
```

See [SETUP.md](SETUP.md) for detailed development instructions.

---

## FAQ

**Q: Is this ready for production use?**
A: SBDK is designed for **local development and testing**. For production, deploy your dbt models to production data warehouses (Snowflake, BigQuery, Redshift) using dbt Cloud or orchestration tools like Airflow.

**Q: Can I use my own data instead of synthetic data?**
A: Yes! SBDK supports multiple data sources:
```bash
sbdk source add postgres --connection-string "postgresql://..."
sbdk source add csv --path ./my-data.csv
```

**Q: Does this work on Windows?**
A: Yes, SBDK works on Windows, macOS, and Linux.

**Q: Can I use this to learn dbt?**
A: Absolutely! That's a primary use case. You get a complete dbt project with realistic data and can experiment freely.

**Q: Is DuckDB suitable for production?**
A: DuckDB is production-ready for embedded analytics. SBDK uses it for local development; production deployments typically use Snowflake/BigQuery/Redshift.

**Q: How do I deploy my dbt models to production?**
A: Export your dbt models and deploy them to your production warehouse:
```bash
# Your SBDK dbt models are standard dbt
cp -r dbt_project/ ~/production-dbt-project/models/

# Deploy with dbt Cloud or your CI/CD pipeline
dbt run --profiles-dir ~/.dbt --target prod
```

---

## License

MIT License - see [LICENSE](LICENSE) file.

Built with: [DuckDB](https://duckdb.org/) • [dbt](https://www.getdbt.com/) • [DLT](https://dlthub.com/) • [Typer](https://typer.tiangolo.com/) • [Rich](https://rich.readthedocs.io/) • [Pydantic](https://pydantic-docs.helpmanual.io/) • [uv](https://github.com/astral-sh/uv)

---

## Connect

- 📦 [PyPI Package](https://pypi.org/project/sbdk-dev/)
- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/sbdk-dev/sbdk/issues)
- 💬 [Discussions](https://github.com/sbdk-dev/sbdk/discussions)
- 📜 [Vision & Roadmap](VISION.md)
- 📋 [Changelog](CHANGELOG.md)

---

**SBDK: The fastest path from zero to working data pipeline.**

*Archive Notice: This project was actively developed 2024-2025 and is archived as a complete, production-ready reference implementation. The code demonstrates modern data engineering patterns and remains available for learning and adaptation.*
