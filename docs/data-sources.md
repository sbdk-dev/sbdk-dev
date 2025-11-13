# SBDK Data Sources Guide

## Overview

SBDK provides a unified interface for connecting to various data sources including databases, files, and APIs. This guide covers everything you need to know about adding, configuring, and syncing data sources in your SBDK projects.

**Key Features:**
- ✅ Multiple connector types (CSV, JSON, Parquet, PostgreSQL, MySQL, etc.)
- ✅ Flexible sampling strategies for different use cases
- ✅ Automatic schema detection
- ✅ Simple CLI and Python API
- ✅ Context-aware connection management
- ✅ Built-in error handling and diagnostics

---

## Quick Start

### Adding Your First Data Source

#### 1. CSV/File Source (Simplest)

```bash
# Add a local CSV file
sbdk source add users --type csv --file ./data/users.csv

# Verify the connection
sbdk source test users
```

#### 2. PostgreSQL Source (Database)

```bash
# Add a PostgreSQL connection
sbdk source add my_postgres \
  --type postgres \
  --host localhost \
  --port 5432 \
  --database mydb \
  --username user \
  --password secret

# Test the connection
sbdk source test my_postgres
```

#### 3. List and View Sources

```bash
# View all configured sources
sbdk source list

# See detailed information about a specific source
sbdk source info users

# Check the detected schema
sbdk source schema users
```

#### 4. Sync Data

```bash
# Sync a single source
sbdk source sync users

# Sync all sources
sbdk source sync --all

# Sync with sampling (only first 1000 rows)
sbdk source sync users --strategy limit --limit 1000
```

---

## Available Connectors

### CSV/File Connector

The CSV connector loads data from local files including CSV, JSON, and Parquet formats.

**Supported Formats:**
- CSV (comma, semicolon, tab separated)
- JSON (line-delimited and array formats)
- Parquet (Apache Parquet binary format)

#### Configuration

```bash
sbdk source add my_csv \
  --type csv \
  --file ./data/customers.csv \
  --delimiter "," \
  --encoding "utf-8" \
  --sample-size 1000
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--file` | Path to the file | Required |
| `--delimiter` | Column delimiter (CSV only) | `,` |
| `--encoding` | File encoding | `utf-8` |
| `--header` | Has header row (CSV only) | `true` |
| `--sample-size` | Rows to sample for schema detection | `1000` |

#### Python API Usage

```python
from sbdk.sources import CSVConnector, SourceConnectionConfig, SourceType
from pathlib import Path

# Create configuration
config = SourceConnectionConfig(
    name="users",
    source_type=SourceType.FILE,
    description="User demographics"
)

# Create connector
connector = CSVConnector(config, file_path="data/users.csv")

# Connect and fetch data
with connector:
    # Get all data
    for row in connector.fetch_data():
        print(row)

    # Get schema
    schema = connector.detect_schema()
    print(schema.columns)
```

#### Example: Load CSV with Different Formats

```bash
# Semicolon-separated values (European format)
sbdk source add products \
  --type csv \
  --file ./data/products.csv \
  --delimiter ";"

# Tab-separated values
sbdk source add events \
  --type csv \
  --file ./data/events.tsv \
  --delimiter "\t"

# JSON Lines format (one JSON object per line)
sbdk source add logs \
  --type csv \
  --file ./data/logs.jsonl

# Apache Parquet
sbdk source add analytics \
  --type csv \
  --file ./data/analytics.parquet
```

---

### PostgreSQL Connector

Connect to PostgreSQL databases for live data access.

#### Basic Configuration

```bash
sbdk source add production_db \
  --type postgres \
  --host db.example.com \
  --port 5432 \
  --database analytics \
  --username analyst \
  --password yourpassword
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Database hostname | Required |
| `--port` | Database port | `5432` |
| `--database` | Database name | Required |
| `--username` | Database user | Required |
| `--password` | Database password | Required |
| `--schema` | PostgreSQL schema | `public` |
| `--timeout` | Connection timeout (seconds) | `30` |
| `--ssl` | Use SSL connection | `false` |

#### Authentication Methods

**1. Password Authentication (Simplest)**
```bash
sbdk source add mydb \
  --type postgres \
  --host localhost \
  --database mydb \
  --username postgres \
  --password mypassword
