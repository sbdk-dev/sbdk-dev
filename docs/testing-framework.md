# SBDK Testing Framework

**Version**: 1.0.0
**Status**: Phase 1.2 Complete

## Overview

The SBDK Testing Framework provides comprehensive utilities for testing data transformations, pipeline logic, and query results. It extends pytest with SBDK-specific functionality designed for data engineering workflows.

## Features

✅ **Data Transformation Testing** - Test SQL queries and dbt models
✅ **Snapshot Testing** - Regression testing for query results
✅ **Pipeline Testing** - Test complete pipeline execution
✅ **Custom Assertions** - Data-specific assertions with clear error messages
✅ **Reusable Fixtures** - Common test data and scenarios
✅ **CLI Integration** - `sbdk test` command for running tests

## Installation

The testing framework is included with SBDK. For development, ensure you have the test dependencies:

```bash
uv add --dev pytest pytest-cov
```

## Quick Start

### 1. Import the Framework

```python
from sbdk.testing import (
    DataTransformationTester,
    SnapshotTester,
    PipelineTester,
    assert_row_count,
    assert_dataframe_equal,
    assert_no_nulls,
)
```

### 2. Test a SQL Query

```python
def test_user_query(temp_db):
    """Test user filtering query"""
    # Create test data
    temp_db.execute(
        "CREATE TABLE users AS SELECT * FROM (VALUES (1, 'Alice', 25), (2, 'Bob', 17)) AS t(id, name, age)"
    )

    # Test query
    tester = DataTransformationTester(connection=temp_db)
    result = tester.test_query(
        "SELECT * FROM users WHERE age >= 18",
        expected_count=1,
        expected_columns=["id", "name", "age"]
    )

    assert result.status == "passed"
```

### 3. Use Assertions

```python
def test_data_quality(sample_users_df):
    """Test data quality rules"""
    # No nulls in critical columns
    assert_no_nulls(sample_users_df, columns=["user_id", "email"])

    # Unique user IDs
    assert_unique(sample_users_df, "user_id")

    # Row count
    assert_row_count(sample_users_df, expected=100)
```

### 4. Test with Snapshots

```python
def test_metrics_snapshot(populated_db, snapshot_dir):
    """Test metrics haven't changed"""
    result = populated_db.execute(
        "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id"
    ).df()

    tester = SnapshotTester(snapshot_dir)
    snapshot_result = tester.assert_matches_snapshot(
        "user_metrics",
        result,
        update_snapshots=False  # Set to True to update
    )

    assert snapshot_result.status == "passed"
```

## Core Components

### 1. DataTransformationTester

Test SQL queries and data transformations with flexible validation options.

#### Features

- Row count validation
- Column name validation
- Data comparison
- Clear error messages

#### Example

```python
from sbdk.testing import DataTransformationTester

def test_transformation(temp_db):
    tester = DataTransformationTester(connection=temp_db)

    # Create test data
    temp_db.execute(
        "CREATE TABLE sales AS SELECT * FROM (VALUES (100), (200), (300)) AS t(amount)"
    )

    # Test transformation
    result = tester.test_query(
        query="SELECT SUM(amount) as total FROM sales",
        expected_count=1
    )

    assert result.status == "passed"
    assert result.duration > 0
```

#### API Reference

```python
class DataTransformationTester:
    def __init__(
        self,
        db_path: Optional[str] = None,
        connection: Optional[duckdb.DuckDBPyConnection] = None
    ):
        """Initialize tester with database connection."""

    def test_query(
        self,
        query: str,
        expected_count: Optional[int] = None,
        expected_columns: Optional[list[str]] = None,
        expected_data: Optional[pd.DataFrame] = None,
        name: Optional[str] = None
    ) -> TestResult:
        """Test a SQL query against expectations."""

    def close(self) -> None:
        """Close database connection."""
```

### 2. SnapshotTester

Regression testing for query results using snapshots.

#### Features

- Capture query results as snapshots
- Compare against saved snapshots
- Update snapshots when needed
- Hash-based change detection

