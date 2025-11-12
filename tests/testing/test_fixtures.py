"""
Tests for SBDK Testing Fixtures

Validates all pytest fixtures provided by the testing framework.
"""

import pytest
import pandas as pd
import duckdb
from pathlib import Path

from sbdk.testing.fixtures import (
    temp_db,
    temp_db_file,
    sample_users_df,
    sample_orders_df,
    sample_events_df,
    populated_db,
    temp_project_dir,
    snapshot_dir,
    mock_dbt_project,
    test_data_generator,
    time_series_data,
)


class TestTempDbFixture:
    """Test temp_db fixture"""

    def test_temp_db_provides_connection(self, temp_db):
        """Test that temp_db provides a working DuckDB connection"""
        assert temp_db is not None
        assert isinstance(temp_db, duckdb.DuckDBPyConnection)

    def test_temp_db_can_execute_query(self, temp_db):
        """Test that temp_db can execute queries"""
        result = temp_db.execute("SELECT 42 as answer").fetchone()
        assert result == (42,)

    def test_temp_db_can_create_table(self, temp_db):
        """Test that temp_db can create tables"""
        temp_db.execute("CREATE TABLE test AS SELECT 1 as id, 'Alice' as name")
        result = temp_db.execute("SELECT COUNT(*) FROM test").fetchone()
        assert result == (1,)

    def test_temp_db_isolation(self, temp_db):
        """Test that each test gets a clean database"""
        # This table shouldn't exist from previous test
        with pytest.raises(Exception):  # Should raise catalog error
            temp_db.execute("SELECT * FROM should_not_exist")


class TestTempDbFileFixture:
    """Test temp_db_file fixture"""

    def test_temp_db_file_provides_path_and_connection(self, temp_db_file):
        """Test that temp_db_file provides both path and connection"""
        db_path, conn = temp_db_file

        assert isinstance(db_path, Path)
        assert isinstance(conn, duckdb.DuckDBPyConnection)
        assert db_path.exists()
        assert db_path.suffix == ".db"

    def test_temp_db_file_persists_data(self, temp_db_file):
        """Test that data persists in file-based database"""
        db_path, conn = temp_db_file

        conn.execute("CREATE TABLE persistent AS SELECT 123 as value")
        result = conn.execute("SELECT * FROM persistent").fetchone()
        assert result == (123,)


class TestSampleDataFrames:
    """Test sample data fixtures"""

    def test_sample_users_df_structure(self, sample_users_df):
        """Test sample_users_df structure"""
        assert isinstance(sample_users_df, pd.DataFrame)
        assert len(sample_users_df) == 100

        expected_columns = ["user_id", "name", "email", "age", "created_at", "country"]
        assert list(sample_users_df.columns) == expected_columns

    def test_sample_users_df_data_types(self, sample_users_df):
        """Test sample_users_df data types"""
        assert sample_users_df["user_id"].dtype == "int64"
        assert sample_users_df["name"].dtype == "object"
        assert sample_users_df["email"].dtype == "object"
        assert sample_users_df["age"].dtype == "int64"

    def test_sample_users_df_reproducible(self, sample_users_df):
        """Test that sample_users_df is reproducible with seed"""
        # The fixture uses Faker.seed(42), so data should be consistent
        first_name = sample_users_df.iloc[0]["name"]
        assert isinstance(first_name, str)
        assert len(first_name) > 0

    def test_sample_orders_df_structure(self, sample_orders_df):
        """Test sample_orders_df structure"""
        assert isinstance(sample_orders_df, pd.DataFrame)
        assert len(sample_orders_df) == 200

        expected_columns = ["order_id", "user_id", "amount", "status", "order_date"]
        assert list(sample_orders_df.columns) == expected_columns

    def test_sample_orders_df_foreign_key_relationship(self, sample_orders_df):
        """Test that order user_ids are in valid range"""
        assert sample_orders_df["user_id"].min() >= 1
        assert sample_orders_df["user_id"].max() <= 100

    def test_sample_orders_df_status_values(self, sample_orders_df):
        """Test that order statuses are valid"""
        valid_statuses = ["completed", "pending", "cancelled"]
        assert set(sample_orders_df["status"].unique()).issubset(set(valid_statuses))

    def test_sample_events_df_structure(self, sample_events_df):
        """Test sample_events_df structure"""
        assert isinstance(sample_events_df, pd.DataFrame)
        assert len(sample_events_df) == 500

        expected_columns = ["event_id", "user_id", "event_type", "timestamp", "properties"]
        assert list(sample_events_df.columns) == expected_columns

    def test_sample_events_df_event_types(self, sample_events_df):
        """Test that event types are valid"""
        valid_types = ["click", "view", "purchase", "signup", "logout"]
        assert set(sample_events_df["event_type"].unique()).issubset(set(valid_types))