```

**2. Environment Variable**
```bash
# Set password in environment
export SBDK_POSTGRES_PASSWORD="mypassword"

sbdk source add mydb \
  --type postgres \
  --host localhost \
  --database mydb \
  --username postgres
```

**3. .pgpass File (Recommended for Production)**
```bash
# Create ~/.pgpass
echo "localhost:5432:mydb:postgres:mypassword" >> ~/.pgpass
chmod 600 ~/.pgpass

# Now password is not needed
sbdk source add mydb \
  --type postgres \
  --host localhost \
  --database mydb \
  --username postgres
```

#### Python API Usage

```python
from sbdk.sources.base import (
    SourceConnectionConfig,
    SourceType,
    SamplingConfig,
    SamplingStrategy
)
from sbdk.sources.connectors import PostgreSQLConnector

# Configure connection
config = SourceConnectionConfig(
    name="production_db",
    source_type=SourceType.DATABASE,
    description="Production analytics database",
    metadata={
        "host": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "analyst",
        "schema": "public"
    }
)

# Create connector with password
connector = PostgreSQLConnector(
    config,
    password="yourpassword"
)

# Use connector
with connector:
    # Test connection
    if connector.test_connection():
        print("Connected!")

    # List available tables
    tables = connector.list_tables()
    print(f"Available tables: {tables}")

    # Fetch data from table
    for row in connector.fetch_data(table="users"):
        print(row)

    # Execute custom query
    for row in connector.execute_query("SELECT * FROM users WHERE status='active'"):
        print(row)

    # Detect schema
    schema = connector.detect_schema(table_name="users")
    print(f"Columns: {schema.columns}")
```

#### Query Examples

```python
# Simple table fetch
connector = PostgreSQLConnector(config, password="secret")
with connector:
    users = list(connector.fetch_data(table="users"))
    print(f"Total users: {len(users)}")

# Complex query
query = """
SELECT
    u.user_id,
    u.email,
    COUNT(o.order_id) as order_count,
    SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.created_at >= '2024-01-01'
GROUP BY u.user_id, u.email
"""

with connector:
    for row in connector.execute_query(query):
        print(row)

# Parameterized queries (prepared statements)
with connector:
    query = "SELECT * FROM users WHERE email = %s"
    for row in connector.execute_query(query, ("john@example.com",)):
        print(row)
```

---

### MySQL Connector

Connect to MySQL/MariaDB databases.

#### Configuration

```bash
sbdk source add mysql_db \
  --type mysql \
  --host db.example.com \
  --port 3306 \
  --database mydb \
  --username root \
  --password secret
```

#### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Database hostname | Required |
| `--port` | Database port | `3306` |
| `--database` | Database name | Required |
| `--username` | Database user | Required |
| `--password` | Database password | Required |
| `--charset` | Character set | `utf8mb4` |

#### Python Example

```python
from sbdk.sources.base import SourceConnectionConfig, SourceType
from sbdk.sources.connectors import MySQLConnector

config = SourceConnectionConfig(
    name="mysql_db",
    source_type=SourceType.DATABASE,
    metadata={
        "host": "localhost",
        "port": 3306,
        "database": "mydb",
        "username": "root",
        "charset": "utf8mb4"
    }
)

with MySQLConnector(config, password="secret") as connector:
    # List tables
    tables = connector.list_tables()

    # Fetch data
    for row in connector.fetch_data(table="products"):
        print(row)
```

---

## Sampling Strategies

SBDK provides flexible sampling strategies for different use cases. Choose the strategy that best fits your needs.

### Overview of Strategies

| Strategy | Use Case | Example | Memory |
|----------|----------|---------|--------|
| **FULL** | Need all data | Analytics on complete dataset | High |
| **LIMIT** | First N rows | Quick preview, schema detection | Low |
| **PERCENTAGE** | Random sample | Testing on subset (10%, 50%) | Medium |
| **RANDOM** | Reproducible sample | Testing with seed for consistency | Medium |
| **INTELLIGENT** | Distribution-aware | Smart sampling based on data | Medium |

### 1. FULL Strategy

Load all available data. Best for small to medium datasets.

```bash
# CLI
sbdk source sync users --strategy full