#### Example

```python
from sbdk.testing import SnapshotTester

def test_with_snapshot(populated_db, snapshot_dir):
    # Query data
    result = populated_db.execute("SELECT * FROM users").df()

    # Test against snapshot
    tester = SnapshotTester(snapshot_dir)
    snapshot_result = tester.assert_matches_snapshot(
        "all_users",
        result,
        update_snapshots=False
    )

    assert snapshot_result.status == "passed"
```

#### Updating Snapshots

```python
# Update snapshot when data changes are expected
result = tester.assert_matches_snapshot(
    "user_summary",
    summary_df,
    update_snapshots=True  # Creates or updates snapshot
)
```

#### API Reference

```python
class SnapshotTester:
    def __init__(self, snapshot_dir: Union[str, Path] = ".snapshots"):
        """Initialize with snapshot directory."""

    def capture_snapshot(
        self,
        name: str,
        data: Union[pd.DataFrame, dict, list]
    ) -> None:
        """Capture data as a snapshot."""

    def load_snapshot(self, name: str) -> dict:
        """Load snapshot from file."""

    def assert_matches_snapshot(
        self,
        name: str,
        data: Union[pd.DataFrame, dict, list],
        update_snapshots: bool = False
    ) -> TestResult:
        """Assert data matches saved snapshot."""
```

### 3. PipelineTester

Test complete pipeline execution with setup, execution, and validation phases.

#### Features

- Setup/teardown management
- Execution tracking
- Validation functions
- Duration measurement

#### Example

```python
from sbdk.testing import PipelineTester

def test_etl_pipeline(temp_db):
    tester = PipelineTester()

    def setup():
        temp_db.execute("CREATE TABLE raw AS SELECT 1 as id")

    def execute():
        temp_db.execute(
            "CREATE TABLE processed AS SELECT id, id * 2 as doubled FROM raw"
        )
        return "Pipeline completed"

    def validate():
        count = temp_db.execute("SELECT COUNT(*) FROM processed").fetchone()[0]
        return count > 0

    def teardown():
        temp_db.execute("DROP TABLE IF EXISTS raw")
        temp_db.execute("DROP TABLE IF EXISTS processed")

    result = tester.run_pipeline_test(
        setup=setup,
        execute=execute,
        validate=validate,
        teardown=teardown,
        name="etl_test"
    )

    assert result.status == "passed"
```

#### API Reference

```python
class PipelineTester:
    def run_pipeline_test(
        self,
        setup: Optional[Callable[[], None]] = None,
        execute: Callable[[], Any] = None,
        validate: Optional[Callable[[], bool]] = None,
        teardown: Optional[Callable[[], None]] = None,
        name: str = "pipeline_test"
    ) -> TestResult:
        """Run complete pipeline test."""
```

## Custom Assertions

The framework provides data-specific assertions with clear, actionable error messages.

### Available Assertions

#### assert_dataframe_equal

```python
assert_dataframe_equal(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    check_dtype: bool = True,
    check_column_order: bool = True,
    rtol: float = 1e-5,
    atol: float = 1e-8
)
```

Compare two DataFrames with detailed error messages.

#### assert_row_count

```python
assert_row_count(
    data: Union[pd.DataFrame, duckdb.DuckDBPyConnection],
    expected: int,
    query: Optional[str] = None
)
```

Assert row count matches expected value.

#### assert_columns_exist

```python
assert_columns_exist(
    df: pd.DataFrame,
    columns: Sequence[str]
)
```

Assert multiple columns exist.

#### assert_no_nulls

```python
assert_no_nulls(
    df: pd.DataFrame,
    columns: Optional[Sequence[str]] = None
)
```

Assert no null values in columns.

#### assert_unique

```python
assert_unique(
    df: pd.DataFrame,
    columns: Union[str, Sequence[str]]
)
```

Assert values are unique.

#### assert_value_in_range

```python
assert_value_in_range(
    df: pd.DataFrame,
    column: str,
    min_value: Any,
    max_value: Any
)
```

Assert all values are within range.