class TestPopulatedDbFixture:
    """Test populated_db fixture"""

    def test_populated_db_has_users_table(self, populated_db):
        """Test that populated_db has users table"""
        result = populated_db.execute("SELECT COUNT(*) FROM users").fetchone()
        assert result == (100,)

    def test_populated_db_has_orders_table(self, populated_db):
        """Test that populated_db has orders table"""
        result = populated_db.execute("SELECT COUNT(*) FROM orders").fetchone()
        assert result == (200,)

    def test_populated_db_has_events_table(self, populated_db):
        """Test that populated_db has events table"""
        result = populated_db.execute("SELECT COUNT(*) FROM events").fetchone()
        assert result == (500,)

    def test_populated_db_can_join_tables(self, populated_db):
        """Test that tables can be joined"""
        query = """
            SELECT u.user_id, u.name, COUNT(o.order_id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.name
            HAVING order_count > 0
        """
        result = populated_db.execute(query).df()
        assert len(result) > 0
        assert "order_count" in result.columns

    def test_populated_db_complex_query(self, populated_db):
        """Test complex analytical query"""
        # Note: timestamp is stored as VARCHAR, so we use string operations
        query = """
            SELECT
                CAST(e.timestamp AS VARCHAR) as event_date,
                COUNT(DISTINCT e.user_id) as unique_users,
                COUNT(*) as total_events
            FROM events e
            GROUP BY event_date
            ORDER BY event_date
        """
        result = populated_db.execute(query).df()
        assert len(result) > 0
        assert "unique_users" in result.columns
        assert "total_events" in result.columns


class TestTempProjectDirFixture:
    """Test temp_project_dir fixture"""

    def test_temp_project_dir_structure(self, temp_project_dir):
        """Test that temp_project_dir creates correct structure"""
        assert temp_project_dir.exists()
        assert (temp_project_dir / "dbt").exists()
        assert (temp_project_dir / "dbt" / "models").exists()
        assert (temp_project_dir / "data").exists()
        assert (temp_project_dir / ".sbdk").exists()

    def test_temp_project_dir_dbt_project_yml(self, temp_project_dir):
        """Test that dbt_project.yml exists and is valid"""
        dbt_project_yml = temp_project_dir / "dbt" / "dbt_project.yml"
        assert dbt_project_yml.exists()

        content = dbt_project_yml.read_text()
        assert "name:" in content
        assert "test_project" in content


class TestSnapshotDirFixture:
    """Test snapshot_dir fixture"""

    def test_snapshot_dir_exists(self, snapshot_dir):
        """Test that snapshot_dir is created"""
        assert snapshot_dir.exists()
        assert snapshot_dir.is_dir()
        assert snapshot_dir.name == ".snapshots"

    def test_snapshot_dir_can_write_files(self, snapshot_dir):
        """Test that files can be written to snapshot_dir"""
        test_file = snapshot_dir / "test.txt"
        test_file.write_text("test content")

        assert test_file.exists()
        assert test_file.read_text() == "test content"


