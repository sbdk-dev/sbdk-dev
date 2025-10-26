# Getting Started with SBDK.dev

Welcome to SBDK.dev! This guide will help you set up your first local data pipeline in minutes.

## Prerequisites

- **Python 3.9 or higher** ([Download](https://www.python.org/downloads/))
- **pip** or **uv** (package manager)
- **5 minutes** of your time

## Installation

### Option 1: Quick Install with pip

```bash
pip install sbdk-dev
```

### Option 2: Fast Install with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is 10-11x faster than pip:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install SBDK
uv pip install sbdk-dev
```

### Option 3: Standalone Binaries (No Python Required)

Download pre-built binaries from [GitHub Releases](https://github.com/sbdk-dev/sbdk-dev/releases):

- **Windows**: `sbdk-windows-x86_64.exe.zip`
- **macOS**: `sbdk-macos-universal.tar.gz`
- **Linux**: `sbdk-linux-x86_64.tar.gz`

```bash
# macOS/Linux
wget https://github.com/sbdk-dev/sbdk-dev/releases/latest/download/sbdk-macos-universal.tar.gz
tar -xzf sbdk-macos-universal.tar.gz
./sbdk version

# Windows
# Download and extract sbdk-windows-x86_64.exe.zip
# Run: sbdk.exe version
```

## Verify Installation

```bash
sbdk version
```

You should see:
```
╭────────────────────────────────── Version ───────────────────────────────────╮
│ SBDK.dev v1.1.2                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Your First Data Pipeline

### Step 1: Initialize a New Project

```bash
sbdk init my_first_pipeline
```

This creates a complete project structure:
```
my_first_pipeline/
├── pipelines/          # Data ingestion scripts
│   ├── users.py
│   ├── events.py
│   └── orders.py
├── dbt/                # Transformation models
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── data/               # DuckDB database (created on first run)
├── query.py            # Helper script for querying
└── sbdk_config.json    # Project configuration
```

### Step 2: Navigate to Your Project

```bash
cd my_first_pipeline
```

### Step 3: Run the Pipeline

```bash
sbdk run
```

This will:
1. ✅ Generate synthetic data (10,000+ records)
2. ✅ Load data into DuckDB
3. ✅ Run dbt transformations
4. ✅ Create analytics-ready tables

**Time**: ~10-15 seconds

### Step 4: Query Your Data

#### View All Tables

```bash
sbdk query
```

Output:
```
Available tables:
  stg_users                      10,000 rows
  stg_events                     50,000 rows
  stg_orders                     25,000 rows
  int_user_activity              10,000 rows
  user_metrics                   10,000 rows
```

#### Run SQL Queries

```bash
sbdk query "SELECT * FROM stg_users LIMIT 5"
```

#### Interactive SQL Mode

```bash
sbdk query --interactive
```

Or use the included helper script:

```bash
python query.py --interactive
```

## Next Steps

### Explore the Data

```bash
# User demographics
sbdk query "SELECT age_group, COUNT(*) as count FROM stg_users GROUP BY age_group"

# Top products
sbdk query "SELECT product_name, SUM(amount) as revenue FROM stg_orders GROUP BY product_name ORDER BY revenue DESC LIMIT 10"

# User activity metrics
sbdk query "SELECT * FROM user_metrics ORDER BY total_revenue DESC LIMIT 10"
```

### Customize Your Pipeline

1. **Modify data generation**: Edit `pipelines/users.py`, `pipelines/events.py`, or `pipelines/orders.py`
2. **Add transformations**: Create new models in `dbt/models/`
3. **Adjust configuration**: Edit `sbdk_config.json`

### Watch Mode (Auto-reload)

```bash
sbdk run --watch
```

Changes to pipeline files automatically trigger re-runs.

### Development Mode

```bash
sbdk dev dev
```

Enhanced development experience with hot reload and detailed logging.

## Common Commands

```bash
# Show all commands
sbdk --help

# Initialize new project
sbdk init <project_name>

# Run complete pipeline
sbdk run

# Run only data generation
sbdk run --pipelines-only

# Run only dbt transformations
sbdk run --dbt-only

# Query database
sbdk query [SQL]

# Interactive SQL
sbdk query --interactive

# View version
sbdk version

# Debug configuration
sbdk debug

# Generate shell completion
sbdk completion bash
```

## Troubleshooting

### Command not found

If `sbdk` command is not found after installation:

```bash
# Check if it's installed
pip list | grep sbdk-dev

# Try with python -m
python -m sbdk version

# Or use uv
uv run sbdk version
```

### Database locked

If you see "database is locked" errors:

```bash
# Close all other connections to the database
# On macOS/Linux:
lsof data/*.duckdb | grep duckdb

# On Windows:
# Close any DuckDB clients or Python scripts
```

### Import errors

```bash
# Reinstall with all dependencies
pip install --force-reinstall sbdk-dev

# Or with uv
uv pip install --reinstall sbdk-dev
```

## Learn More

- **[User Guide](USER_GUIDE.md)**: Detailed features and workflows
- **[API Reference](API_REFERENCE.md)**: Complete command documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)**: Contributing and development
- **[FAQ](FAQ.md)**: Frequently asked questions
- **[GitHub Repository](https://github.com/sbdk-dev/sbdk-dev)**: Source code and issues

## Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/sbdk-dev/sbdk-dev/issues)
- **Discussions**: [Ask questions](https://github.com/sbdk-dev/sbdk-dev/discussions)
- **Documentation**: [Full docs](https://docs.sbdk.dev) (coming soon)

---

**Next**: Continue to the [User Guide](USER_GUIDE.md) for advanced features →
