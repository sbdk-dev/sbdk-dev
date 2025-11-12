# Incremental Processing in SBDK

**Version**: 1.0
**Last Updated**: January 2025
**Status**: Phase 1.1 Implementation

---

## Overview

SBDK's incremental processing engine enables **rapid iteration cycles** (<30 seconds) by only processing new or changed data instead of full reloads. This is essential for maintaining fast feedback loops during local development while maintaining production parity.

### Key Benefits

- ⚡ **Fast Iterations**: Process only changed data, dramatically reducing run times
- 💾 **State Management**: Automatic tracking of watermarks and processing history
- 🔄 **Multiple Strategies**: Timestamp, hash-based, watermark, or full refresh
- 🎯 **Production Parity**: Same incremental patterns work in local dev and production
- 📊 **Progress Tracking**: Visibility into what data is processed each run

---

## Quick Start

### Basic Usage

```bash
# Enable incremental mode
sbdk run --incremental

# Combine with watch mode for fast iteration
sbdk run --incremental --watch

# Force full refresh (ignore incremental state)
sbdk run  # Default is full refresh
```

### Python API

```python
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig, IncrementalStrategy

# Create processor
processor = IncrementalProcessor("my_pipeline")

# Configure incremental strategy
config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="updated_at"
)

# Process data
def extract_and_load():
    # Get last watermark
    last_value = processor.get_last_watermark(config)

    # Extract data since last watermark
    query = f"SELECT * FROM source WHERE updated_at > '{last_value}'"
    data = fetch_data(query)

    # Load data
    load_to_warehouse(data)

    # Return new watermark
    return {
        "records_processed": len(data),
        "max_timestamp": max(r["updated_at"] for r in data)
    }

# Execute with automatic state tracking
result = processor.process(
    extract_and_load,
    config,
    extract_watermark=lambda r: r["max_timestamp"]
)

print(f"Processed {result['records_processed']} records")
```

---

## Incremental Strategies

SBDK supports four incremental strategies, each optimized for different use cases:

### 1. Timestamp-Based (Recommended)

**Best for**: Event logs, audit trails, time-series data

Uses a timestamp column to track which records have been processed.

```python
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig, IncrementalStrategy

processor = IncrementalProcessor("events_pipeline")

config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="created_at",
    mode=IncrementalMode.APPEND
)

# Get SQL filter for incremental query
filter_sql = processor.build_incremental_filter(config)
# Returns: "created_at > '2025-01-01T00:00:00'"

# Use in your query
query = f"SELECT * FROM events WHERE {filter_sql}"
```

**Advantages**:
- Simple and efficient
- Works with any database
- Fast queries with indexed timestamp columns
- Natural fit for append-only data

**Considerations**:
- Requires reliable timestamp column
- Assumes timestamps are monotonically increasing
- May miss records with backdated timestamps

### 2. Hash-Based (Change Detection)

**Best for**: Slowly changing dimensions, product catalogs, user profiles

Detects changes by computing content hashes of records.

```python
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig, IncrementalStrategy

processor = IncrementalProcessor("products_pipeline")

config = IncrementalConfig(
    strategy=IncrementalStrategy.HASH,
    unique_key="product_id",
    check_columns=["name", "price", "description"],  # Columns to monitor
    mode=IncrementalMode.MERGE
)

# Simulate data processing
products = fetch_all_products()  # Fetch all products

# Load previous hashes
previous_hashes = load_previous_hashes()  # Your implementation

# Filter only changed products
changed_products = processor.filter_changed_rows(
    products,
    config,
    previous_hashes
)

print(f"Detected {len(changed_products)} changed products")
```

**Advantages**:
- Detects any content changes
- Works without timestamp columns
- Can monitor specific columns
- Perfect for slowly changing dimensions

**Considerations**:
- Requires fetching all records (or recent subset)
- More compute-intensive than timestamp
- Needs persistent hash storage

### 3. Watermark-Based (Generic)

**Best for**: Sequence numbers, version columns, custom ordering

Uses any sequential column for incremental tracking.

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.WATERMARK,
    watermark_column="sequence_id",
    mode=IncrementalMode.APPEND
)

