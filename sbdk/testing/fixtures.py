"""
SBDK Testing Fixtures

Reusable pytest fixtures for SBDK testing scenarios.
Provides common test data, database connections, and utilities.

Usage:
    Import fixtures in your conftest.py or test files:

    >>> from sbdk.testing.fixtures import *

    Then use in tests:

    >>> def test_query(temp_db):
    ...     result = temp_db.execute("SELECT 1").fetchone()
    ...     assert result == (1,)
"""

import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any
from datetime import datetime, timedelta

import pytest
import duckdb
import pandas as pd
from faker import Faker


@pytest.fixture
def temp_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Provide a temporary in-memory DuckDB connection.

    Yields:
        DuckDB connection that is automatically closed after test

    Example:
        >>> def test_simple_query(temp_db):
        ...     result = temp_db.execute("SELECT 42 as answer").df()
        ...     assert result['answer'][0] == 42
    """
    conn = duckdb.connect(":memory:")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def temp_db_file(tmp_path: Path) -> Generator[tuple[Path, duckdb.DuckDBPyConnection], None, None]:
    """
    Provide a temporary file-based DuckDB connection.

    Args:
        tmp_path: Pytest's temporary path fixture

    Yields:
        Tuple of (database_path, connection)

    Example:
        >>> def test_persistent_data(temp_db_file):
        ...     db_path, conn = temp_db_file
        ...     conn.execute("CREATE TABLE test AS SELECT 1 as id")
        ...     assert db_path.exists()
    """
    db_path = tmp_path / "test.db"
    conn = duckdb.connect(str(db_path))
    try:
        yield db_path, conn
    finally:
        conn.close()


@pytest.fixture
def sample_users_df() -> pd.DataFrame:
    """
    Provide sample user data as DataFrame.

    Returns:
        DataFrame with sample user records

    Example:
        >>> def test_user_processing(sample_users_df):
        ...     assert len(sample_users_df) == 100
        ...     assert 'email' in sample_users_df.columns
    """
    fake = Faker()
    Faker.seed(42)  # For reproducible tests

    data = {
        "user_id": range(1, 101),
        "name": [fake.name() for _ in range(100)],
        "email": [fake.email() for _ in range(100)],
        "age": [fake.random_int(min=18, max=80) for _ in range(100)],
        "created_at": [
            fake.date_time_between(start_date="-2y", end_date="now")
            for _ in range(100)
        ],
        "country": [fake.country() for _ in range(100)],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_orders_df() -> pd.DataFrame:
    """
    Provide sample order data as DataFrame.

    Returns:
        DataFrame with sample order records

    Example:
        >>> def test_order_aggregation(sample_orders_df):
        ...     total_revenue = sample_orders_df['amount'].sum()
        ...     assert total_revenue > 0
    """
    fake = Faker()
    Faker.seed(42)

    data = {
        "order_id": range(1, 201),
        "user_id": [fake.random_int(min=1, max=100) for _ in range(200)],
        "amount": [round(fake.random.uniform(10.0, 500.0), 2) for _ in range(200)],
        "status": [
            fake.random_element(elements=("completed", "pending", "cancelled"))
            for _ in range(200)
        ],
        "order_date": [
            fake.date_time_between(start_date="-1y", end_date="now")
            for _ in range(200)
        ],
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_events_df() -> pd.DataFrame:
    """
    Provide sample event data as DataFrame.

    Returns:
        DataFrame with sample event records

    Example:
        >>> def test_event_filtering(sample_events_df):
        ...     clicks = sample_events_df[sample_events_df['event_type'] == 'click']
        ...     assert len(clicks) > 0
    """
    fake = Faker()
    Faker.seed(42)

    event_types = ["click", "view", "purchase", "signup", "logout"]
    data = {
        "event_id": range(1, 501),
        "user_id": [fake.random_int(min=1, max=100) for _ in range(500)],
        "event_type": [fake.random_element(elements=event_types) for _ in range(500)],
        "timestamp": [
            fake.date_time_between(start_date="-30d", end_date="now")
            for _ in range(500)
        ],
        "properties": [
            fake.pydict(nb_elements=3, variable_nb_elements=True)
            for _ in range(500)
        ],
    }

    return pd.DataFrame(data)


@pytest.fixture
def populated_db(
    temp_db: duckdb.DuckDBPyConnection,
    sample_users_df: pd.DataFrame,
    sample_orders_df: pd.DataFrame,
    sample_events_df: pd.DataFrame,
) -> duckdb.DuckDBPyConnection:
    """
    Provide a DuckDB connection populated with sample data.

    Creates tables: users, orders, events with sample data.

    Args:
        temp_db: Temporary DuckDB connection
        sample_users_df: Sample users data
        sample_orders_df: Sample orders data
        sample_events_df: Sample events data

    Returns:
        Populated DuckDB connection

    Example:
        >>> def test_join_query(populated_db):
        ...     result = populated_db.execute('''
        ...         SELECT u.name, COUNT(*) as order_count
        ...         FROM users u
        ...         JOIN orders o ON u.user_id = o.user_id
        ...         GROUP BY u.name
        ...     ''').df()
        ...     assert len(result) > 0
    """
    # Create tables directly from DataFrames
    # Convert datetime columns to strings to avoid conversion issues
    users_copy = sample_users_df.copy()
    users_copy['created_at'] = users_copy['created_at'].astype(str)

    orders_copy = sample_orders_df.copy()
    orders_copy['order_date'] = orders_copy['order_date'].astype(str)

    events_copy = sample_events_df.copy()
    events_copy['timestamp'] = events_copy['timestamp'].astype(str)
    events_copy['properties'] = events_copy['properties'].astype(str)

    # Register and create tables
    temp_db.register("users_temp", users_copy)
    temp_db.register("orders_temp", orders_copy)
    temp_db.register("events_temp", events_copy)

    temp_db.execute("CREATE TABLE users AS SELECT * FROM users_temp")
    temp_db.execute("CREATE TABLE orders AS SELECT * FROM orders_temp")
    temp_db.execute("CREATE TABLE events AS SELECT * FROM events_temp")

    # Unregister temporary views
    temp_db.unregister("users_temp")
    temp_db.unregister("orders_temp")
    temp_db.unregister("events_temp")

    return temp_db


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary SBDK project directory structure.

    Creates:
        - dbt/ directory with models and dbt_project.yml
        - data/ directory for sample data
        - .sbdk/ directory for SBDK metadata

    Args:
        tmp_path: Pytest's temporary path fixture

    Yields:
        Path to temporary project directory

    Example:
        >>> def test_project_structure(temp_project_dir):
        ...     assert (temp_project_dir / 'dbt').exists()
        ...     assert (temp_project_dir / 'data').exists()
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create directory structure
    (project_dir / "dbt").mkdir()
    (project_dir / "dbt" / "models").mkdir()
    (project_dir / "data").mkdir()
    (project_dir / ".sbdk").mkdir()

    # Create minimal dbt_project.yml
    dbt_project_yml = """