#### assert_schema_matches

```python
assert_schema_matches(
    df: pd.DataFrame,
    expected_schema: dict[str, Union[type, str]]
)
```

Assert DataFrame schema matches expected.

#### assert_valid_fact_table

```python
assert_valid_fact_table(
    df: pd.DataFrame,
    grain_columns: Sequence[str],
    required_columns: Optional[Sequence[str]] = None,
    no_null_columns: Optional[Sequence[str]] = None
)
```

Validate fact table structure.

### Example: Data Quality Tests

```python
def test_user_data_quality(sample_users_df):
    """Comprehensive data quality tests"""
    df = sample_users_df

    # Schema validation
    assert_schema_matches(df, {
        "user_id": "int64",
        "name": "object",
        "email": "object",
        "age": "int64"
    })

    # No nulls
    assert_no_nulls(df, columns=["user_id", "email"])

    # Unique IDs
    assert_unique(df, "user_id")

    # Age range
    assert_value_in_range(df, "age", min_value=18, max_value=120)
```

## Pytest Fixtures

The framework provides reusable fixtures for common test scenarios.

### Database Fixtures

#### temp_db

In-memory DuckDB connection.

```python
def test_query(temp_db):
    temp_db.execute("CREATE TABLE test AS SELECT 1 as id")
    result = temp_db.execute("SELECT * FROM test").df()
    assert len(result) == 1
```

#### temp_db_file

File-based DuckDB connection.

```python
def test_persistent(temp_db_file):
    db_path, conn = temp_db_file
    conn.execute("CREATE TABLE data AS SELECT 42 as value")
    assert db_path.exists()
```

#### populated_db

DuckDB connection with sample data (users, orders, events).

```python
def test_joins(populated_db):
    result = populated_db.execute("""
        SELECT u.name, COUNT(*) as order_count
        FROM users u
        JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.name
    """).df()
    assert len(result) > 0
```

### Sample Data Fixtures

#### sample_users_df

100 sample user records.

```python
def test_users(sample_users_df):
    assert len(sample_users_df) == 100
    assert "email" in sample_users_df.columns
```

#### sample_orders_df

200 sample order records.

```python
def test_orders(sample_orders_df):
    assert len(sample_orders_df) == 200
    total_revenue = sample_orders_df["amount"].sum()
    assert total_revenue > 0
```

#### sample_events_df

500 sample event records.

```python
def test_events(sample_events_df):
    assert len(sample_events_df) == 500
    event_types = sample_events_df["event_type"].unique()
    assert "click" in event_types
```

#### time_series_data

90 days of time series data.

```python
def test_daily_metrics(time_series_data):
    assert len(time_series_data) == 91
    assert "daily_revenue" in time_series_data.columns
```

### Project Fixtures

#### temp_project_dir

Temporary SBDK project structure.

```python
def test_project_structure(temp_project_dir):
    assert (temp_project_dir / "dbt").exists()
    assert (temp_project_dir / "data").exists()
```

#### mock_dbt_project

Mock dbt project with sample models.

```python
def test_dbt_models(mock_dbt_project):
    model_path = mock_dbt_project / "models" / "staging" / "stg_users.sql"
    assert model_path.exists()
```

#### snapshot_dir

Directory for snapshot testing.

```python
def test_snapshots(snapshot_dir):
    from sbdk.testing import SnapshotTester
    tester = SnapshotTester(snapshot_dir)
    # Use tester...
```

### Utility Fixtures

#### test_data_generator

Faker instance for generating test data.

```python
def test_fake_data(test_data_generator):
    name = test_data_generator.name()
    email = test_data_generator.email()
    assert isinstance(name, str)
```

### Listing Available Fixtures

```bash
sbdk test list-fixtures
```

## CLI Usage

### Running Tests

```bash
# Run all tests
sbdk test run

# Run specific test file
sbdk test run tests/test_pipeline.py

# Run with coverage
sbdk test run --coverage

# Run with HTML coverage report
sbdk test run --coverage --html

# Run tests matching markers
sbdk test run --markers dbt

# Run excluding slow tests
sbdk test run --markers "not slow"

# Run with keyword filter
sbdk test run --keyword "user"

# Fail if coverage below 95%
sbdk test run --coverage --fail-under 95
```

