"""
CSV Connector Usage Examples

Demonstrates how to use the CSVConnector for various file formats
and data processing scenarios.
"""

from pathlib import Path
from sbdk.sources.base import SourceConnectionConfig, SourceType
from sbdk.sources.connectors import (
    CSVConnector,
    CSVConnectorConfig,
    FileFormat,
    Encoding,
    ColumnType,
)


def example_basic_csv():
    """Basic CSV file reading."""
    print("\n=== Example 1: Basic CSV Reading ===")

    # Create configuration
    base_config = SourceConnectionConfig(
        name="sales_data",
        source_type=SourceType.FILE,
        description="Sales data from CSV file"
    )

    csv_config = CSVConnectorConfig(
        name="sales_data",
        file_format=FileFormat.CSV,
        infer_types=True
    )

    # Create connector (assuming file exists)
    file_path = Path("data/sales.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        # Use context manager for automatic connection handling
        with connector:
            # Detect schema
            schema = connector.detect_schema()
            print(f"Table: {schema.table_name}")
            print(f"Columns: {len(schema.columns)}")
            for col in schema.columns:
                print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")

            # Fetch data
            print("\nFirst 3 records:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def example_type_inference():
    """Demonstrate automatic type inference."""
    print("\n=== Example 2: Type Inference ===")

    base_config = SourceConnectionConfig(
        name="typed_data",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="typed_data",
        infer_types=True,
        type_inference_sample_size=1000  # Sample first 1000 rows
    )

    file_path = Path("data/customers.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            # Schema detection automatically infers types
            schema = connector.detect_schema()

            print("Inferred column types:")
            for col in schema.columns:
                print(f"  {col['name']}: {col['type']}")

            # Records will have converted types
            for i, record in enumerate(connector.fetch_data()):
                if i >= 1:
                    break
                print("\nSample record with converted types:")
                for key, value in record.items():
                    print(f"  {key}: {value} (type: {type(value).__name__})")
    else:
        print(f"File not found: {file_path}")


def example_column_filtering():
    """Filter specific columns."""
    print("\n=== Example 3: Column Filtering ===")

    base_config = SourceConnectionConfig(
        name="filtered_data",
        source_type=SourceType.FILE
    )

    # Only read specific columns
    csv_config = CSVConnectorConfig(
        name="filtered_data",
        columns=["customer_id", "name", "email"],  # Only these columns
        infer_types=False
    )

    file_path = Path("data/customers.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading only selected columns:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def example_column_exclusion():
    """Exclude sensitive columns."""
    print("\n=== Example 4: Column Exclusion ===")

    base_config = SourceConnectionConfig(
        name="safe_data",
        source_type=SourceType.FILE
    )

    # Exclude sensitive columns
    csv_config = CSVConnectorConfig(
        name="safe_data",
        exclude_columns=["password", "ssn", "credit_card"],  # Exclude these
        infer_types=False
    )

    file_path = Path("data/users.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading data without sensitive columns:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def example_large_file_streaming():
    """Stream large file efficiently."""
    print("\n=== Example 5: Large File Streaming ===")

    base_config = SourceConnectionConfig(
        name="large_dataset",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="large_dataset",
        chunk_size=10000,  # Process in chunks
        max_rows=100000,   # Limit total rows
        infer_types=True
    )

    file_path = Path("data/large_dataset.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            # Process records in streaming fashion
            count = 0
            for record in connector.fetch_data():
                count += 1
                if count % 10000 == 0:
                    print(f"Processed {count} records...")

            print(f"Total records processed: {count}")
    else:
        print(f"File not found: {file_path}")


def example_json_file():
    """Read JSON file."""
    print("\n=== Example 6: JSON File ===")

    base_config = SourceConnectionConfig(
        name="json_data",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="json_data",
        file_format=FileFormat.JSON  # Explicitly set format
    )

    file_path = Path("data/products.json")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading JSON file:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def example_jsonl_file():
    """Read JSONL (line-delimited JSON) file."""
    print("\n=== Example 7: JSONL File ===")

    base_config = SourceConnectionConfig(
        name="jsonl_logs",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="jsonl_logs",
        file_format=FileFormat.JSONL,
        max_rows=10  # Only read first 10 lines
    )

    file_path = Path("data/logs.jsonl")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading JSONL file:")
            for i, record in enumerate(connector.fetch_data()):
                print(f"  Record {i+1}: {record}")
    else:
        print(f"File not found: {file_path}")


def example_auto_detection():
    """Automatic format and delimiter detection."""
    print("\n=== Example 8: Auto-Detection ===")

    base_config = SourceConnectionConfig(
        name="auto_data",
        source_type=SourceType.FILE
    )

    # No format or delimiter specified - will auto-detect
    csv_config = CSVConnectorConfig(
        name="auto_data"
    )

    file_path = Path("data/unknown_format.csv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            # Connector will automatically detect format and delimiter
            detected_format = connector._get_file_format()
            detected_delimiter = connector._get_delimiter()
            detected_encoding = connector._get_encoding()

            print(f"Detected format: {detected_format}")
            print(f"Detected delimiter: {repr(detected_delimiter)}")
            print(f"Detected encoding: {detected_encoding}")

            print("\nData:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def example_error_handling():
    """Demonstrate error handling."""
    print("\n=== Example 9: Error Handling ===")

    base_config = SourceConnectionConfig(
        name="error_data",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="error_data",
        file_format=FileFormat.JSONL,
        skip_errors=True  # Skip malformed rows
    )

    file_path = Path("data/malformed.jsonl")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading file with skip_errors=True:")
            valid_count = 0
            for record in connector.fetch_data():
                valid_count += 1

            print(f"Successfully read {valid_count} valid records")
            print("(Malformed rows were automatically skipped)")
    else:
        print(f"File not found: {file_path}")


def example_tsv_file():
    """Read tab-separated values file."""
    print("\n=== Example 10: TSV File ===")

    base_config = SourceConnectionConfig(
        name="tsv_data",
        source_type=SourceType.FILE
    )

    csv_config = CSVConnectorConfig(
        name="tsv_data",
        file_format=FileFormat.TSV  # Tab-separated
    )

    file_path = Path("data/data.tsv")

    if file_path.exists():
        connector = CSVConnector(base_config, file_path, csv_config)

        with connector:
            print("Reading TSV file:")
            for i, record in enumerate(connector.fetch_data()):
                if i >= 3:
                    break
                print(f"  {record}")
    else:
        print(f"File not found: {file_path}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("CSV Connector Examples")
    print("=" * 60)

    # Run examples
    example_basic_csv()
    example_type_inference()
    example_column_filtering()
    example_column_exclusion()
    example_large_file_streaming()
    example_json_file()
    example_jsonl_file()
    example_auto_detection()
    example_error_handling()
    example_tsv_file()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
