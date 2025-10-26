# SBDK.dev User Guide

Complete guide to using SBDK for local data pipeline development.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Project Structure](#project-structure)
- [Commands](#commands)
- [Data Generation](#data-generation)
- [Data Transformations](#data-transformations)
- [Querying Data](#querying-data)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)

## Core Concepts

### What is SBDK?

SBDK.dev (Sandbox Development Kit) is a local-first data pipeline framework that combines:

- **DLT (Data Load Tool)**: Data ingestion and loading
- **DuckDB**: Embedded analytical database
- **dbt**: SQL-based data transformations

### Why SBDK?

- ✅ **100% Local**: No cloud dependencies
- ✅ **Zero Configuration**: Works out of the box
- ✅ **Fast Setup**: From zero to pipeline in 30 seconds
- ✅ **Real Data**: Generates realistic synthetic datasets
- ✅ **Production Patterns**: Uses industry-standard tools

## Project Structure

When you run `sbdk init my_project`, you get:

```
my_project/
├── pipelines/                  # Data ingestion
│   ├── users.py               # User data generation
│   ├── events.py              # Event tracking data
│   └── orders.py              # E-commerce orders
├── dbt/                        # Transformations
│   ├── dbt_project.yml        # dbt configuration
│   └── models/
│       ├── _sources.yml       # Source definitions
│       ├── staging/           # Raw → Clean
│       │   ├── stg_users.sql
│       │   ├── stg_events.sql
│       │   └── stg_orders.sql
│       ├── intermediate/      # Business logic
│       │   └── int_user_activity.sql
│       └── marts/             # Analytics-ready
│           └── user_metrics.sql
├── data/                       # Database storage
│   └── my_project.duckdb      # (created on first run)
├── .sbdk/                      # SBDK metadata
│   └── logs/                  # Execution logs
├── query.py                    # Query helper script
└── sbdk_config.json           # Configuration
```

## Commands

### Global Options

Available on all commands:

```bash
--verbose, -v          # Detailed debug output
--quiet, -q            # Suppress non-essential output
--dry-run              # Preview without executing
--format, -f FORMAT    # Output format: text|json|yaml|table|minimal
--project-dir, -p DIR  # Custom project directory
```

### sbdk init

Initialize a new project:

```bash
# Basic usage
sbdk init my_project

# With options
sbdk --verbose init my_analytics --project-dir /path/to/dir
```

### sbdk run

Execute the data pipeline:

```bash
# Run complete pipeline (DLT + dbt)
sbdk run

# Run only data generation
sbdk run --pipelines-only

# Run only dbt transformations
sbdk run --dbt-only

# Watch mode (auto-reload on file changes)
sbdk run --watch

# Verbose output
sbdk --verbose run

# Dry run (preview only)
sbdk --dry-run run
```

### sbdk query

Query your DuckDB database:

```bash
# Show all tables with row counts
sbdk query

# Execute SQL query
sbdk query "SELECT * FROM stg_users WHERE age > 30"

# Multi-line queries
sbdk query "
SELECT
    age_group,
    COUNT(*) as user_count,
    AVG(total_spent) as avg_spent
FROM user_metrics
GROUP BY age_group
ORDER BY user_count DESC
"

# Interactive SQL mode
sbdk query --interactive

# Output as JSON
sbdk --format json query "SELECT * FROM stg_users LIMIT 5"

# Output as table
sbdk --format table query "SELECT * FROM stg_users LIMIT 5"
```

### sbdk dev

Development mode with enhanced features:

```bash
# Start development mode
sbdk dev dev

# Watch for file changes
sbdk dev dev --watch

# Run specific pipelines only
sbdk dev dev --pipelines-only
```

### sbdk version

Show version information:

```bash
# Simple version
sbdk version

# Detailed version info
sbdk --verbose version

# JSON output
sbdk --format json version
```

### sbdk debug

Debug configuration and environment:

```bash
sbdk debug
```

Shows:
- Configuration file status
- Python environment
- Installed packages
- Project structure
- Database status

### sbdk completion

Generate shell completion:

```bash
# Bash
sbdk completion bash >> ~/.bashrc

# Zsh
sbdk completion zsh >> ~/.zshrc

# Fish
sbdk completion fish > ~/.config/fish/completions/sbdk.fish

# PowerShell
sbdk completion powershell >> $PROFILE
```

## Data Generation

### Pipeline Files

Each pipeline file in `pipelines/` generates data:

#### users.py

Generates user demographic data:

```python
@dlt.resource
def users_pipeline():
    """Generate synthetic user data"""
    for i in range(10000):
        yield {
            "user_id": i + 1,
            "email": fake.unique.email(),
            "name": fake.name(),
            "age": random.randint(18, 80),
            "country": fake.country(),
            "created_at": fake.date_time_between(
                start_date="-2y", end_date="now"
            ),
        }
```

#### events.py

Generates user activity events:

```python
@dlt.resource
def events_pipeline():
    """Generate user interaction events"""
    for i in range(50000):
        yield {
            "event_id": i + 1,
            "user_id": random.randint(1, 10000),
            "event_type": random.choice([
                "page_view", "click", "purchase", "signup"
            ]),
            "timestamp": fake.date_time_between(
                start_date="-1y", end_date="now"
            ),
        }
```

#### orders.py

Generates e-commerce order data:

```python
@dlt.resource
def orders_pipeline():
    """Generate order transaction data"""
    for i in range(25000):
        yield {
            "order_id": i + 1,
            "user_id": random.randint(1, 10000),
            "product_name": fake.word(),
            "amount": round(random.uniform(10, 1000), 2),
            "status": random.choice(["pending", "completed", "cancelled"]),
            "order_date": fake.date_time_between(
                start_date="-1y", end_date="now"
            ),
        }
```

### Customizing Data Generation

1. **Edit pipeline files** to change data structure
2. **Adjust row counts** in the loops
3. **Add new pipelines** by creating new `.py` files in `pipelines/`
4. **Modify fake data** using [Faker](https://faker.readthedocs.io/) methods

## Data Transformations

### dbt Models

SBDK uses dbt for SQL-based transformations:

#### Staging Models (`staging/`)

Clean and standardize raw data:

```sql
-- stg_users.sql
SELECT
    user_id,
    LOWER(email) AS email,
    name,
    age,
    CASE
        WHEN age < 25 THEN '18-24'
        WHEN age < 35 THEN '25-34'
        WHEN age < 50 THEN '35-49'
        ELSE '50+'
    END AS age_group,
    country,
    created_at
FROM {{ source('raw', 'users') }}
```

#### Intermediate Models (`intermediate/`)

Business logic and joins:

```sql
-- int_user_activity.sql
SELECT
    u.user_id,
    u.email,
    COUNT(DISTINCT e.event_id) AS total_events,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.amount) AS total_spent
FROM {{ ref('stg_users') }} u
LEFT JOIN {{ ref('stg_events') }} e ON u.user_id = e.user_id
LEFT JOIN {{ ref('stg_orders') }} o ON u.user_id = o.user_id
GROUP BY u.user_id, u.email
```

#### Mart Models (`marts/`)

Analytics-ready aggregations:

```sql
-- user_metrics.sql
SELECT
    u.user_id,
    u.age_group,
    u.country,
    ua.total_events,
    ua.total_orders,
    ua.total_spent,
    ROUND(ua.total_spent / NULLIF(ua.total_orders, 0), 2) AS avg_order_value
FROM {{ ref('stg_users') }} u
LEFT JOIN {{ ref('int_user_activity') }} ua ON u.user_id = ua.user_id
```

### Running Transformations

```bash
# Run all transformations
sbdk run --dbt-only

# Or use dbt directly
cd dbt
dbt run
dbt test
dbt docs generate
```

## Querying Data

### Using sbdk query

```bash
# Simple query
sbdk query "SELECT COUNT(*) FROM stg_users"

# Aggregation
sbdk query "
SELECT
    age_group,
    COUNT(*) as users,
    AVG(total_spent) as avg_spent
FROM user_metrics
GROUP BY age_group
"

# Joins
sbdk query "
SELECT
    u.name,
    COUNT(o.order_id) as order_count
FROM stg_users u
LEFT JOIN stg_orders o ON u.user_id = o.user_id
GROUP BY u.name
ORDER BY order_count DESC
LIMIT 10
"
```

### Using query.py Helper

The included `query.py` script provides additional features:

```bash
# Show all tables
python query.py

# Run query
python query.py "SELECT * FROM stg_users LIMIT 5"

# Interactive mode
python query.py --interactive

# Execute query from file
python query.py --file my_query.sql

# Output as JSON
python query.py --format json "SELECT * FROM stg_users LIMIT 5"
```

### Using DuckDB CLI (Optional)

Install DuckDB CLI for the best experience:

```bash
# macOS
brew install duckdb

# Or download from https://duckdb.org/

# Connect to database
duckdb data/my_project.duckdb

# Run queries
SELECT * FROM stg_users LIMIT 10;
.tables
.schema stg_users
.mode markdown
```

## Configuration

### sbdk_config.json

Project configuration file:

```json
{
  "project": "my_project",
  "database": "data/my_project.duckdb",
  "dbt_project": "dbt",
  "pipelines_dir": "pipelines",
  "log_level": "INFO"
}
```

### Environment Variables

```bash
# Override database path
export SBDK_DATABASE="custom_path/db.duckdb"

# Set log level
export SBDK_LOG_LEVEL="DEBUG"

# Custom project directory
export SBDK_PROJECT_DIR="/path/to/project"
```

## Advanced Usage

### Custom Pipeline Development

Create new pipeline in `pipelines/new_data.py`:

```python
import dlt
from faker import Faker
import random

fake = Faker()

@dlt.resource
def new_data_pipeline():
    """Custom data generation"""
    for i in range(1000):
        yield {
            "id": i + 1,
            "custom_field": fake.word(),
            "value": random.randint(1, 100),
        }

if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="new_data",
        destination="duckdb",
        dataset_name="raw"
    )
    load_info = pipeline.run(new_data_pipeline())
    print(load_info)
```

### Testing Transformations

```bash
# Navigate to dbt directory
cd dbt

# Run specific model
dbt run --select stg_users

# Run and test
dbt run && dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### Performance Optimization

```bash
# Use DuckDB's COPY for large datasets
sbdk query "
COPY (SELECT * FROM stg_users)
TO 'export/users.parquet' (FORMAT PARQUET)
"

# Create indexes
sbdk query "
CREATE INDEX idx_user_id ON stg_users(user_id)
"

# Analyze query performance
sbdk query "EXPLAIN SELECT * FROM user_metrics"
```

### Integration with Other Tools

#### Export to CSV

```bash
sbdk query "
COPY (SELECT * FROM user_metrics)
TO 'export/metrics.csv' (FORMAT CSV, HEADER TRUE)
"
```

#### Export to Parquet

```bash
sbdk query "
COPY (SELECT * FROM user_metrics)
TO 'export/metrics.parquet' (FORMAT PARQUET)
"
```

#### Import External Data

```bash
sbdk query "
CREATE TABLE external_data AS
SELECT * FROM read_csv_auto('path/to/file.csv')
"
```

## Best Practices

1. **Version Control**: Commit pipeline and dbt files, not data
2. **Testing**: Add dbt tests for data quality
3. **Documentation**: Document models in dbt YAML files
4. **Modular Design**: One responsibility per pipeline/model
5. **Naming Conventions**: `stg_*` for staging, `int_*` for intermediate, `dim_*`/`fact_*` for marts

---

**Next**: See [Developer Guide](DEVELOPER_GUIDE.md) for contributing →