# Works with any sequential column
# - sequence_id (auto-increment)
# - version_number
# - batch_id
# - transaction_id
```

**Advantages**:
- Flexible - works with any sequential column
- No timestamp dependencies
- Efficient for ordered data

**Considerations**:
- Requires sequential ordering
- Column must be monotonically increasing

### 4. Full Refresh

**Best for**: Small datasets, development testing, forced rebuilds

Processes all data on every run, ignoring incremental state.

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.FULL
)

# No incremental filtering applied
# All data processed on every run
```

**Use cases**:
- Initial development and testing
- Small reference tables
- Forced data rebuilds
- Validating incremental logic

---

## Processing Modes

Choose how to handle incremental data:

### APPEND (Default)

Add new records without updating existing ones.

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="created_at",
    mode=IncrementalMode.APPEND
)
```

**Use when**:
- Data is append-only (events, logs)
- Records never change after creation
- Performance is critical

### MERGE (Upsert)

Update existing records and insert new ones.

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.HASH,
    unique_key=["user_id"],
    mode=IncrementalMode.MERGE
)
```

**Use when**:
- Records can change over time
- Need to maintain latest state
- Implementing slowly changing dimensions

### DELETE_INSERT

Delete existing records and insert updated ones.

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="updated_at",
    unique_key="order_id",
    mode=IncrementalMode.DELETE_INSERT
)
```

**Use when**:
- Need clean replacement of records
- Merge is complex or unsupported
- Guaranteed data consistency required

---

## State Management

SBDK automatically manages incremental state in `.sbdk/state/`:

### State Directory Structure

```
.sbdk/state/
├── users_pipeline/
│   ├── current.json          # Current state
│   └── history/
│       ├── run-123.json      # Historical run 1
│       ├── run-456.json      # Historical run 2
│       └── run-789.json      # Historical run 3
└── orders_pipeline/
    ├── current.json
    └── history/
        └── ...
```

### State Contents

```json
{
  "pipeline_name": "users_pipeline",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-01-15T10:00:00",
  "completed_at": "2025-01-15T10:00:30",
  "status": "completed",
  "incremental": {
    "strategy": "timestamp",
    "last_value": "2025-01-15T09:59:50",
    "last_updated": "2025-01-15T10:00:30",
    "records_processed": 1250,
    "metadata": {}
  },
  "metrics": {
    "records_processed": 1250,
    "duration_seconds": 30
  },
  "errors": [],
  "config_hash": "a1b2c3d4..."
}
```

### Accessing State

```python
from sbdk.pipeline import IncrementalProcessor

processor = IncrementalProcessor("my_pipeline")

# Get current state
state = processor.get_state()
if state:
    print(f"Last run: {state.completed_at}")
    print(f"Records processed: {state.incremental.records_processed}")

# Get run history
history = processor.get_history(limit=10)
for run in history:
    print(f"{run.run_id}: {run.status} - {run.metrics}")

# Reset state (force full refresh)
processor.reset_state(include_history=False)
```

---

## Integration Patterns

### DLT Integration

```python
import dlt
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig, IncrementalStrategy

processor = IncrementalProcessor("dlt_users")

config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="updated_at"
)

@dlt.resource
def users_incremental():
    """Load users incrementally."""
    last_value = processor.get_last_watermark(config)

    # Query with incremental filter
    query = f"""
        SELECT * FROM users
        WHERE updated_at > '{last_value or '1970-01-01'}'
    """

    data = fetch_from_source(query)

    # Track new watermark
    if data:
        new_watermark = max(r["updated_at"] for r in data)
        processor.complete_run(new_watermark, len(data))

    return data

# Run DLT pipeline
pipeline = dlt.pipeline(
    pipeline_name="users_pipeline",
    destination="duckdb",
    dataset_name="staging"
)

pipeline.run(users_incremental())
```

### dbt Integration

SBDK incremental processing complements dbt's incremental models:

```sql
-- dbt/models/marts/users_incremental.sql
{{
    config(
        materialized='incremental',
        unique_key='user_id',
        on_schema_change='fail'
    )
}}

SELECT
    user_id,
    email,
    created_at,
    updated_at
FROM {{ ref('stg_users') }}

{% if is_incremental() %}
    -- dbt handles incremental logic
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

**Best Practice**: Use SBDK for source data extraction, dbt for transformations.

### Custom Pipeline Integration