name: 'test_project'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"
"""
    (project_dir / "dbt" / "dbt_project.yml").write_text(dbt_project_yml)

    yield project_dir

    # Cleanup is automatic with tmp_path


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary directory for snapshot testing.

    Args:
        tmp_path: Pytest's temporary path fixture

    Yields:
        Path to snapshot directory

    Example:
        >>> def test_with_snapshots(snapshot_dir):
        ...     from sbdk.testing.framework import SnapshotTester
        ...     tester = SnapshotTester(snapshot_dir)
        ...     # Use tester...
    """
    snap_dir = tmp_path / ".snapshots"
    snap_dir.mkdir()
    yield snap_dir


@pytest.fixture
def mock_dbt_project(temp_project_dir: Path) -> Path:
    """
    Create a mock dbt project with sample models.

    Creates sample dbt models for testing dbt integration.

    Args:
        temp_project_dir: Temporary project directory

    Returns:
        Path to dbt project directory

    Example:
        >>> def test_dbt_model(mock_dbt_project):
        ...     model_path = mock_dbt_project / 'models' / 'users.sql'
        ...     assert model_path.exists()
    """
    dbt_dir = temp_project_dir / "dbt"
    models_dir = dbt_dir / "models"

    # Create sample model files
    (models_dir / "staging").mkdir()

    # staging/stg_users.sql
    (models_dir / "staging" / "stg_users.sql").write_text(
        """
-- staging/stg_users.sql
SELECT
    user_id,
    name,
    email,
    age,
    created_at,
    country
FROM {{ source('raw', 'users') }}
"""
    )

    # marts/user_metrics.sql
    (models_dir / "marts").mkdir()
    (models_dir / "marts" / "user_metrics.sql").write_text(
        """
-- marts/user_metrics.sql
SELECT
    u.user_id,
    u.name,
    COUNT(o.order_id) as total_orders,
    SUM(o.amount) as total_spent
FROM {{ ref('stg_users') }} u
LEFT JOIN {{ source('raw', 'orders') }} o
    ON u.user_id = o.user_id
GROUP BY u.user_id, u.name
"""
    )

    # Create schema.yml
    schema_yml = """
version: 2

sources:
  - name: raw
    tables:
      - name: users
      - name: orders
      - name: events

models:
  - name: stg_users
    description: Staging layer for users
    columns:
      - name: user_id
        tests:
          - unique
          - not_null

  - name: user_metrics
    description: User metrics aggregated from orders
    columns:
      - name: user_id
        tests:
          - unique
          - not_null
"""
    (models_dir / "schema.yml").write_text(schema_yml)

    return dbt_dir


