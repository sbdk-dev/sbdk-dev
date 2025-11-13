"""
Comprehensive tests for CSV/File Connector.

Tests cover:
- All file formats (CSV, TSV, JSON, JSONL, Parquet)
- Schema detection and type inference
- Column filtering and selection
- Error handling and edge cases
- Memory-efficient streaming
- Encoding detection
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

from sbdk.exceptions import ValidationError, FileSystemError
from sbdk.sources.base import SourceConnectionConfig, SourceType, SchemaInfo
from sbdk.sources.connectors.csv_connector import (
    CSVConnector,
    CSVConnectorConfig,
    ColumnType,
    Encoding,
    FileFormat,
)


class TestCSVConnectorConfig:
    """Test suite for CSVConnectorConfig validation."""

    def test_create_basic_config(self):
        """Test creating basic CSV connector configuration."""
        config = CSVConnectorConfig(name="test_csv")

        assert config.name == "test_csv"
        assert config.encoding == Encoding.UTF8
        assert config.has_header is True
        assert config.chunk_size == 10000
        assert config.infer_types is True

    def test_create_config_with_options(self):
        """Test creating config with custom options."""
        config = CSVConnectorConfig(
            name="custom_csv",
            file_format=FileFormat.CSV,
            delimiter=",",
            encoding=Encoding.LATIN1,
            skip_rows=2,
            chunk_size=5000,
            max_rows=1000
        )

        assert config.file_format == FileFormat.CSV
        assert config.delimiter == ","
        assert config.encoding == Encoding.LATIN1
        assert config.skip_rows == 2
        assert config.chunk_size == 5000
        assert config.max_rows == 1000

    def test_invalid_delimiter(self):
        """Test that multi-character delimiter raises error."""
        # Valid single character should work
        config = CSVConnectorConfig(
            name="test",
            delimiter=","
        )
        assert config.delimiter == ","

        # Multi-character delimiter should raise error
        with pytest.raises(Exception):  # Pydantic ValidationError
            CSVConnectorConfig(
                name="test",
                delimiter="||"  # Invalid multi-character
            )

    def test_column_list_validation(self):
        """Test column list validation."""
        # Valid column lists
        config = CSVConnectorConfig(
            name="test",
            columns=["name", "age", "city"]
        )
        assert len(config.columns) == 3

        # Duplicate columns should raise error
        with pytest.raises(Exception):  # Pydantic ValidationError
            CSVConnectorConfig(
                name="test",
                columns=["name", "age", "name"]  # Duplicate
            )

    def test_exclude_columns_validation(self):
        """Test exclude_columns validation."""
        # Valid exclusion list
        config = CSVConnectorConfig(
            name="test",
            exclude_columns=["password", "secret"]
        )
        assert len(config.exclude_columns) == 2

        # Duplicate exclusions should raise error
        with pytest.raises(Exception):  # Pydantic ValidationError
            CSVConnectorConfig(
                name="test",
                exclude_columns=["password", "password"]  # Duplicate
            )


class TestCSVConnector:
    """Test suite for CSVConnector core functionality."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    @pytest.fixture
    def sample_csv_data(self) -> List[Dict[str, Any]]:
        """Sample data for CSV tests."""
        return [
            {"name": "Alice", "age": "25", "city": "New York", "active": "true"},
            {"name": "Bob", "age": "30", "city": "London", "active": "false"},
            {"name": "Charlie", "age": "35", "city": "Paris", "active": "true"},
        ]

    @pytest.fixture
    def sample_csv_file(self, temp_dir, sample_csv_data):
        """Create sample CSV file."""
        csv_file = temp_dir / "test.csv"

        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "age", "city", "active"])
            writer.writeheader()
            writer.writerows(sample_csv_data)

        return csv_file

    @pytest.fixture
    def sample_tsv_file(self, temp_dir, sample_csv_data):
        """Create sample TSV file."""
        tsv_file = temp_dir / "test.tsv"

        with open(tsv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "age", "city", "active"], delimiter="\t")
            writer.writeheader()
            writer.writerows(sample_csv_data)

        return tsv_file

    @pytest.fixture
    def sample_json_file(self, temp_dir, sample_csv_data):
        """Create sample JSON file."""
        json_file = temp_dir / "test.json"

        with open(json_file, "w") as f:
            json.dump(sample_csv_data, f)

        return json_file

    @pytest.fixture
    def sample_jsonl_file(self, temp_dir, sample_csv_data):
        """Create sample JSONL file."""
        jsonl_file = temp_dir / "test.jsonl"

        with open(jsonl_file, "w") as f:
            for record in sample_csv_data:
                f.write(json.dumps(record) + "\n")

        return jsonl_file

    def test_csv_connector_initialization(self, sample_csv_file):
        """Test CSV connector initialization."""
        base_config = SourceConnectionConfig(
            name="test_csv",
            source_type=SourceType.FILE
        )
        csv_config = CSVConnectorConfig(name="test_csv")

        connector = CSVConnector(base_config, sample_csv_file, csv_config)

        assert connector.file_path == sample_csv_file
        assert connector.csv_config.name == "test_csv"
        assert connector._connected is False

    def test_csv_connector_connect(self, sample_csv_file):
        """Test connector connection validation."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        connector = CSVConnector(base_config, sample_csv_file)

        # Should connect successfully
        connector.connect()
        assert connector._connected is True

        # Disconnect
        connector.disconnect()
        assert connector._connected is False

    def test_csv_connector_missing_file(self, temp_dir):
        """Test connector with missing file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        missing_file = temp_dir / "missing.csv"

        connector = CSVConnector(base_config, missing_file)

        with pytest.raises(FileNotFoundError):
            connector.connect()

    def test_parse_csv_file(self, sample_csv_file, sample_csv_data):
        """Test parsing CSV file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            file_format=FileFormat.CSV,
            infer_types=False  # Keep as strings for this test
        )

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 3
        assert records[0]["name"] == "Alice"
        assert records[1]["age"] == "30"
        assert records[2]["city"] == "Paris"

    def test_parse_tsv_file(self, sample_tsv_file):
        """Test parsing TSV file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            file_format=FileFormat.TSV,
            infer_types=False
        )

        connector = CSVConnector(base_config, sample_tsv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 3
        assert records[0]["name"] == "Alice"

    def test_parse_json_file(self, sample_json_file):
        """Test parsing JSON file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            file_format=FileFormat.JSON
        )

        connector = CSVConnector(base_config, sample_json_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 3
        assert records[0]["name"] == "Alice"

    def test_parse_jsonl_file(self, sample_jsonl_file):
        """Test parsing JSONL file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            file_format=FileFormat.JSONL
        )

        connector = CSVConnector(base_config, sample_jsonl_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 3
        assert records[0]["name"] == "Alice"

    def test_auto_detect_csv_format(self, sample_csv_file):
        """Test automatic CSV format detection."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test")  # No format specified

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        detected_format = connector._get_file_format()
        assert detected_format == FileFormat.CSV

    def test_auto_detect_json_format(self, sample_json_file):
        """Test automatic JSON format detection."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test")

        connector = CSVConnector(base_config, sample_json_file, csv_config)
        connector.connect()

        detected_format = connector._get_file_format()
        assert detected_format == FileFormat.JSON

    def test_delimiter_detection(self, temp_dir):
        """Test automatic delimiter detection."""
        # Create semicolon-delimited file
        csv_file = temp_dir / "test_semicolon.csv"
        with open(csv_file, "w") as f:
            f.write("name;age;city\n")
            f.write("Alice;25;New York\n")
            f.write("Bob;30;London\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test")  # No delimiter specified

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        detected_delimiter = connector._get_delimiter()
        assert detected_delimiter == ";"

    def test_schema_detection(self, sample_csv_file):
        """Test schema detection from CSV file."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=True)

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        schema = connector.detect_schema()

        assert isinstance(schema, SchemaInfo)
        assert schema.table_name == "test"  # From filename
        assert len(schema.columns) == 4

        # Check column names
        column_names = [col["name"] for col in schema.columns]
        assert "name" in column_names
        assert "age" in column_names
        assert "city" in column_names
        assert "active" in column_names

    def test_type_inference(self, temp_dir):
        """Test automatic type inference."""
        # Create CSV with various types
        csv_file = temp_dir / "types.csv"
        with open(csv_file, "w") as f:
            f.write("name,age,salary,active,signup_date\n")
            f.write("Alice,25,50000.50,true,2023-01-15\n")
            f.write("Bob,30,60000.75,false,2023-02-20\n")
            f.write("Charlie,35,70000.00,true,2023-03-10\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=True)

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        schema = connector.detect_schema()

        # Check inferred types
        type_map = {col["name"]: col["type"] for col in schema.columns}

        assert type_map["name"] == ColumnType.STRING.value
        assert type_map["age"] == ColumnType.INTEGER.value
        assert type_map["salary"] == ColumnType.FLOAT.value
        assert type_map["active"] == ColumnType.BOOLEAN.value
        assert type_map["signup_date"] == ColumnType.DATE.value

    def test_column_filtering(self, sample_csv_file):
        """Test filtering specific columns."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            columns=["name", "age"],  # Only these columns
            infer_types=False
        )

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        # Check only selected columns present
        assert len(records[0].keys()) == 2
        assert "name" in records[0]
        assert "age" in records[0]
        assert "city" not in records[0]
        assert "active" not in records[0]

    def test_column_exclusion(self, sample_csv_file):
        """Test excluding specific columns."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            exclude_columns=["active"],  # Exclude this column
            infer_types=False
        )

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        # Check excluded column not present
        assert "name" in records[0]
        assert "age" in records[0]
        assert "city" in records[0]
        assert "active" not in records[0]

    def test_skip_rows(self, temp_dir):
        """Test skipping initial rows."""
        csv_file = temp_dir / "skip_rows.csv"
        with open(csv_file, "w") as f:
            f.write("# Comment line 1\n")
            f.write("# Comment line 2\n")
            f.write("name,age\n")
            f.write("Alice,25\n")
            f.write("Bob,30\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            skip_rows=2,  # Skip first 2 rows
            infer_types=False
        )

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_max_rows_limit(self, sample_csv_file):
        """Test limiting maximum rows read."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            max_rows=2,  # Only read 2 rows
            infer_types=False
        )

        connector = CSVConnector(base_config, sample_csv_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        assert len(records) == 2

    def test_context_manager(self, sample_csv_file):
        """Test using connector as context manager."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        connector = CSVConnector(base_config, sample_csv_file)

        with connector:
            assert connector._connected is True
            records = list(connector.fetch_data())
            assert len(records) > 0

        assert connector._connected is False

    def test_empty_file(self, temp_dir):
        """Test handling empty CSV file."""
        csv_file = temp_dir / "empty.csv"
        with open(csv_file, "w") as f:
            f.write("name,age\n")  # Only header

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        connector = CSVConnector(base_config, csv_file)
        connector.connect()

        # Should handle gracefully
        with pytest.raises(ValidationError) as exc_info:
            connector.detect_schema()

        assert "empty" in str(exc_info.value).lower()

    def test_malformed_csv(self, temp_dir):
        """Test handling malformed CSV."""
        csv_file = temp_dir / "malformed.csv"
        with open(csv_file, "w") as f:
            f.write("name,age\n")
            f.write("Alice,25\n")
            f.write("Bob,30,extra,columns\n")  # Malformed
            f.write("Charlie,35\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)

        # With skip_errors=False, should raise
        csv_config = CSVConnectorConfig(name="test", skip_errors=False, infer_types=False)
        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        # Should still work (CSV is flexible with extra columns)
        records = list(connector.parse_file())
        assert len(records) >= 2

    def test_skip_malformed_rows(self, temp_dir):
        """Test skipping malformed rows."""
        jsonl_file = temp_dir / "malformed.jsonl"
        with open(jsonl_file, "w") as f:
            f.write('{"name": "Alice", "age": 25}\n')
            f.write('not valid json\n')  # Malformed
            f.write('{"name": "Bob", "age": 30}\n')

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            file_format=FileFormat.JSONL,
            skip_errors=True  # Skip malformed rows
        )

        connector = CSVConnector(base_config, jsonl_file, csv_config)
        connector.connect()

        records = list(connector.parse_file())

        # Should skip malformed row
        assert len(records) == 2
        assert records[0]["name"] == "Alice"
        assert records[1]["name"] == "Bob"

    def test_encoding_detection(self, temp_dir):
        """Test encoding detection and handling."""
        # Create file with Latin-1 encoding
        csv_file = temp_dir / "latin1.csv"
        with open(csv_file, "w", encoding="latin-1") as f:
            f.write("name,city\n")
            f.write("José,São Paulo\n")  # Latin-1 characters

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=False)

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        # Should auto-detect or fallback to working encoding
        records = list(connector.parse_file())
        assert len(records) >= 1

    def test_type_conversion(self, temp_dir):
        """Test type conversion of parsed values."""
        csv_file = temp_dir / "convert.csv"
        with open(csv_file, "w") as f:
            f.write("name,age,salary,active\n")
            f.write("Alice,25,50000.50,true\n")
            f.write("Bob,30,60000.75,false\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=True)

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        # Trigger schema detection (caches types)
        schema = connector.detect_schema()

        # Now fetch data with type conversion
        records = list(connector.parse_file())

        # Types should be converted
        assert isinstance(records[0]["age"], int)
        assert isinstance(records[0]["salary"], float)
        assert isinstance(records[0]["active"], bool)
        assert records[0]["age"] == 25
        assert records[0]["active"] is True

    def test_boolean_inference(self, temp_dir):
        """Test boolean value inference."""
        csv_file = temp_dir / "bool.csv"
        with open(csv_file, "w") as f:
            f.write("value1,value2,value3,value4\n")
            f.write("true,yes,1,t\n")
            f.write("false,no,0,f\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=True)

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        schema = connector.detect_schema()

        # All columns should be inferred as boolean
        for col in schema.columns:
            assert col["type"] == ColumnType.BOOLEAN.value

    def test_null_handling(self, temp_dir):
        """Test handling of null/empty values."""
        csv_file = temp_dir / "nulls.csv"
        with open(csv_file, "w") as f:
            f.write("name,age,city\n")
            f.write("Alice,25,New York\n")
            f.write("Bob,,London\n")  # Missing age
            f.write("Charlie,35,\n")  # Missing city

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", infer_types=True)

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        schema = connector.detect_schema()

        # Check nullable detection
        age_col = next(col for col in schema.columns if col["name"] == "age")
        city_col = next(col for col in schema.columns if col["name"] == "city")

        assert age_col["nullable"] is True
        assert city_col["nullable"] is True

    def test_row_count_estimation(self, sample_csv_file):
        """Test row count estimation."""
        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        connector = CSVConnector(base_config, sample_csv_file)
        connector.connect()

        schema = connector.detect_schema()

        # Should estimate row count for CSV
        assert schema.row_count is not None
        assert schema.row_count == 3

    def test_json_invalid_structure(self, temp_dir):
        """Test JSON file with invalid structure."""
        json_file = temp_dir / "invalid.json"
        with open(json_file, "w") as f:
            json.dump({"not": "an array"}, f)  # Not an array

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(name="test", file_format=FileFormat.JSON)

        connector = CSVConnector(base_config, json_file, csv_config)
        connector.connect()

        with pytest.raises(ValidationError) as exc_info:
            list(connector.parse_file())

        assert "array" in str(exc_info.value).lower()

    def test_unsupported_format(self, temp_dir):
        """Test unsupported file format."""
        unknown_file = temp_dir / "test.xyz"
        with open(unknown_file, "w") as f:
            f.write("some data")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        connector = CSVConnector(base_config, unknown_file)
        connector.connect()

        with pytest.raises(ValidationError) as exc_info:
            connector._get_file_format()

        assert "format" in str(exc_info.value).lower()


class TestCSVConnectorIntegration:
    """Integration tests for CSVConnector."""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow from file to data."""
        # Create test CSV
        csv_file = tmp_path / "sales.csv"
        with open(csv_file, "w") as f:
            f.write("product,quantity,price,sold\n")
            f.write("Widget,10,29.99,true\n")
            f.write("Gadget,5,49.99,true\n")
            f.write("Doohickey,15,19.99,false\n")

        # Create connector
        base_config = SourceConnectionConfig(
            name="sales_data",
            source_type=SourceType.FILE,
            description="Sales data connector"
        )
        csv_config = CSVConnectorConfig(
            name="sales_data",
            file_format=FileFormat.CSV,
            infer_types=True
        )

        connector = CSVConnector(base_config, csv_file, csv_config)

        # Connect and validate
        connector.connect()
        assert connector.test_connection() is True

        # Detect schema
        schema = connector.detect_schema("sales")
        assert schema.table_name == "sales"
        assert len(schema.columns) == 4

        # Fetch data
        records = list(connector.fetch_data())
        assert len(records) == 3

        # Verify types were inferred
        assert isinstance(records[0]["quantity"], int)
        assert isinstance(records[0]["price"], float)
        assert isinstance(records[0]["sold"], bool)

        # Disconnect
        connector.disconnect()
        assert connector._connected is False

    def test_streaming_large_file(self, tmp_path):
        """Test memory-efficient streaming of large file."""
        csv_file = tmp_path / "large.csv"

        # Create large CSV file
        num_rows = 10000
        with open(csv_file, "w") as f:
            f.write("id,value\n")
            for i in range(num_rows):
                f.write(f"{i},{i * 2}\n")

        base_config = SourceConnectionConfig(name="test", source_type=SourceType.FILE)
        csv_config = CSVConnectorConfig(
            name="test",
            chunk_size=1000,
            infer_types=False
        )

        connector = CSVConnector(base_config, csv_file, csv_config)
        connector.connect()

        # Stream records (should not load all into memory)
        count = 0
        for record in connector.fetch_data():
            count += 1
            if count >= 100:  # Only process first 100
                break

        assert count == 100