```python
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig, IncrementalStrategy

def my_custom_pipeline():
    """Custom pipeline with incremental processing."""

    processor = IncrementalProcessor("custom_pipeline")

    config = IncrementalConfig(
        strategy=IncrementalStrategy.TIMESTAMP,
        watermark_column="event_time"
    )

    def process_data():
        # Start the run
        state = processor.start_run(config)

        try:
            # Get last watermark
            last_value = processor.get_last_watermark(config)

            # Extract data
            data = extract_data(since=last_value)

            # Transform data
            transformed = transform_data(data)

            # Load data
            load_data(transformed)

            # Calculate new watermark
            new_watermark = max(r["event_time"] for r in data)

            # Complete run
            processor.complete_run(
                new_watermark,
                len(data),
                metrics={"rows_transformed": len(transformed)}
            )

        except Exception as e:
            processor.fail_run(str(e))
            raise

    return processor.process(process_data, config)
```

---

## Advanced Usage

### Composite Keys

For multi-column unique keys:

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.HASH,
    unique_key=["user_id", "product_id", "date"],
    check_columns=["quantity", "price"]
)
```

### Custom State Directory

```python
from pathlib import Path

processor = IncrementalProcessor(
    "my_pipeline",
    state_dir=Path("/custom/state/location")
)
```

### Force Full Refresh

```python
config = IncrementalConfig(
    strategy=IncrementalStrategy.TIMESTAMP,
    watermark_column="updated_at",
    force_full_refresh=True  # Ignore previous state
)
```

### Configuration Change Detection

SBDK detects when pipeline configuration changes:

```python
pipeline_config = {
    "source": "postgres",
    "batch_size": 1000,
    "filters": ["active=true"]
}

# Config hash is automatically tracked
state = processor.start_run(config, pipeline_config)

# Check if config changed
changed = processor.state_manager.has_config_changed(
    "my_pipeline",
    pipeline_config
)

if changed:
    print("Pipeline configuration changed - consider full refresh")
```

---

## Best Practices

### 1. Choose the Right Strategy

| Data Type | Recommended Strategy | Reason |
|-----------|---------------------|---------|
| Event logs | TIMESTAMP | Append-only, time-ordered |
| User profiles | HASH | Changes need detection |
| Transactions | TIMESTAMP | Natural time ordering |
| Product catalog | HASH | Slow-changing dimensions |
| Reference data | FULL | Small, rarely changes |

### 2. Index Watermark Columns

```sql
-- Ensure fast incremental queries
CREATE INDEX idx_users_updated_at ON users(updated_at);
CREATE INDEX idx_events_created_at ON events(created_at);
```

### 3. Handle Null Watermarks

```python
last_value = processor.get_last_watermark(config)
query = f"""
    SELECT * FROM source
    WHERE updated_at > '{last_value or '1970-01-01T00:00:00'}'
"""
```

### 4. Monitor State Size

```python
history = processor.get_history(limit=100)
if len(history) > 50:
    # Clean up old history
    processor.reset_state(include_history=True)
```

### 5. Test Incremental Logic

```python
import pytest
from sbdk.pipeline import IncrementalProcessor, IncrementalConfig

def test_incremental_processing(tmp_path):
    """Test incremental pipeline logic."""

    processor = IncrementalProcessor("test_pipeline", tmp_path / "state")

    config = IncrementalConfig(
        strategy=IncrementalStrategy.TIMESTAMP,
        watermark_column="created_at"
    )

    # Run 1: Initial load
    def run1():
        return {"records_processed": 100, "max_timestamp": "2025-01-01T00:00:00"}

    result1 = processor.process(
        run1,
        config,
        extract_watermark=lambda r: r["max_timestamp"]
    )

    assert result1["records_processed"] == 100

    # Run 2: Incremental load
    processor2 = IncrementalProcessor("test_pipeline", tmp_path / "state")
    last_value = processor2.get_last_watermark(config)

    assert last_value == "2025-01-01T00:00:00"
```

### 6. Handle Late-Arriving Data

For timestamp-based strategies, consider a lookback window:

```python
last_value = processor.get_last_watermark(config)

# Lookback 1 hour to catch late arrivals
if last_value:
    from datetime import datetime, timedelta
    dt = datetime.fromisoformat(last_value)
    lookback_dt = dt - timedelta(hours=1)
    last_value = lookback_dt.isoformat()

query = f"SELECT * FROM source WHERE updated_at > '{last_value}'"
```

---

## Troubleshooting

### Issue: Incremental state not updating

**Symptoms**: Same data processed repeatedly

**Solution**:
```python
# Check if state is being saved
state = processor.get_state()
print(f"Last value: {state.incremental.last_value}")