### Creating Test Files

```bash
# Create unit test
sbdk test create test_users

# Create dbt test
sbdk test create test_user_metrics --type dbt

# Create pipeline test
sbdk test create test_etl --type pipeline

# Create integration test
sbdk test create test_e2e --type integration
```

## Best Practices

### 1. Organize Tests by Type

```
tests/
├── unit/              # Unit tests for functions
├── integration/       # Integration tests
├── dbt/              # dbt model tests
├── pipeline/         # Pipeline tests
└── fixtures.py       # Shared fixtures
```

### 2. Use Descriptive Test Names

```python
# Good
def test_user_metrics_excludes_cancelled_orders():
    ...

# Bad
def test_metrics():
    ...
```

### 3. Follow AAA Pattern

```python
def test_transformation():
    # Arrange
    df = pd.DataFrame({"value": [1, 2, 3]})

    # Act
    result = df["value"].sum()

    # Assert
    assert result == 6
```

### 4. Test One Thing at a Time

```python
# Good - focused test
def test_user_count():
    assert_row_count(users_df, expected=100)

def test_no_duplicate_users():
    assert_unique(users_df, "user_id")

# Bad - testing multiple things
def test_users():
    assert_row_count(users_df, expected=100)
    assert_unique(users_df, "user_id")
    assert_no_nulls(users_df)
    # ... many more assertions
```

### 5. Use Fixtures for Common Setup

```python
@pytest.fixture
def analytics_db(temp_db, sample_users_df, sample_orders_df):
    """Fixture with prepared analytics data"""
    temp_db.register("users", sample_users_df)
    temp_db.register("orders", sample_orders_df)
    return temp_db

def test_revenue_by_user(analytics_db):
    result = analytics_db.execute("""
        SELECT user_id, SUM(amount) as revenue
        FROM orders
        GROUP BY user_id
    """).df()
    assert len(result) > 0
```

### 6. Use Markers for Test Organization

```python
import pytest

@pytest.mark.slow
def test_large_dataset():
    # Test that takes a long time
    ...

@pytest.mark.dbt
def test_dbt_model():
    # Test for dbt model
    ...

@pytest.mark.integration
def test_end_to_end():
    # Integration test
    ...
```

Run specific markers:

```bash
sbdk test run --markers dbt
sbdk test run --markers "not slow"
```

### 7. Test Error Cases

```python
from sbdk.testing import DataAssertionError

def test_invalid_age_raises_error():
    df = pd.DataFrame({"age": [-5, 25, 30]})

    with pytest.raises(DataAssertionError):
        assert_value_in_range(df, "age", min_value=0, max_value=120)
```

## Examples

### Testing dbt Models

```python
import pytest
from sbdk.testing import DataTransformationTester, assert_unique, assert_no_nulls

@pytest.mark.dbt
class TestUserMetricsModel:
    """Test user_metrics dbt model"""

    def test_model_execution(self, populated_db):
        """Test model executes successfully"""
        tester = DataTransformationTester(connection=populated_db)

        result = tester.test_query(
            """
            SELECT
                user_id,
                COUNT(*) as total_orders,
                SUM(amount) as total_spent
            FROM orders
            GROUP BY user_id
            """,
            expected_columns=["user_id", "total_orders", "total_spent"]
        )

        assert result.status == "passed"

    def test_grain_uniqueness(self, populated_db):
        """Test grain (user_id) is unique"""
        result = populated_db.execute("""
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            GROUP BY user_id
        """).df()

        assert_unique(result, "user_id")

    def test_no_nulls_in_metrics(self, populated_db):
        """Test no nulls in metric columns"""
        result = populated_db.execute("""
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            GROUP BY user_id
        """).df()

        assert_no_nulls(result, columns=["user_id", "order_count"])
```

### Testing Data Pipelines