# Suitable for <1GB datasets
```

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

config = SamplingConfig(strategy=SamplingStrategy.FULL)
for row in connector.get_sample(config):
    print(row)
```

**When to use:**
- Complete analysis required
- Small datasets (<1GB)
- No performance constraints

---

### 2. LIMIT Strategy

Load first N rows. Best for quick previews and schema detection.

```bash
# CLI: Load first 1000 rows
sbdk source sync users --strategy limit --limit 1000

# Load first 100 rows
sbdk source sync users --strategy limit --limit 100
```

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

# Sample first 500 rows
config = SamplingConfig(
    strategy=SamplingStrategy.LIMIT,
    limit=500
)

for row in connector.get_sample(config):
    print(row)
```

**When to use:**
- Schema discovery
- Data preview
- Quick validation
- Memory constraints

---

### 3. PERCENTAGE Strategy

Random sample by percentage. Best for large datasets needing representative samples.

```bash
# CLI: Sample 10% of data
sbdk source sync orders --strategy percentage --percentage 10

# Sample 5% of data
sbdk source sync orders --strategy percentage --percentage 5
```

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

# Sample 15% of rows
config = SamplingConfig(
    strategy=SamplingStrategy.PERCENTAGE,
    percentage=15
)

for row in connector.get_sample(config):
    print(row)
```

**When to use:**
- Large datasets (>1GB)
- Representative samples needed
- Statistical analysis
- Performance testing

---

### 4. RANDOM Strategy

Reproducible random sampling using a seed. Best for testing with consistent results.

```bash
# CLI: Random 20% with seed for reproducibility
sbdk source sync events --strategy random --percentage 20 --seed 42

# Same seed = same sample
sbdk source sync events --strategy random --percentage 20 --seed 42
```

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

# Reproducible 25% sample
config = SamplingConfig(
    strategy=SamplingStrategy.RANDOM,
    percentage=25,
    seed=12345
)

# Multiple runs with same seed produce identical samples
for run in range(3):
    sample = list(connector.get_sample(config))
    print(f"Run {run}: {len(sample)} rows")  # Always same count
```

**When to use:**
- Reproducible testing
- Consistent development samples
- Comparing algorithm versions
- CI/CD pipelines

---

### 5. INTELLIGENT Strategy

Smart sampling based on data distribution. Best for balanced representation.

```bash
# CLI
sbdk source sync products --strategy intelligent

# Automatically determines best sampling approach
```

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

config = SamplingConfig(strategy=SamplingStrategy.INTELLIGENT)

for row in connector.get_sample(config):
    print(row)
```

**When to use:**
- Unknown data distribution
- Need balanced representation
- Automated testing
- AI/ML preprocessing

---

## CLI Commands

### sbdk source add

Add a new data source.

```bash
# CSV file
sbdk source add <name> --type csv --file <path>

# PostgreSQL database
sbdk source add <name> \
  --type postgres \
  --host <host> \
  --port <port> \
  --database <db> \
  --username <user> \
  --password <pass>

# MySQL database
sbdk source add <name> \
  --type mysql \
  --host <host> \
  --port <port> \
  --database <db> \
  --username <user> \
  --password <pass>

# With sampling configuration
sbdk source add <name> \
  --type csv \
  --file <path> \
  --sampling-strategy limit \
  --sampling-limit 5000
```

**Options:**
- `--type` (required): Source type (csv, postgres, mysql)
- `--description`: Source description
- `--sampling-strategy`: Default sampling strategy
- `--sampling-limit`: Default limit for LIMIT strategy
- `--sampling-percentage`: Default percentage for PERCENTAGE strategy

---

### sbdk source list

List all configured sources.

```bash
# Show all sources
sbdk source list

# Output:
# Name          Type       Status     Description
# users         csv        ready      User demographics
# products      csv        ready      Product catalog
# my_postgres   postgres   connected  Production database

# JSON format for automation
sbdk source list --format json
```

---

### sbdk source info

Show detailed information about a source.