# Verify watermark extraction
result = processor.process(
    data_fn,
    config,
    extract_watermark=lambda r: r["max_timestamp"]  # Ensure this returns correct value
)
```

### Issue: Missing data in incremental runs

**Symptoms**: Gaps in processed data

**Solutions**:
1. Check for null timestamps:
   ```sql
   SELECT COUNT(*) FROM source WHERE updated_at IS NULL
   ```

2. Verify timestamp timezone consistency

3. Use lookback window for late arrivals

4. Force full refresh and compare:
   ```python
   config.force_full_refresh = True
   ```

### Issue: Performance degradation

**Symptoms**: Incremental runs getting slower

**Solutions**:
1. Check index on watermark column
2. Analyze query plan
3. Consider partitioning strategy
4. Review state file size

### Issue: State file corruption

**Symptoms**: `ValidationError: Corrupted state file`

**Solution**:
```bash
# Delete corrupted state
rm .sbdk/state/my_pipeline/current.json

# Or reset in Python
processor.reset_state(include_history=True)
```

---

## Performance Benchmarks

### Typical Iteration Times

| Dataset Size | Full Refresh | Incremental (1% new) |
|--------------|--------------|----------------------|
| 1K rows      | 2s          | 0.5s                 |
| 10K rows     | 8s          | 1s                   |
| 100K rows    | 45s         | 2s                   |
| 1M rows      | 5min        | 5s                   |

### State Storage

| History Runs | State Size | Recommendation |
|--------------|-----------|----------------|
| 10 runs      | ~50KB     | Keep          |
| 100 runs     | ~500KB    | Keep          |
| 1000 runs    | ~5MB      | Clean up      |

---

## API Reference

### IncrementalProcessor

```python
class IncrementalProcessor:
    """Main class for incremental processing."""

    def __init__(self, pipeline_name: str, state_dir: Optional[Path] = None)
    def get_last_watermark(self, config: IncrementalConfig) -> Optional[str]
    def build_incremental_filter(self, config: IncrementalConfig, dialect: str = "duckdb") -> Optional[str]
    def compute_row_hash(self, row: dict, check_columns: Optional[list[str]] = None) -> str
    def filter_changed_rows(self, rows: list[dict], config: IncrementalConfig, previous_hashes: Optional[dict] = None) -> list[dict]
    def start_run(self, config: IncrementalConfig, pipeline_config: Optional[dict] = None) -> PipelineState
    def complete_run(self, new_watermark: Optional[str], records_processed: int, metrics: Optional[dict] = None) -> None
    def fail_run(self, error: str) -> None
    def process(self, data_fn: Callable, config: IncrementalConfig, extract_watermark: Optional[Callable] = None, pipeline_config: Optional[dict] = None) -> dict
    def reset_state(self, include_history: bool = False) -> None
    def get_state(self) -> Optional[PipelineState]
    def get_history(self, limit: int = 10) -> list[PipelineState]
```

### IncrementalConfig

```python
class IncrementalConfig(BaseModel):
    """Configuration for incremental processing."""

    strategy: IncrementalStrategy = IncrementalStrategy.TIMESTAMP
    mode: IncrementalMode = IncrementalMode.APPEND
    watermark_column: Optional[str] = None
    unique_key: Union[str, list[str]] = "id"
    check_columns: Optional[list[str]] = None
    state_dir: Optional[Path] = None
    force_full_refresh: bool = False
```

---

## Examples

See complete examples in `/examples/incremental/`:

- `timestamp_example.py` - Timestamp-based processing
- `hash_example.py` - Hash-based change detection
- `dlt_integration.py` - DLT integration
- `dbt_integration.py` - dbt integration
- `custom_pipeline.py` - Custom pipeline implementation

---

## Next Steps

1. **Try the examples**: Start with `examples/incremental/timestamp_example.py`
2. **Integrate with your pipelines**: Add incremental processing to existing pipelines
3. **Monitor performance**: Track iteration times and state size
4. **Optimize queries**: Ensure watermark columns are indexed
5. **Join the community**: Share your incremental patterns and learnings

---

## Support

- **Documentation**: https://docs.sbdk.dev/incremental-processing
- **GitHub Issues**: https://github.com/sbdk-dev/sbdk/issues
- **Community**: https://discord.gg/sbdk

---

*Last updated: January 2025*
*SBDK Version: 1.1.2+*