@pytest.fixture
def test_data_generator() -> Faker:
    """
    Provide a seeded Faker instance for generating test data.

    Returns:
        Faker instance with fixed seed for reproducible tests

    Example:
        >>> def test_with_fake_data(test_data_generator):
        ...     fake = test_data_generator
        ...     name = fake.name()
        ...     assert isinstance(name, str)
    """
    fake = Faker()
    Faker.seed(12345)
    return fake


@pytest.fixture
def time_series_data() -> pd.DataFrame:
    """
    Provide sample time series data for testing temporal queries.

    Returns:
        DataFrame with daily metrics over 90 days

    Example:
        >>> def test_time_series_aggregation(time_series_data):
        ...     monthly = time_series_data.resample('M', on='date').sum()
        ...     assert len(monthly) > 0
    """
    dates = pd.date_range(start="2024-01-01", end="2024-03-31", freq="D")
    fake = Faker()
    Faker.seed(42)

    data = {
        "date": dates,
        "daily_users": [fake.random_int(min=100, max=1000) for _ in range(len(dates))],
        "daily_revenue": [
            round(fake.random.uniform(1000.0, 10000.0), 2) for _ in range(len(dates))
        ],
        "daily_orders": [fake.random_int(min=10, max=100) for _ in range(len(dates))],
    }

    return pd.DataFrame(data)


# Pytest plugin hooks for SBDK-specific test configuration


def pytest_configure(config: Any) -> None:
    """
    Register custom markers for SBDK tests.

    Args:
        config: Pytest config object
    """
    config.addinivalue_line(
        "markers", "dbt: mark test as requiring dbt (deselect with '-m \"not dbt\"')"
    )
    config.addinivalue_line(
        "markers",
        "snapshot: mark test as snapshot test (deselect with '-m \"not snapshot\"')",
    )
    config.addinivalue_line(
        "markers",
        "pipeline: mark test as pipeline test (deselect with '-m \"not pipeline\"')",
    )


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """
    Automatically mark tests based on naming conventions.

    Args:
        config: Pytest config object
        items: List of collected test items
    """
    for item in items:
        # Auto-mark snapshot tests
        if "snapshot" in item.nodeid:
            item.add_marker(pytest.mark.snapshot)

        # Auto-mark dbt tests
        if "dbt" in item.nodeid or "dbt" in str(item.function.__name__):
            item.add_marker(pytest.mark.dbt)

        # Auto-mark pipeline tests
        if "pipeline" in item.nodeid or "pipeline" in str(item.function.__name__):
            item.add_marker(pytest.mark.pipeline)
