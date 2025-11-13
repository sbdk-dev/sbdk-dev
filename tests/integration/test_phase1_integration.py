"""
Integration tests for Phase 1.1 + Phase 1.2.

Tests the complete workflow:
1. Create environment (Phase 1.1)
2. Add data sources (Phase 1.2)
3. Sample data
4. Switch environments
5. Verify isolation
"""

import csv
import json
from pathlib import Path

import pytest

from sbdk.environment import EnvironmentManager, EnvironmentTemplate
from sbdk.sources import (
    CSVConnector,
    CSVConnectorConfig,
    ColumnType,
    Encoding,
    FileFormat,
    SamplingConfig,
    SamplingStrategy,
)


class TestPhase1Integration:
    """Integration tests for Phase 1.1 + Phase 1.2."""

    @pytest.fixture
    def env_manager(self, tmp_path, monkeypatch):
        """Create EnvironmentManager with temporary directory."""
        sbdk_home = tmp_path / ".sbdk"
        monkeypatch.setenv("HOME", str(tmp_path))
        return EnvironmentManager(sbdk_home=sbdk_home)

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV file."""
        csv_file = tmp_path / "users.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "age", "active"])
            writer.writeheader()
            writer.writerows([
                {"id": "1", "name": "Alice", "age": "30", "active": "true"},
                {"id": "2", "name": "Bob", "age": "25", "active": "false"},
                {"id": "3", "name": "Charlie", "age": "35", "active": "true"},
                {"id": "4", "name": "Diana", "age": "28", "active": "true"},
                {"id": "5", "name": "Eve", "age": "32", "active": "false"},
            ])
        return csv_file

    @pytest.fixture
    def sample_json(self, tmp_path):
        """Create sample JSON file."""
        json_file = tmp_path / "products.json"
        with open(json_file, "w") as f:
            json.dump([
                {"id": 1, "name": "Laptop", "price": 999.99, "in_stock": True},
                {"id": 2, "name": "Mouse", "price": 29.99, "in_stock": True},
                {"id": 3, "name": "Keyboard", "price": 79.99, "in_stock": False},
            ], f)
        return json_file

    def test_full_workflow_single_environment(self, env_manager, sample_csv, sample_json):
        """Test complete workflow in single environment."""
        # Step 1: Create environment (Phase 1.1)
        env_path = env_manager.create("dev", template=EnvironmentTemplate.ANALYTICS)
        assert env_path.exists()
        assert (env_path / "config.json").exists()

        # Step 2: Switch to environment
        env_manager.switch("dev")
        assert env_manager.get_active_environment() == "dev"

        # Step 3: Add CSV data source (Phase 1.2)
        csv_config = CSVConnectorConfig(
            name="users",
            description="User data",
            file_format=FileFormat.CSV,
            encoding=Encoding.UTF8,
            has_header=True,
            infer_types=True,  # Enable type inference
        )
        csv_connector = CSVConnector(csv_config, sample_csv)

        # Step 4: Connect and test
        csv_connector.connect()
        assert csv_connector.test_connection()

        # Step 5: Sample data
        sample = list(csv_connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=3)
        ))
        assert len(sample) == 3
        assert sample[0]["name"] == "Alice"
        assert "age" in sample[0]  # Age field present

        # Step 6: Detect schema
        schema = csv_connector.detect_schema()
        assert schema.table_name == "users"
        assert len(schema.columns) == 4

        # Find the age column
        age_col = next(c for c in schema.columns if c["name"] == "age")
        assert age_col["type"] == ColumnType.INTEGER

        # Step 7: Full data fetch
        all_data = list(csv_connector.fetch_data())
        assert len(all_data) == 5

        csv_connector.disconnect()

        # Step 8: Add JSON data source
        json_config = CSVConnectorConfig(
            name="products",
            description="Product catalog",
            file_format=FileFormat.JSON,
            encoding=Encoding.UTF8,
        )
        json_connector = CSVConnector(json_config, sample_json)

        json_connector.connect()
        json_data = list(json_connector.fetch_data())
        assert len(json_data) == 3
        assert json_data[0]["name"] == "Laptop"
        json_connector.disconnect()

    def test_multi_environment_isolation(self, env_manager, sample_csv):
        """Test data source isolation across environments."""
        # Create two environments
        dev_path = env_manager.create("dev")
        staging_path = env_manager.create("staging")

        # Switch to dev
        env_manager.switch("dev")
        assert env_manager.get_active_environment() == "dev"

        # Add source in dev
        dev_config = CSVConnectorConfig(
            name="dev_users",
            description="Dev users",
        )
        dev_connector = CSVConnector(dev_config, sample_csv)
        dev_connector.connect()
        dev_data = list(dev_connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=2)
        ))
        assert len(dev_data) == 2
        dev_connector.disconnect()

        # Switch to staging
        env_manager.switch("staging")
        assert env_manager.get_active_environment() == "staging"

        # Add different source in staging
        staging_config = CSVConnectorConfig(
            name="staging_users",
            description="Staging users",
        )
        staging_connector = CSVConnector(staging_config, sample_csv)
        staging_connector.connect()
        staging_data = list(staging_connector.fetch_data())
        assert len(staging_data) == 5
        staging_connector.disconnect()

        # Verify both environments exist
        environments = env_manager.list_environments()
        assert len(environments) == 2
        env_names = [e["name"] for e in environments]
        assert "dev" in env_names
        assert "staging" in env_names

    def test_sampling_strategies(self, env_manager, sample_csv):
        """Test different sampling strategies in environment."""
        # Create environment
        env_path = env_manager.create("analytics", template=EnvironmentTemplate.ANALYTICS)
        env_manager.switch("analytics")

        config = CSVConnectorConfig(
            name="users",
        )
        connector = CSVConnector(config, sample_csv)
        connector.connect()

        # Test FULL strategy
        full_data = list(connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.FULL)
        ))
        assert len(full_data) == 5

        # Test LIMIT strategy
        limited_data = list(connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=2)
        ))
        assert len(limited_data) == 2

        # Test PERCENTAGE strategy (deterministic-ish for small dataset)
        percent_data = list(connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.PERCENTAGE, percentage=50.0)
        ))
        # Should be roughly 2-3 records for 5 records at 50%
        assert 1 <= len(percent_data) <= 4

        # Test RANDOM strategy with seed (deterministic)
        random_data1 = list(connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.RANDOM, percentage=60.0, seed=42)
        ))
        random_data2 = list(connector.get_sample(
            SamplingConfig(strategy=SamplingStrategy.RANDOM, percentage=60.0, seed=42)
        ))
        # Same seed should produce same results
        assert len(random_data1) == len(random_data2)
        assert random_data1 == random_data2

        connector.disconnect()

    def test_context_manager_integration(self, env_manager, sample_csv):
        """Test using context managers for clean resource management."""
        env_path = env_manager.create("dev")
        env_manager.switch("dev")

        config = CSVConnectorConfig(
            name="users",
        )

        # Use context manager
        with CSVConnector(config, sample_csv) as connector:
            assert connector._connected
            data = list(connector.get_sample(
                SamplingConfig(strategy=SamplingStrategy.LIMIT, limit=3)
            ))
            assert len(data) == 3

        # Connection should be closed after exiting context
        assert not connector._connected

    def test_schema_detection_with_types(self, env_manager, tmp_path):
        """Test schema detection with various data types."""
        env_path = env_manager.create("dev")
        env_manager.switch("dev")

        # Create CSV with mixed types
        csv_file = tmp_path / "mixed_types.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "name", "price", "quantity", "active", "created_at"]
            )
            writer.writeheader()
            writer.writerows([
                {
                    "id": "1",
                    "name": "Item A",
                    "price": "99.99",
                    "quantity": "10",
                    "active": "true",
                    "created_at": "2024-01-15"
                },
                {
                    "id": "2",
                    "name": "Item B",
                    "price": "149.50",
                    "quantity": "5",
                    "active": "false",
                    "created_at": "2024-01-16"
                },
            ])

        config = CSVConnectorConfig(
            name="mixed_data",
        )

        with CSVConnector(config, csv_file) as connector:
            schema = connector.detect_schema()

            # Verify column types
            columns_by_name = {col["name"]: col for col in schema.columns}

            assert columns_by_name["id"]["type"] == ColumnType.INTEGER
            assert columns_by_name["name"]["type"] == ColumnType.STRING
            assert columns_by_name["price"]["type"] == ColumnType.FLOAT
            assert columns_by_name["quantity"]["type"] == ColumnType.INTEGER
            assert columns_by_name["active"]["type"] == ColumnType.BOOLEAN
            assert columns_by_name["created_at"]["type"] == ColumnType.DATE

    def test_environment_copy_with_sources(self, env_manager, sample_csv):
        """Test copying environment with data source configurations."""
        # Create and configure dev environment
        dev_path = env_manager.create("dev", template=EnvironmentTemplate.ANALYTICS)
        env_manager.switch("dev")

        # Add data source
        config = CSVConnectorConfig(
            name="users",
        )
        connector = CSVConnector(config, sample_csv)
        connector.connect()
        data = list(connector.fetch_data())
        assert len(data) == 5
        connector.disconnect()

        # Copy to staging
        staging_path = env_manager.create("staging", copy_from="dev")

        # Verify staging exists
        assert staging_path.exists()
        staging_config = env_manager.get_environment("staging")
        assert staging_config.name == "staging"
        assert staging_config.template == EnvironmentTemplate.ANALYTICS

        # Switch to staging
        env_manager.switch("staging")
        assert env_manager.get_active_environment() == "staging"

        # Verify source still works in copied environment
        staging_connector = CSVConnector(config, sample_csv)
        staging_connector.connect()
        staging_data = list(staging_connector.fetch_data())
        assert len(staging_data) == 5
        staging_connector.disconnect()

    def test_status_across_components(self, env_manager, sample_csv):
        """Test status reporting across environments and sources."""
        # Create environments
        env_manager.create("dev", template=EnvironmentTemplate.BASIC)
        env_manager.create("staging", template=EnvironmentTemplate.ANALYTICS)
        env_manager.create("prod", template=EnvironmentTemplate.ML)

        # Switch to dev
        env_manager.switch("dev")

        # Get status
        status = env_manager.get_status()
        assert status["active_environment"] == "dev"
        assert status["total_environments"] == 3

        # Add source and check connector status
        config = CSVConnectorConfig(
            name="users",
            description="User data",
        )
        connector = CSVConnector(config, sample_csv)
        connector.connect()

        # Connector status reflects connection state
        assert connector._connected is True

        connector.disconnect()
        assert connector._connected is False
