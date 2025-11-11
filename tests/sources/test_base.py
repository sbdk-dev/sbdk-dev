"""
Tests for base connector framework.

Tests all abstract base classes, sampling strategies, and common functionality
for SBDK data source connectors.
"""

from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pytest

from sbdk.sources.base import (
    BaseConnector,
    ConnectionStatus,
    DatabaseConnector,
    FileConnector,
    SamplingConfig,
    SamplingStrategy,
    SchemaInfo,
    SourceConnectionConfig,
    SourceType,
)


# Test Implementation Classes

class MockConnector(BaseConnector):
    """Mock connector for testing base functionality."""

    def __init__(self, config: SourceConnectionConfig, test_data: Optional[List[Dict[str, Any]]] = None):
        """Initialize mock connector with test data."""
        super().__init__(config)
        self.test_data = test_data or [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
            {"id": 4, "name": "Diana", "age": 28},
            {"id": 5, "name": "Eve", "age": 32},
        ]
        self.connect_called = False
        self.disconnect_called = False
        self.test_connection_result = True

    def connect(self) -> None:
        """Mock connection."""
        self.connect_called = True
        self._connected = True

    def disconnect(self) -> None:
        """Mock disconnection."""
        self.disconnect_called = True
        self._connected = False

    def test_connection(self) -> bool:
        """Mock connection test."""
        return self.test_connection_result

    def fetch_data(self, query: Optional[str] = None, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """Mock data fetch."""
        yield from self.test_data

    def detect_schema(self, table_name: Optional[str] = None) -> SchemaInfo:
        """Mock schema detection."""
        return SchemaInfo(
            table_name=table_name or "mock_table",
            columns=[
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "age", "type": "integer"},
            ],
            row_count=len(self.test_data),
        )


class MockDatabaseConnector(DatabaseConnector):
    """Mock database connector for testing."""

    def __init__(self, config: SourceConnectionConfig):
        super().__init__(config)
        self.tables = ["users", "orders", "products"]
        self.query_results = {
            "users": [{"id": 1, "name": "Alice"}],
            "orders": [{"id": 1, "user_id": 1, "total": 100.0}],
        }

    def connect(self) -> None:
        """Mock connection."""
        self._connected = True

    def disconnect(self) -> None:
        """Mock disconnection."""
        self._connected = False

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True

    def execute_query(self, query: str) -> Iterator[Dict[str, Any]]:
        """Mock query execution."""
        # Simple parsing to return table data
        query_lower = query.lower()
        for table in self.tables:
            if table in query_lower:
                yield from self.query_results.get(table, [])
                return
        yield {"result": "no data"}

    def list_tables(self) -> List[str]:
        """Mock table listing."""
        return self.tables

    def detect_schema(self, table_name: Optional[str] = None) -> SchemaInfo:
        """Mock schema detection."""
        return SchemaInfo(
            table_name=table_name or "mock_table",
            columns=[{"name": "id", "type": "integer"}],
            row_count=1,
        )


class MockFileConnector(FileConnector):
    """Mock file connector for testing."""

    def __init__(self, config: SourceConnectionConfig, file_path: Path):
        super().__init__(config, file_path)
        self.file_data = [
            {"col1": "value1", "col2": "value2"},
            {"col1": "value3", "col2": "value4"},
        ]

    def parse_file(self) -> Iterator[Dict[str, Any]]:
        """Mock file parsing."""
        yield from self.file_data

    def detect_schema(self, table_name: Optional[str] = None) -> SchemaInfo:
        """Mock schema detection."""
        return SchemaInfo(
            table_name=table_name or "file",
            columns=[
                {"name": "col1", "type": "string"},
                {"name": "col2", "type": "string"},
            ],
            row_count=len(self.file_data),
        )


# Test Fixtures

@pytest.fixture
def basic_config():
    """Create basic source connection config."""
    return SourceConnectionConfig(
        name="test_source",
        source_type=SourceType.DATABASE,
        description="Test data source",
    )


@pytest.fixture
def mock_connector(basic_config):
    """Create mock connector instance."""
    return MockConnector(basic_config)


@pytest.fixture
def mock_db_connector(basic_config):
    """Create mock database connector instance."""
    return MockDatabaseConnector(basic_config)