```python
from sbdk.testing import PipelineTester, assert_row_count

@pytest.mark.pipeline
def test_etl_pipeline(temp_db):
    """Test complete ETL pipeline"""
    tester = PipelineTester()

    def setup():
        # Load raw data
        temp_db.execute("""
            CREATE TABLE raw_events AS
            SELECT * FROM (VALUES
                (1, 'click', '2024-01-01'),
                (2, 'view', '2024-01-01'),
                (1, 'purchase', '2024-01-02')
            ) AS t(user_id, event_type, event_date)
        """)

    def execute():
        # Transform data
        temp_db.execute("""
            CREATE TABLE daily_metrics AS
            SELECT
                event_date,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_events
            FROM raw_events
            GROUP BY event_date
        """)

    def validate():
        # Check results
        result = temp_db.execute("SELECT * FROM daily_metrics").df()
        return len(result) == 2  # 2 days of data

    result = tester.run_pipeline_test(
        setup=setup,
        execute=execute,
        validate=validate,
        name="daily_metrics_pipeline"
    )

    assert result.status == "passed"
```

### Snapshot Testing

```python
from sbdk.testing import SnapshotTester

def test_user_summary_snapshot(populated_db, snapshot_dir):
    """Test user summary hasn't changed"""
    # Generate summary
    summary = populated_db.execute("""
        SELECT
            u.user_id,
            u.name,
            COUNT(o.order_id) as order_count,
            COALESCE(SUM(o.amount), 0) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        GROUP BY u.user_id, u.name
        ORDER BY u.user_id
    """).df()

    # Test against snapshot
    tester = SnapshotTester(snapshot_dir)
    result = tester.assert_matches_snapshot(
        "user_summary_v1",
        summary,
        update_snapshots=False
    )

    assert result.status == "passed"
```

## Troubleshooting

### Tests Not Found

```bash
# Ensure tests directory exists and files start with test_
tests/
└── test_my_feature.py  # ✅ Good
└── my_test.py          # ❌ Won't be discovered
```

### Import Errors

```python
# Ensure sbdk/testing is in your path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sbdk.testing import DataTransformationTester
```

### Fixture Not Found

```python
# Import fixtures in conftest.py or test file
from sbdk.testing.fixtures import *
```

### Snapshot Mismatch

```bash
# Update snapshots when changes are intentional
sbdk test run --markers snapshot

# Then update in code
result = tester.assert_matches_snapshot(
    "my_snapshot",
    data,
    update_snapshots=True  # Update snapshot
)
```

## API Reference

### Test Results

```python
@dataclass
class TestResult:
    name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float  # seconds
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

### Test Suite

```python
@dataclass
class TestSuite:
    name: str
    results: list[TestResult]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def total_tests(self) -> int
    @property
    def passed(self) -> int
    @property
    def failed(self) -> int
    @property
    def success_rate(self) -> float
```

## Contributing

### Adding New Assertions

1. Add function to `sbdk/testing/assertions.py`
2. Export in `sbdk/testing/__init__.py`
3. Add tests in `tests/testing/test_assertions.py`
4. Update documentation

### Adding New Fixtures

1. Add fixture to `sbdk/testing/fixtures.py`
2. Add tests in `tests/testing/test_fixtures.py`
3. Update fixture list in CLI and documentation

## Support

- **Documentation**: [docs.sbdk.dev](https://docs.sbdk.dev)
- **GitHub**: [github.com/sbdk-dev/sbdk](https://github.com/sbdk-dev/sbdk)
- **Issues**: [github.com/sbdk-dev/sbdk/issues](https://github.com/sbdk-dev/sbdk/issues)

## Version History

### 1.0.0 (Phase 1.2)

- ✅ Core testing framework
- ✅ Data transformation testing
- ✅ Snapshot testing
- ✅ Pipeline testing
- ✅ Custom assertions
- ✅ Pytest fixtures
- ✅ CLI integration
- ✅ 95%+ test coverage

---

**Next**: Phase 2 - Quality Framework Integration