```bash
# Get source details
sbdk source info users

# Output:
# Name:          users
# Type:          csv
# File:          data/users.csv
# Status:        ready
# Sampling:      LIMIT 1000
# Row Count:     150,000
# Detected:      2025-01-15 10:30:45 UTC
```

---

### sbdk source schema

Detect and display source schema.

```bash
# Auto-detect schema
sbdk source schema users

# Output:
# Table: users
# Columns:
#   user_id         INTEGER       NOT NULL
#   email          VARCHAR(255)  NOT NULL
#   first_name     VARCHAR(100)
#   last_name      VARCHAR(100)
#   signup_date    DATE
#   status         VARCHAR(20)   DEFAULT 'active'

# JSON output for automation
sbdk source schema users --format json

# Specific table (for databases)
sbdk source schema my_postgres --table users
```

---

### sbdk source sync

Sync data from a source to local storage.

```bash
# Sync single source
sbdk source sync users

# Sync all sources
sbdk source sync --all

# Sync with specific strategy
sbdk source sync users --strategy limit --limit 5000

# Sync with percentage sampling
sbdk source sync orders --strategy percentage --percentage 10

# Sync with reproducible random sample
sbdk source sync events --strategy random --percentage 20 --seed 42

# Quiet mode (no progress output)
sbdk source sync users --quiet

# Force re-sync (overwrite existing)
sbdk source sync users --force
```

**Output:**
```
Syncing: users                                            [████████████] 100%

Synced 150,000 rows in 2.45s
Rows/sec: 61,224
Status: ✅ Complete
```

---

### sbdk source test

Test connectivity to a source.

```bash
# Test single source
sbdk source test users

# Output:
# Testing source: users
# File: data/users.csv
# File exists: ✅
# Readable: ✅
# Schema detectable: ✅
# Status: ✅ Ready

# Test with verbose output
sbdk source test users --verbose

# Test all sources
sbdk source test --all
```

---

### sbdk source remove

Remove a data source configuration.

```bash
# Remove source
sbdk source remove users

# Confirm before removal
sbdk source remove users --confirm

# Remove without confirmation
sbdk source remove users --force
```

---

### sbdk source sync-all

Convenience command to sync all configured sources.

```bash
# Sync all sources
sbdk source sync-all

# Sync all with specific strategy
sbdk source sync-all --strategy percentage --percentage 10

# Sync with parallel processing (faster)
sbdk source sync-all --parallel --workers 4
```

---

## API Usage

### Python API Examples

#### Basic Connection and Data Fetching

```python
from sbdk.sources import (
    CSVConnector,
    SourceConnectionConfig,
    SourceType,
    SamplingConfig,
    SamplingStrategy
)

# Create configuration
config = SourceConnectionConfig(
    name="users",
    source_type=SourceType.FILE,
    description="User data"
)

# Create and use connector
connector = CSVConnector(config, file_path="data/users.csv")

with connector:
    # Fetch all data
    all_rows = list(connector.fetch_data())
    print(f"Total rows: {len(all_rows)}")

    # Detect schema
    schema = connector.detect_schema()
    print(f"Columns: {[col['name'] for col in schema.columns]}")

    # Get sample
    sample = list(connector.get_sample(
        SamplingConfig(
            strategy=SamplingStrategy.LIMIT,
            limit=10
        )
    ))
    print(f"Sample (first 10): {sample}")
```

#### Database Queries

```python
from sbdk.sources.base import SourceConnectionConfig, SourceType

# PostgreSQL example
config = SourceConnectionConfig(
    name="analytics_db",
    source_type=SourceType.DATABASE,
    metadata={
        "host": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "analyst",
        "schema": "public"
    }
)

from sbdk.sources.connectors import PostgreSQLConnector

connector = PostgreSQLConnector(config, password="secret")

with connector:
    # List tables
    tables = connector.list_tables()
    print(f"Tables: {tables}")

    # Fetch from specific table
    users = list(connector.fetch_data(table="users"))

    # Execute complex query
    query = """
    SELECT
        DATE_TRUNC('day', created_at) as date,
        COUNT(*) as event_count,
        AVG(amount) as avg_amount
    FROM events
    GROUP BY DATE_TRUNC('day', created_at)
    ORDER BY date DESC
    LIMIT 30
    """

    results = list(connector.execute_query(query))
    for row in results:
        print(row)
```