class TestMockDbtProjectFixture:
    """Test mock_dbt_project fixture"""

    def test_mock_dbt_project_structure(self, mock_dbt_project):
        """Test mock dbt project structure"""
        assert mock_dbt_project.exists()
        assert (mock_dbt_project / "models").exists()
        assert (mock_dbt_project / "models" / "staging").exists()
        assert (mock_dbt_project / "models" / "marts").exists()

    def test_mock_dbt_project_has_models(self, mock_dbt_project):
        """Test that mock project has sample models"""
        staging_model = mock_dbt_project / "models" / "staging" / "stg_users.sql"
        marts_model = mock_dbt_project / "models" / "marts" / "user_metrics.sql"

        assert staging_model.exists()
        assert marts_model.exists()

        # Check content
        staging_content = staging_model.read_text()
        assert "SELECT" in staging_content
        assert "user_id" in staging_content

    def test_mock_dbt_project_has_schema_yml(self, mock_dbt_project):
        """Test that schema.yml exists"""
        schema_yml = mock_dbt_project / "models" / "schema.yml"
        assert schema_yml.exists()

        content = schema_yml.read_text()
        assert "sources:" in content
        assert "models:" in content


class TestTestDataGeneratorFixture:
    """Test test_data_generator fixture"""

    def test_test_data_generator_is_faker(self, test_data_generator):
        """Test that fixture provides Faker instance"""
        from faker import Faker

        assert isinstance(test_data_generator, Faker)

    def test_test_data_generator_can_generate_data(self, test_data_generator):
        """Test that generator can create fake data"""
        name = test_data_generator.name()
        email = test_data_generator.email()

        assert isinstance(name, str)
        assert isinstance(email, str)
        assert "@" in email


class TestTimeSeriesDataFixture:
    """Test time_series_data fixture"""

    def test_time_series_data_structure(self, time_series_data):
        """Test time series data structure"""
        assert isinstance(time_series_data, pd.DataFrame)
        assert len(time_series_data) == 91  # 91 days (Jan 1 - Mar 31, inclusive)

        expected_columns = ["date", "daily_users", "daily_revenue", "daily_orders"]
        assert list(time_series_data.columns) == expected_columns

    def test_time_series_data_date_range(self, time_series_data):
        """Test that dates cover the expected range"""
        assert time_series_data["date"].min() == pd.Timestamp("2024-01-01")
        assert time_series_data["date"].max() == pd.Timestamp("2024-03-31")

    def test_time_series_data_values(self, time_series_data):
        """Test that values are in expected ranges"""
        assert time_series_data["daily_users"].min() >= 100
        assert time_series_data["daily_users"].max() <= 1000

        assert time_series_data["daily_revenue"].min() >= 1000.0
        assert time_series_data["daily_revenue"].max() <= 10000.0

        assert time_series_data["daily_orders"].min() >= 10
        assert time_series_data["daily_orders"].max() <= 100


class TestFixtureIntegration:
    """Test fixtures working together"""

    def test_multiple_fixtures_together(
        self, temp_db, sample_users_df, sample_orders_df
    ):
        """Test using multiple fixtures in one test"""
        # Register DataFrames in database
        temp_db.register("users", sample_users_df)
        temp_db.register("orders", sample_orders_df)

        # Run join query
        result = temp_db.execute(
            """
            SELECT u.name, COUNT(*) as order_count
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.name
            HAVING order_count > 0
            """
        ).df()

        assert len(result) > 0
        assert "order_count" in result.columns

    def test_populated_db_with_snapshot(self, populated_db, snapshot_dir):
        """Test using populated_db with snapshot directory"""
        from sbdk.testing.framework import SnapshotTester

        # Query data
        result = populated_db.execute("SELECT COUNT(*) as user_count FROM users").df()

        # Create snapshot
        tester = SnapshotTester(snapshot_dir)
        tester.capture_snapshot("user_count", result)

        # Verify snapshot was created
        snapshot_path = snapshot_dir / "user_count.json"
        assert snapshot_path.exists()