@pytest.fixture
def mock_file_connector(basic_config, tmp_path):
    """Create mock file connector instance."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("col1,col2\nvalue1,value2\n")
    return MockFileConnector(basic_config, test_file)


# Tests for SourceConnectionConfig

class TestSourceConnectionConfig:
    """Test suite for SourceConnectionConfig."""

    def test_create_basic_config(self):
        """Test creating basic configuration."""
        config = SourceConnectionConfig(
            name="my_source",
            source_type=SourceType.DATABASE,
        )

        assert config.name == "my_source"
        assert config.source_type == SourceType.DATABASE
        assert config.description is None
        assert isinstance(config.sampling, SamplingConfig)
        assert config.metadata == {}

    def test_config_with_description(self):
        """Test configuration with description."""
        config = SourceConnectionConfig(
            name="my_source",
            source_type=SourceType.FILE,
            description="Test file source",
        )

        assert config.description == "Test file source"

    def test_config_with_sampling(self):
        """Test configuration with custom sampling."""
        sampling = SamplingConfig(
            strategy=SamplingStrategy.LIMIT,
            limit=100,
        )
        config = SourceConnectionConfig(
            name="my_source",
            source_type=SourceType.DATABASE,
            sampling=sampling,
        )

        assert config.sampling.strategy == SamplingStrategy.LIMIT
        assert config.sampling.limit == 100

    def test_config_with_metadata(self):
        """Test configuration with metadata."""
        metadata = {"owner": "data-team", "environment": "dev"}
        config = SourceConnectionConfig(
            name="my_source",
            source_type=SourceType.API,
            metadata=metadata,
        )

        assert config.metadata["owner"] == "data-team"
        assert config.metadata["environment"] == "dev"

    @pytest.mark.parametrize("source_type", [
        SourceType.DATABASE,
        SourceType.FILE,
        SourceType.API,
        SourceType.STREAM,
    ])
    def test_all_source_types(self, source_type):
        """Test all source type enums."""
        config = SourceConnectionConfig(
            name="test",
            source_type=source_type,
        )
        assert config.source_type == source_type


# Tests for SamplingConfig

class TestSamplingConfig:
    """Test suite for SamplingConfig."""

    def test_default_sampling(self):
        """Test default sampling configuration."""
        config = SamplingConfig()

        assert config.strategy == SamplingStrategy.FULL
        assert config.percentage is None
        assert config.limit is None
        assert config.seed is None

    def test_limit_sampling(self):
        """Test LIMIT sampling strategy."""
        config = SamplingConfig(
            strategy=SamplingStrategy.LIMIT,
            limit=1000,
        )

        assert config.strategy == SamplingStrategy.LIMIT
        assert config.limit == 1000

    def test_percentage_sampling(self):
        """Test PERCENTAGE sampling strategy."""
        config = SamplingConfig(
            strategy=SamplingStrategy.PERCENTAGE,
            percentage=10.0,
        )

        assert config.strategy == SamplingStrategy.PERCENTAGE
        assert config.percentage == 10.0

    def test_random_sampling_with_seed(self):
        """Test RANDOM sampling with seed."""
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            percentage=25.0,
            seed=42,
        )

        assert config.strategy == SamplingStrategy.RANDOM
        assert config.percentage == 25.0
        assert config.seed == 42

    def test_intelligent_sampling(self):
        """Test INTELLIGENT sampling strategy."""
        config = SamplingConfig(strategy=SamplingStrategy.INTELLIGENT)
        assert config.strategy == SamplingStrategy.INTELLIGENT


# Tests for SchemaInfo

class TestSchemaInfo:
    """Test suite for SchemaInfo."""

    def test_create_schema_info(self):
        """Test creating schema information."""
        columns = [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "string"},
        ]
        schema = SchemaInfo(
            table_name="users",
            columns=columns,
            row_count=100,
        )

        assert schema.table_name == "users"
        assert len(schema.columns) == 2
        assert schema.row_count == 100
        assert isinstance(schema.detected_at, datetime)

    def test_schema_without_row_count(self):
        """Test schema without row count."""
        schema = SchemaInfo(
            table_name="test_table",
            columns=[{"name": "col1", "type": "string"}],
        )

        assert schema.row_count is None

    def test_schema_json_serialization(self):
        """Test schema JSON serialization."""
        schema = SchemaInfo(
            table_name="users",
            columns=[{"name": "id", "type": "integer"}],
            row_count=50,
        )

        # Test that it can be serialized
        schema_dict = schema.dict()
        assert "table_name" in schema_dict
        assert "columns" in schema_dict
        assert "detected_at" in schema_dict


# Tests for BaseConnector

class TestBaseConnector:
    """Test suite for BaseConnector base class."""

    def test_connector_initialization(self, mock_connector):
        """Test connector initialization."""
        assert mock_connector.config.name == "test_source"
        assert mock_connector._connected is False
        assert mock_connector._connection is None

    def test_connect_and_disconnect(self, mock_connector):
        """Test connect and disconnect methods."""
        mock_connector.connect()
        assert mock_connector.connect_called is True
        assert mock_connector._connected is True

        mock_connector.disconnect()
        assert mock_connector.disconnect_called is True
        assert mock_connector._connected is False

    def test_connection_test(self, mock_connector):
        """Test connection testing."""
        result = mock_connector.test_connection()
        assert result is True

        mock_connector.test_connection_result = False
        result = mock_connector.test_connection()
        assert result is False

    def test_fetch_data(self, mock_connector):
        """Test data fetching."""
        data = list(mock_connector.fetch_data())

        assert len(data) == 5
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_detect_schema(self, mock_connector):
        """Test schema detection."""
        schema = mock_connector.detect_schema("test_table")

        assert schema.table_name == "test_table"
        assert len(schema.columns) == 3
        assert schema.row_count == 5

    def test_get_status(self, mock_connector):
        """Test getting connector status."""
        status = mock_connector.get_status()

        assert status["name"] == "test_source"
        assert status["source_type"] == "database"
        assert status["connected"] is False
        assert "sampling" in status

    def test_context_manager(self, mock_connector):
        """Test connector as context manager."""
        with mock_connector as conn:
            assert conn.connect_called is True
            assert conn._connected is True

        assert mock_connector.disconnect_called is True

    def test_get_sample_full(self, mock_connector):
        """Test FULL sampling strategy."""
        sample_config = SamplingConfig(strategy=SamplingStrategy.FULL)
        sample = list(mock_connector.get_sample(sample_config))

        assert len(sample) == 5  # All records

    def test_get_sample_limit(self, mock_connector):
        """Test LIMIT sampling strategy."""
        sample_config = SamplingConfig(
            strategy=SamplingStrategy.LIMIT,
            limit=3,
        )
        sample = list(mock_connector.get_sample(sample_config))

        assert len(sample) == 3  # Limited to 3 records
        assert sample[0]["name"] == "Alice"

    def test_get_sample_percentage(self, mock_connector):
        """Test PERCENTAGE sampling strategy."""
        # Create larger dataset for percentage testing
        large_data = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        mock_connector.test_data = large_data

        sample_config = SamplingConfig(
            strategy=SamplingStrategy.PERCENTAGE,
            percentage=10.0,
        )
        sample = list(mock_connector.get_sample(sample_config))

        # Should get approximately 10% (with randomness)
        assert 5 <= len(sample) <= 20  # Allow variance in random sampling

    def test_get_sample_random_with_seed(self, mock_connector):
        """Test RANDOM sampling with seed for reproducibility."""
        large_data = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        mock_connector.test_data = large_data

        sample_config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            percentage=20.0,
            seed=42,
        )

        # Get two samples with same seed
        sample1 = list(mock_connector.get_sample(sample_config))
        mock_connector.test_data = large_data.copy()  # Reset data
        sample2 = list(mock_connector.get_sample(sample_config))

        # Should be identical due to seed
        assert len(sample1) == len(sample2)
        assert sample1 == sample2

    def test_get_sample_intelligent(self, mock_connector):
        """Test INTELLIGENT sampling strategy."""
        sample_config = SamplingConfig(strategy=SamplingStrategy.INTELLIGENT)
        sample = list(mock_connector.get_sample(sample_config))

        # Default intelligent sampling uses limit of 1000
        # For our small dataset, should return all
        assert len(sample) == 5

    def test_get_sample_default_config(self, mock_connector):
        """Test sampling with default config from connector."""
        sample = list(mock_connector.get_sample())
        # Default is FULL strategy
        assert len(sample) == 5


# Tests for DatabaseConnector

class TestDatabaseConnector:
    """Test suite for DatabaseConnector base class."""

    def test_execute_query(self, mock_db_connector):
        """Test query execution."""
        results = list(mock_db_connector.execute_query("SELECT * FROM users"))

        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_list_tables(self, mock_db_connector):
        """Test listing tables."""
        tables = mock_db_connector.list_tables()

        assert len(tables) == 3
        assert "users" in tables
        assert "orders" in tables
        assert "products" in tables

    def test_fetch_data_with_query(self, mock_db_connector):
        """Test fetching data with SQL query."""
        data = list(mock_db_connector.fetch_data(query="SELECT * FROM orders"))

        assert len(data) == 1
        assert data[0]["user_id"] == 1

    def test_fetch_data_with_table(self, mock_db_connector):
        """Test fetching data by table name."""
        data = list(mock_db_connector.fetch_data(table="users"))

        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    def test_fetch_data_no_params_raises_error(self, mock_db_connector):
        """Test that fetch_data without query or table raises error."""
        with pytest.raises(ValueError) as exc_info:
            list(mock_db_connector.fetch_data())

        assert "query" in str(exc_info.value).lower() or "table" in str(exc_info.value).lower()


# Tests for FileConnector

class TestFileConnector:
    """Test suite for FileConnector base class."""

    def test_file_connector_initialization(self, mock_file_connector, tmp_path):
        """Test file connector initialization."""
        assert mock_file_connector.file_path.exists()
        assert mock_file_connector._connected is False

    def test_connect_success(self, mock_file_connector):
        """Test successful connection to existing file."""
        mock_file_connector.connect()
        assert mock_file_connector._connected is True

    def test_connect_missing_file_raises_error(self, basic_config, tmp_path):
        """Test connection to missing file raises error."""
        missing_file = tmp_path / "missing.csv"
        connector = MockFileConnector(basic_config, missing_file)

        with pytest.raises(FileNotFoundError):
            connector.connect()

    def test_disconnect(self, mock_file_connector):
        """Test disconnection."""
        mock_file_connector.connect()
        mock_file_connector.disconnect()
        assert mock_file_connector._connected is False

    def test_connection_test_valid_file(self, mock_file_connector):
        """Test connection test with valid file."""
        result = mock_file_connector.test_connection()
        assert result is True

    def test_connection_test_missing_file(self, basic_config, tmp_path):
        """Test connection test with missing file."""
        missing_file = tmp_path / "missing.csv"
        connector = MockFileConnector(basic_config, missing_file)

        result = connector.test_connection()
        assert result is False

    def test_parse_file(self, mock_file_connector):
        """Test file parsing."""
        data = list(mock_file_connector.parse_file())

        assert len(data) == 2
        assert data[0]["col1"] == "value1"

    def test_fetch_data(self, mock_file_connector):
        """Test fetching data from file."""
        data = list(mock_file_connector.fetch_data())

        assert len(data) == 2
        assert data[0]["col1"] == "value1"
        assert data[1]["col1"] == "value3"


# Tests for Enum Types

class TestEnumTypes:
    """Test suite for enum types."""

    def test_sampling_strategy_values(self):
        """Test SamplingStrategy enum values."""
        assert SamplingStrategy.FULL.value == "full"
        assert SamplingStrategy.PERCENTAGE.value == "percentage"
        assert SamplingStrategy.LIMIT.value == "limit"
        assert SamplingStrategy.RANDOM.value == "random"
        assert SamplingStrategy.INTELLIGENT.value == "intelligent"

    def test_source_type_values(self):
        """Test SourceType enum values."""
        assert SourceType.DATABASE.value == "database"
        assert SourceType.FILE.value == "file"
        assert SourceType.API.value == "api"
        assert SourceType.STREAM.value == "stream"

    def test_connection_status_values(self):
        """Test ConnectionStatus enum values."""
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"
        assert ConnectionStatus.ERROR.value == "error"
        assert ConnectionStatus.TESTING.value == "testing"


# Integration Tests

class TestIntegrationScenarios:
    """Integration tests for common usage scenarios."""

    def test_full_workflow_with_context_manager(self, mock_connector):
        """Test complete workflow using context manager."""
        with mock_connector as conn:
            # Test connection
            assert conn.test_connection() is True

            # Detect schema
            schema = conn.detect_schema("users")
            assert schema.table_name == "users"

            # Fetch sample
            sample_config = SamplingConfig(
                strategy=SamplingStrategy.LIMIT,
                limit=3,
            )
            sample = list(conn.get_sample(sample_config))
            assert len(sample) == 3

            # Check status
            status = conn.get_status()
            assert status["connected"] is True

    def test_error_handling_in_context_manager(self, basic_config):
        """Test error handling with context manager."""
        connector = MockConnector(basic_config)
        connector.test_connection_result = False

        with connector as conn:
            # Even if test fails, context manager should work
            assert conn.test_connection() is False

        # Should still disconnect
        assert connector.disconnect_called is True

    def test_database_query_workflow(self, mock_db_connector):
        """Test typical database query workflow."""
        with mock_db_connector as conn:
            # List available tables
            tables = conn.list_tables()
            assert len(tables) > 0

            # Query specific table
            data = list(conn.fetch_data(table="users"))
            assert len(data) > 0

            # Execute custom query
            results = list(conn.execute_query("SELECT * FROM orders"))
            assert len(results) > 0

    def test_file_processing_workflow(self, mock_file_connector):
        """Test typical file processing workflow."""
        with mock_file_connector as conn:
            # Verify file exists
            assert conn.test_connection() is True

            # Detect schema
            schema = conn.detect_schema()
            assert len(schema.columns) == 2

            # Parse and process file
            data = list(conn.fetch_data())
            assert len(data) > 0

            # Get sample
            sample_config = SamplingConfig(
                strategy=SamplingStrategy.LIMIT,
                limit=1,
            )
            sample = list(conn.get_sample(sample_config))
            assert len(sample) == 1