#### Sampling Examples

```python
from sbdk.sources import SamplingConfig, SamplingStrategy

connector = CSVConnector(config, file_path="data/large_file.csv")

with connector:
    # Strategy 1: Full data (small files)
    full_sample = list(connector.get_sample(
        SamplingConfig(strategy=SamplingStrategy.FULL)
    ))

    # Strategy 2: First 1000 rows (quick preview)
    preview = list(connector.get_sample(
        SamplingConfig(
            strategy=SamplingStrategy.LIMIT,
            limit=1000
        )
    ))

    # Strategy 3: Random 10% (large files)
    random_sample = list(connector.get_sample(
        SamplingConfig(
            strategy=SamplingStrategy.PERCENTAGE,
            percentage=10
        )
    ))

    # Strategy 4: Reproducible 25% (testing)
    reproducible = list(connector.get_sample(
        SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            percentage=25,
            seed=42
        )
    ))

    # Strategy 5: Intelligent sampling
    smart_sample = list(connector.get_sample(
        SamplingConfig(strategy=SamplingStrategy.INTELLIGENT)
    ))
```

#### Batch Processing

```python
# Process large files in chunks
from sbdk.sources import SamplingConfig, SamplingStrategy

def process_in_batches(connector, batch_size=1000):
    """Process data in memory-efficient batches."""
    batch = []
    for row in connector.fetch_data():
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

with connector:
    for batch_num, batch in enumerate(process_in_batches(connector), 1):
        print(f"Processing batch {batch_num}: {len(batch)} rows")
        # Process batch
        for row in batch:
            # Your logic here
            pass
```

---

## Schema Detection

SBDK automatically detects the schema of data sources.

### CSV Schema Detection

```python
from sbdk.sources import CSVConnector, SourceConnectionConfig, SourceType

config = SourceConnectionConfig(
    name="users",
    source_type=SourceType.FILE
)

connector = CSVConnector(config, file_path="data/users.csv")

with connector:
    schema = connector.detect_schema()

    # Access schema information
    print(f"Table: {schema.table_name}")
    print(f"Columns: {len(schema.columns)}")
    print(f"Row count: {schema.row_count}")
    print(f"Detected at: {schema.detected_at}")

    # Iterate columns
    for col in schema.columns:
        print(f"  {col['name']}: {col['type']}")
```

**Auto-detected Types:**
- INTEGER, BIGINT, SMALLINT
- DECIMAL, FLOAT, DOUBLE
- VARCHAR, TEXT
- DATE, TIMESTAMP
- BOOLEAN
- JSON (for JSON columns)

---

## Troubleshooting

### Connection Errors

**Problem**: "Connection refused"

```python
# Check connection
try:
    connector.test_connection()
except ConnectionError as e:
    print(f"Connection failed: {e}")
    # Solutions:
    # 1. Verify host and port
    # 2. Check database server is running
    # 3. Verify credentials
    # 4. Check network connectivity
```

**Solution:**
```bash
# Test database connectivity directly
psql -h db.example.com -U user -d mydb -c "SELECT 1"

# Check if server is reachable
ping db.example.com
telnet db.example.com 5432

# Verify credentials
sbdk source test my_postgres --verbose
```

---

### File Not Found

**Problem**: "File not found: data/users.csv"

```python
# Check file exists
from pathlib import Path

file_path = Path("data/users.csv")
if not file_path.exists():
    print(f"File not found: {file_path.absolute()}")
    print(f"Current directory: {Path.cwd()}")
```

**Solution:**
```bash
# Check file exists
ls -la data/users.csv

# Use absolute path
sbdk source add users \
  --type csv \
  --file /absolute/path/to/users.csv

# Or relative path from project root
sbdk source add users \
  --type csv \
  --file ./data/users.csv
```

---

### Schema Detection Issues

**Problem**: "Unable to detect schema"

**Causes:**
1. File is empty
2. File format is incorrect
3. No readable rows
4. Encoding issue

**Solutions:**
```python
# Increase sample size for better detection
config = SourceConnectionConfig(
    name="data",
    source_type=SourceType.FILE,
    metadata={"sample_size": 5000}
)

# Check file format
import csv
with open("data/file.csv") as f:
    dialect = csv.Sniffer().sniff(f.read(1024))
    print(f"Detected delimiter: {repr(dialect.delimiter)}")

# Check encoding
with open("data/file.csv", encoding='utf-8') as f:
    first_line = f.readline()
    print(first_line)
```

---

### Memory Issues

**Problem**: "MemoryError" or slow performance with large files

**Solution:** Use sampling strategies

```python
# Instead of full load
# config = SamplingConfig(strategy=SamplingStrategy.FULL)

# Use sampling
config = SamplingConfig(
    strategy=SamplingStrategy.PERCENTAGE,
    percentage=10  # 10% sample
)

for row in connector.get_sample(config):
    print(row)  # Process in streaming fashion
```

---

### Database-Specific Issues

**PostgreSQL: SSL Connection Issues**
```bash
# Disable SSL
sbdk source add mydb \
  --type postgres \
  --host db.example.com \
  --ssl false

# Or use .pgpass for auth
echo "db.example.com:5432:*:user:password" >> ~/.pgpass
chmod 600 ~/.pgpass
```

**MySQL: Character Set Issues**
```bash
# Specify character set
sbdk source add mydb \
  --type mysql \
  --host localhost \
  --charset utf8mb4

# Or use environment variable
export MYSQL_CHARSET=utf8mb4
sbdk source add mydb --type mysql --host localhost
```

---

## Best Practices

### 1. Source Configuration

**Do:**
```bash
# Meaningful names
sbdk source add production_analytics --type postgres

# Include descriptions
sbdk source add users \
  --type csv \
  --file ./data/users.csv \
  --description "User demographics from export 2025-01-15"

# Test after adding
sbdk source test production_analytics
```

**Don't:**
```bash
# Vague names
sbdk source add db1 --type postgres

# Hardcoded passwords (security issue)
sbdk source add mydb --type postgres --password "secret123"
# Use environment variables instead
```

### 2. Sampling Strategy Selection

```python
# Small datasets (<100MB) - use FULL
if file_size < 100_000_000:
    strategy = SamplingStrategy.FULL

# Large datasets - use PERCENTAGE
elif file_size < 1_000_000_000:
    strategy = SamplingStrategy.PERCENTAGE
    percentage = 10

# Very large datasets - use LIMIT
else:
    strategy = SamplingStrategy.LIMIT
    limit = 10000
```

### 3. Error Handling

```python
from sbdk.sources.base import BaseConnector
from sbdk.exceptions import SBDKError

try:
    with connector:
        schema = connector.detect_schema()
        for row in connector.fetch_data():
            process(row)
except FileNotFoundError as e:
    print(f"File not found: {e}")
    # Handle file-specific error
except ConnectionError as e:
    print(f"Connection failed: {e}")
    # Handle connection-specific error
except SBDKError as e:
    print(f"SBDK error: {e}")
    # Handle SBDK-specific error
```

### 4. Performance Optimization

```python
# Use context manager for auto-cleanup
with connector:
    # Connection automatically closed
    data = list(connector.fetch_data())

# Stream large datasets instead of loading all
for row in connector.fetch_data():
    process(row)  # Memory-efficient

# Use sampling for large files
from sbdk.sources import SamplingConfig, SamplingStrategy
config = SamplingConfig(
    strategy=SamplingStrategy.PERCENTAGE,
    percentage=1  # 1% sample
)
for row in connector.get_sample(config):
    analyze(row)
```

---

## Integration Examples

### With SBDK Pipelines

```python
# pipelines/load_external_data.py
from sbdk.sources import CSVConnector, SourceConnectionConfig, SourceType
import dlt

@dlt.resource(name="external_users")
def load_external_users():
    config = SourceConnectionConfig(
        name="users",
        source_type=SourceType.FILE
    )

    connector = CSVConnector(config, file_path="data/external_users.csv")

    with connector:
        for row in connector.fetch_data():
            yield row

# In dbt model or elsewhere
# SELECT * FROM external_users
```

### With dbt Models

```sql
-- dbt/models/staging/stg_external_users.sql
{{ config(materialized='view') }}

SELECT
    user_id,
    email,
    first_name,
    last_name,
    signup_date,
    CURRENT_TIMESTAMP as _loaded_at
FROM {{ ref('external_users') }}
WHERE status = 'active'
```

### Syncing Multiple Sources

```python
# sync_all_sources.py
from sbdk.sources import CSVConnector, SourceConnectionConfig, SourceType
from sbdk.sources.base import SamplingConfig, SamplingStrategy
import time

sources = [
    ("users", "data/users.csv"),
    ("products", "data/products.csv"),
    ("orders", "data/orders.csv"),
]

for name, file_path in sources:
    print(f"Syncing {name}...")

    config = SourceConnectionConfig(
        name=name,
        source_type=SourceType.FILE
    )

    connector = CSVConnector(config, file_path=file_path)

    with connector:
        schema = connector.detect_schema()
        row_count = schema.row_count

        for row in connector.fetch_data():
            # Load into database
            pass

        print(f"  ✅ Synced {row_count} rows")
        time.sleep(1)

print("All sources synced!")
```

---

## Advanced Topics

### Custom Connector Implementation

```python
from sbdk.sources import (
    FileConnector,
    SourceConnectionConfig,
    SchemaInfo
)
from typing import Iterator, Dict, Any
from pathlib import Path

class CustomConnector(FileConnector):
    """Custom connector for specialized format."""

    def parse_file(self) -> Iterator[Dict[str, Any]]:
        """Parse custom format."""
        with open(self.file_path) as f:
            for line in f:
                # Custom parsing logic
                yield self._parse_line(line)

    def _parse_line(self, line: str) -> Dict[str, Any]:
        # Your parsing implementation
        return {}

    def detect_schema(self, table_name=None) -> SchemaInfo:
        """Detect schema from sample."""
        columns = []

        # Read sample and infer types
        for row in self.parse_file():
            for key, value in row.items():
                # Infer column type
                pass
            break

        return SchemaInfo(
            table_name=self.config.name,
            columns=columns
        )
```

### Caching and Optimization

```python
from functools import lru_cache

class OptimizedConnector:
    def __init__(self, connector):
        self.connector = connector
        self._schema_cache = None
        self._data_cache = None

    @property
    def schema(self):
        """Cache schema detection."""
        if self._schema_cache is None:
            self._schema_cache = self.connector.detect_schema()
        return self._schema_cache

    def fetch_data(self, use_cache=False):
        """Fetch with optional caching."""
        if use_cache and self._data_cache is not None:
            return iter(self._data_cache)

        data = list(self.connector.fetch_data())

        if use_cache:
            self._data_cache = data

        return iter(data)
```

---

## Frequently Asked Questions

**Q: How do I secure database passwords?**
A: Use environment variables or .pgpass files, never hardcode passwords.

```bash
# Environment variable
export DB_PASSWORD="secret"
# Then use in code
password = os.environ.get("DB_PASSWORD")

# Or .pgpass for PostgreSQL
echo "host:port:db:user:password" >> ~/.pgpass
chmod 600 ~/.pgpass
```

**Q: Can I use sources for real-time data?**
A: SBDK sources are designed for batch ingestion. For streaming data, consider using dlt with streaming sources.

**Q: How do I handle large files efficiently?**
A: Use sampling strategies or stream processing:

```python
# Memory-efficient streaming
for row in connector.fetch_data():
    process(row)  # Process one at a time

# Or use sampling
config = SamplingConfig(
    strategy=SamplingStrategy.PERCENTAGE,
    percentage=5
)
```

**Q: Can I transform data while syncing?**
A: Yes, process in Python or use dbt after sync:

```python
# During sync
for row in connector.fetch_data():
    row['processed'] = transform(row['value'])
    yield row

# After sync in dbt
SELECT *, UPPER(email) as email_upper FROM raw_data
```

---

## Next Steps

- **[User Guide](USER_GUIDE.md)**: Learn about SBDK workflows
- **[API Reference](API_REFERENCE.md)**: Complete API documentation
- **[Configuration Guide](CONFIGURATION.md)**: Advanced configuration options
- **[DBT Guide](DBT_MODELS.md)**: Building transformations with your data

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Status**: Phase 1.2 - Data Sources Complete
