"""
CSV/File Connector for SBDK Data Sources

Production-ready connector for CSV, JSON, and Parquet files with automatic
schema detection, memory-efficient streaming, and intelligent type inference.
"""

import csv
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set

from pydantic import BaseModel, Field, field_validator

from sbdk.exceptions import ValidationError, FileSystemError
from sbdk.sources.base import (
    FileConnector,
    SchemaInfo,
    SourceConnectionConfig,
    SourceType,
)


class FileFormat(str, Enum):
    """Supported file formats."""

    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    JSONL = "jsonl"
    PARQUET = "parquet"


class Encoding(str, Enum):
    """Common file encodings."""

    UTF8 = "utf-8"
    LATIN1 = "latin-1"
    ASCII = "ascii"
    UTF16 = "utf-16"
    CP1252 = "cp1252"


class ColumnType(str, Enum):
    """Inferred column data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    NULL = "null"


class CSVConnectorConfig(BaseModel):
    """
    Configuration for CSV/file connector.

    Provides comprehensive configuration options for reading various file formats
    with automatic detection and explicit override capabilities.

    Example:
        >>> config = CSVConnectorConfig(
        ...     name="sales_data",
        ...     file_format=FileFormat.CSV,
        ...     delimiter=",",
        ...     encoding=Encoding.UTF8
        ... )
    """

    # Inherited from SourceConnectionConfig
    name: str = Field(..., description="Connection name")
    description: Optional[str] = Field(None, description="Connection description")

    # File format settings
    file_format: Optional[FileFormat] = Field(
        None,
        description="File format (auto-detected if None)"
    )
    encoding: Encoding = Field(
        default=Encoding.UTF8,
        description="File encoding"
    )

    # CSV-specific settings
    delimiter: Optional[str] = Field(
        None,
        description="CSV delimiter (auto-detected if None)"
    )
    quotechar: str = Field(
        default='"',
        description="Quote character for CSV"
    )
    escapechar: Optional[str] = Field(
        None,
        description="Escape character for CSV"
    )
    has_header: bool = Field(
        default=True,
        description="Whether file has header row"
    )
    skip_rows: int = Field(
        default=0,
        ge=0,
        description="Number of rows to skip at start"
    )

    # Column selection
    columns: Optional[List[str]] = Field(
        None,
        description="Specific columns to read (None = all)"
    )
    exclude_columns: Optional[List[str]] = Field(
        None,
        description="Columns to exclude"
    )

    # Performance settings
    chunk_size: int = Field(
        default=10000,
        ge=100,
        le=1000000,
        description="Number of rows per chunk"
    )
    max_rows: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum rows to read (None = all)"
    )

    # Type inference settings
    infer_types: bool = Field(
        default=True,
        description="Automatically infer column types"
    )
    type_inference_sample_size: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Number of rows to sample for type inference"
    )

    # Error handling
    skip_errors: bool = Field(
        default=False,
        description="Skip malformed rows instead of failing"
    )
    strict_validation: bool = Field(
        default=True,
        description="Strict validation of file structure"
    )

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate delimiter is a single character.

        Args:
            v: Delimiter value

        Returns:
            Validated delimiter

        Raises:
            ValueError: If delimiter is invalid
        """
        if v is not None and len(v) != 1:
            raise ValueError("Delimiter must be a single character")
        return v

    @field_validator("columns", "exclude_columns")
    @classmethod
    def validate_column_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validate column lists don't have duplicates.

        Args:
            v: Column list

        Returns:
            Validated column list

        Raises:
            ValueError: If duplicates found
        """
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Column list contains duplicates")
        return v

    class Config:
        """Pydantic configuration."""
        extra = "forbid"


class CSVConnector(FileConnector):
    """
    Production-ready CSV/file connector for SBDK.

    Supports CSV, TSV, JSON, JSONL, and Parquet formats with automatic
    schema detection, intelligent type inference, and memory-efficient
    streaming for large files.

    Features:
        - Automatic format and delimiter detection
        - Multiple encoding support with fallback
        - Memory-efficient chunked reading
        - Intelligent type inference from sample data
        - Column selection and filtering
        - Error handling with skip capability
        - Schema caching for performance

    Example:
        >>> from pathlib import Path
        >>> config = CSVConnectorConfig(name="sales", file_format=FileFormat.CSV)
        >>> base_config = SourceConnectionConfig(name="sales", source_type=SourceType.FILE)
        >>> connector = CSVConnector(base_config, Path("sales.csv"), csv_config=config)
        >>> with connector:
        ...     for record in connector.fetch_data():
        ...         print(record)
    """

    def __init__(
        self,
        config: SourceConnectionConfig,
        file_path: Path,
        csv_config: Optional[CSVConnectorConfig] = None
    ):
        """
        Initialize CSV connector.

        Args:
            config: Base source connection configuration
            file_path: Path to the file to read
            csv_config: CSV-specific configuration (uses defaults if None)

        Raises:
            ValidationError: If configuration is invalid
        """
        super().__init__(config, file_path)

        # Initialize CSV config with defaults
        if csv_config is None:
            csv_config = CSVConnectorConfig(
                name=config.name,
                description=config.description
            )

        self.csv_config = csv_config
        self._detected_format: Optional[FileFormat] = None
        self._detected_delimiter: Optional[str] = None
        self._detected_encoding: Optional[Encoding] = None
        self._schema_cache: Optional[SchemaInfo] = None
        self._column_types_cache: Optional[Dict[str, ColumnType]] = None

    def parse_file(self) -> Iterator[Dict[str, Any]]:
        """
        Parse file and yield records as dictionaries.

        Automatically detects file format if not specified and uses the
        appropriate parser. Yields records in chunks for memory efficiency.

        Yields:
            Parsed records as dictionaries

        Raises:
            FileSystemError: If file cannot be read
            ValidationError: If file format is unsupported or malformed

        Example:
            >>> for record in connector.parse_file():
            ...     print(f"Name: {record['name']}, Age: {record['age']}")
        """
        # Detect format if not specified
        file_format = self._get_file_format()

        # Route to appropriate parser
        if file_format == FileFormat.CSV or file_format == FileFormat.TSV:
            yield from self._parse_csv()
        elif file_format == FileFormat.JSON:
            yield from self._parse_json()
        elif file_format == FileFormat.JSONL:
            yield from self._parse_jsonl()
        elif file_format == FileFormat.PARQUET:
            yield from self._parse_parquet()
        else:
            raise ValidationError(
                f"Unsupported file format: {file_format}",
                suggestion="Supported formats: CSV, TSV, JSON, JSONL, Parquet"
            )

    def detect_schema(self, table_name: Optional[str] = None) -> SchemaInfo:
        """
        Detect schema from file with automatic type inference.

        Samples the file to determine column names and infer types from
        actual data values.

        Args:
            table_name: Optional table name (uses filename if None)

        Returns:
            SchemaInfo with detected columns and types

        Raises:
            FileSystemError: If file cannot be read
            ValidationError: If schema detection fails

        Example:
            >>> schema = connector.detect_schema()
            >>> for col in schema.columns:
            ...     print(f"{col['name']}: {col['type']}")
        """
        # Use cache if available
        if self._schema_cache is not None:
            return self._schema_cache

        table_name = table_name or self.file_path.stem

        try:
            # Sample records for type inference
            sample_records = []
            sample_size = self.csv_config.type_inference_sample_size

            for i, record in enumerate(self.parse_file()):
                if i >= sample_size:
                    break
                sample_records.append(record)

            if not sample_records:
                raise ValidationError(
                    "Cannot detect schema from empty file",
                    suggestion="Ensure file contains data rows"
                )

            # Get column names from first record
            column_names = list(sample_records[0].keys())

            # Infer types if enabled
            if self.csv_config.infer_types:
                column_types = self._infer_types(sample_records)
            else:
                column_types = {col: ColumnType.STRING for col in column_names}

            # Build column schema
            columns = []
            for col_name in column_names:
                col_type = column_types.get(col_name, ColumnType.STRING)
                columns.append({
                    "name": col_name,
                    "type": col_type.value,
                    "nullable": self._check_nullable(sample_records, col_name),
                })

            # Create schema info
            schema = SchemaInfo(
                table_name=table_name,
                columns=columns,
                row_count=self._estimate_row_count(),
                detected_at=datetime.utcnow()
            )

            # Cache the schema
            self._schema_cache = schema
            self._column_types_cache = column_types

            return schema

        except Exception as e:
            if isinstance(e, (ValidationError, FileSystemError)):
                raise
            raise FileSystemError(
                f"Schema detection failed: {e}",
                suggestion="Check file format and ensure it's not corrupted"
            ) from e

    def _parse_csv(self) -> Iterator[Dict[str, Any]]:
        """
        Parse CSV/TSV file with automatic delimiter detection.

        Yields:
            CSV records as dictionaries
        """
        delimiter = self._get_delimiter()
        encoding = self._get_encoding()

        try:
            with open(self.file_path, "r", encoding=encoding, newline="") as f:
                # Skip initial rows if configured
                for _ in range(self.csv_config.skip_rows):
                    next(f, None)

                # Create CSV reader
                reader = csv.DictReader(
                    f,
                    delimiter=delimiter,
                    quotechar=self.csv_config.quotechar,
                    escapechar=self.csv_config.escapechar
                )

                # Process rows
                row_count = 0
                max_rows = self.csv_config.max_rows

                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Filter columns if specified
                        record = self._filter_columns(row)

                        # Convert types if enabled and cached
                        if self.csv_config.infer_types and self._column_types_cache:
                            record = self._convert_types(record)

                        yield record

                        row_count += 1
                        if max_rows and row_count >= max_rows:
                            break

                    except Exception as e:
                        if self.csv_config.skip_errors:
                            continue
                        raise FileSystemError(
                            f"Error parsing CSV row {row_num}: {e}",
                            suggestion="Use skip_errors=True to skip malformed rows"
                        ) from e

        except FileNotFoundError:
            raise FileSystemError(
                f"File not found: {self.file_path}",
                suggestion="Check file path and permissions"
            )
        except UnicodeDecodeError as e:
            raise FileSystemError(
                f"Encoding error: {e}",
                suggestion=f"Try different encoding (current: {encoding})"
            ) from e

    def _parse_json(self) -> Iterator[Dict[str, Any]]:
        """
        Parse JSON file (array of objects).

        Yields:
            JSON records as dictionaries
        """
        encoding = self._get_encoding()

        try:
            with open(self.file_path, "r", encoding=encoding) as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValidationError(
                    "JSON file must contain an array of objects",
                    suggestion="Use JSONL format for line-delimited JSON"
                )

            max_rows = self.csv_config.max_rows
            for i, record in enumerate(data):
                if max_rows and i >= max_rows:
                    break

                if not isinstance(record, dict):
                    if self.csv_config.skip_errors:
                        continue
                    raise ValidationError(
                        f"JSON array must contain objects, got {type(record)}",
                        suggestion="Ensure all array elements are JSON objects"
                    )

                yield self._filter_columns(record)

        except json.JSONDecodeError as e:
            raise FileSystemError(
                f"Invalid JSON: {e}",
                suggestion="Validate JSON syntax"
            ) from e
        except FileNotFoundError:
            raise FileSystemError(
                f"File not found: {self.file_path}",
                suggestion="Check file path and permissions"
            )

    def _parse_jsonl(self) -> Iterator[Dict[str, Any]]:
        """
        Parse JSONL file (line-delimited JSON).

        Yields:
            JSONL records as dictionaries
        """
        encoding = self._get_encoding()

        try:
            with open(self.file_path, "r", encoding=encoding) as f:
                # Skip initial rows
                for _ in range(self.csv_config.skip_rows):
                    next(f, None)

                row_count = 0
                max_rows = self.csv_config.max_rows

                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        if not isinstance(record, dict):
                            if self.csv_config.skip_errors:
                                continue
                            raise ValidationError(
                                f"JSONL line must be an object, got {type(record)}",
                                suggestion="Each line must be a valid JSON object"
                            )

                        yield self._filter_columns(record)

                        row_count += 1
                        if max_rows and row_count >= max_rows:
                            break

                    except json.JSONDecodeError as e:
                        if self.csv_config.skip_errors:
                            continue
                        raise FileSystemError(
                            f"Invalid JSON on line {line_num}: {e}",
                            suggestion="Check JSON syntax on each line"
                        ) from e

        except FileNotFoundError:
            raise FileSystemError(
                f"File not found: {self.file_path}",
                suggestion="Check file path and permissions"
            )

    def _parse_parquet(self) -> Iterator[Dict[str, Any]]:
        """
        Parse Parquet file using pyarrow.

        Yields:
            Parquet records as dictionaries

        Raises:
            DependencyError: If pyarrow is not installed
        """
        try:
            import pyarrow.parquet as pq
        except ImportError:
            from sbdk.exceptions import DependencyError
            raise DependencyError(
                "pyarrow",
                reason="Required for Parquet file support"
            )

        try:
            # Read Parquet file
            table = pq.read_table(str(self.file_path))

            # Convert to batches for memory efficiency
            chunk_size = self.csv_config.chunk_size
            max_rows = self.csv_config.max_rows
            total_yielded = 0

            for batch in table.to_batches(max_chunksize=chunk_size):
                records = batch.to_pylist()

                for record in records:
                    if max_rows and total_yielded >= max_rows:
                        return

                    yield self._filter_columns(record)
                    total_yielded += 1

        except FileNotFoundError:
            raise FileSystemError(
                f"File not found: {self.file_path}",
                suggestion="Check file path and permissions"
            )
        except Exception as e:
            raise FileSystemError(
                f"Error reading Parquet file: {e}",
                suggestion="Ensure file is valid Parquet format"
            ) from e

    def _get_file_format(self) -> FileFormat:
        """
        Detect or return configured file format.

        Returns:
            Detected or configured FileFormat

        Raises:
            ValidationError: If format cannot be detected
        """
        if self._detected_format:
            return self._detected_format

        if self.csv_config.file_format:
            self._detected_format = self.csv_config.file_format
            return self._detected_format

        # Auto-detect from extension
        extension = self.file_path.suffix.lower().lstrip(".")

        format_map = {
            "csv": FileFormat.CSV,
            "tsv": FileFormat.TSV,
            "txt": FileFormat.CSV,  # Assume CSV for .txt
            "json": FileFormat.JSON,
            "jsonl": FileFormat.JSONL,
            "ndjson": FileFormat.JSONL,
            "parquet": FileFormat.PARQUET,
            "pq": FileFormat.PARQUET,
        }

        if extension in format_map:
            self._detected_format = format_map[extension]
            return self._detected_format

        raise ValidationError(
            f"Cannot detect file format from extension: {extension}",
            suggestion="Specify file_format explicitly in configuration"
        )

    def _get_delimiter(self) -> str:
        """
        Detect or return configured CSV delimiter.

        Returns:
            CSV delimiter character

        Raises:
            ValidationError: If delimiter cannot be detected
        """
        if self._detected_delimiter:
            return self._detected_delimiter

        if self.csv_config.delimiter:
            self._detected_delimiter = self.csv_config.delimiter
            return self._detected_delimiter

        # Auto-detect delimiter from first few lines
        file_format = self._get_file_format()

        if file_format == FileFormat.TSV:
            self._detected_delimiter = "\t"
            return self._detected_delimiter

        # Try to detect from file content
        encoding = self._get_encoding()

        try:
            with open(self.file_path, "r", encoding=encoding) as f:
                # Read first few lines for detection
                sample_lines = []
                for _ in range(5):
                    line = f.readline()
                    if line:
                        sample_lines.append(line)

                if not sample_lines:
                    raise ValidationError(
                        "Cannot detect delimiter from empty file",
                        suggestion="Specify delimiter explicitly"
                    )

                # Use csv.Sniffer to detect delimiter
                sniffer = csv.Sniffer()
                sample = "".join(sample_lines)
                dialect = sniffer.sniff(sample, delimiters=",;\t|")

                self._detected_delimiter = dialect.delimiter
                return self._detected_delimiter

        except Exception as e:
            # Default to comma
            self._detected_delimiter = ","
            return self._detected_delimiter

    def _get_encoding(self) -> str:
        """
        Detect or return configured file encoding.

        Tries multiple encodings with fallback to common alternatives.

        Returns:
            File encoding string
        """
        if self._detected_encoding:
            return self._detected_encoding.value

        # Try configured encoding first
        try:
            with open(self.file_path, "r", encoding=self.csv_config.encoding.value) as f:
                f.read(1024)  # Try reading first KB
            self._detected_encoding = self.csv_config.encoding
            return self._detected_encoding.value
        except UnicodeDecodeError:
            pass

        # Try common encodings with fallback
        fallback_encodings = [
            Encoding.UTF8,
            Encoding.LATIN1,
            Encoding.CP1252,
            Encoding.ASCII
        ]

        for encoding in fallback_encodings:
            try:
                with open(self.file_path, "r", encoding=encoding.value) as f:
                    f.read(1024)
                self._detected_encoding = encoding
                return encoding.value
            except UnicodeDecodeError:
                continue

        # If all fail, use latin-1 (never fails)
        self._detected_encoding = Encoding.LATIN1
        return self._detected_encoding.value

    def _filter_columns(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter record columns based on configuration.

        Args:
            record: Input record

        Returns:
            Filtered record with selected columns only
        """
        # No filtering needed
        if not self.csv_config.columns and not self.csv_config.exclude_columns:
            return record

        # Include specific columns
        if self.csv_config.columns:
            filtered = {
                k: v for k, v in record.items()
                if k in self.csv_config.columns
            }
            return filtered

        # Exclude specific columns
        if self.csv_config.exclude_columns:
            filtered = {
                k: v for k, v in record.items()
                if k not in self.csv_config.exclude_columns
            }
            return filtered

        return record

    def _infer_types(self, sample_records: List[Dict[str, Any]]) -> Dict[str, ColumnType]:
        """
        Infer column types from sample data.

        Analyzes sample records to determine the most appropriate type for
        each column based on value patterns.

        Args:
            sample_records: Sample records for type inference

        Returns:
            Dictionary mapping column names to inferred types

        Example:
            >>> records = [{"age": "25", "name": "Alice"}, {"age": "30", "name": "Bob"}]
            >>> types = connector._infer_types(records)
            >>> types["age"]
            ColumnType.INTEGER
        """
        if not sample_records:
            return {}

        column_names = list(sample_records[0].keys())
        column_types: Dict[str, ColumnType] = {}

        for col_name in column_names:
            # Collect non-null values
            values = [
                record[col_name] for record in sample_records
                if col_name in record and record[col_name] not in (None, "", "null", "NULL")
            ]

            if not values:
                column_types[col_name] = ColumnType.NULL
                continue

            # Try to infer type from values
            detected_type = self._infer_column_type(values)
            column_types[col_name] = detected_type

        return column_types

    def _infer_column_type(self, values: List[Any]) -> ColumnType:
        """
        Infer type for a single column from its values.

        Args:
            values: List of non-null values

        Returns:
            Inferred ColumnType
        """
        if not values:
            return ColumnType.NULL

        # Try boolean first (most specific)
        if all(self._is_boolean(v) for v in values):
            return ColumnType.BOOLEAN

        # Try integer
        if all(self._is_integer(v) for v in values):
            return ColumnType.INTEGER

        # Try float
        if all(self._is_float(v) for v in values):
            return ColumnType.FLOAT

        # Try datetime
        if all(self._is_datetime(v) for v in values):
            return ColumnType.DATETIME

        # Try date
        if all(self._is_date(v) for v in values):
            return ColumnType.DATE

        # Default to string
        return ColumnType.STRING

    def _is_boolean(self, value: Any) -> bool:
        """Check if value is boolean."""
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ("true", "false", "yes", "no", "1", "0", "t", "f", "y", "n")
        return False

    def _is_integer(self, value: Any) -> bool:
        """Check if value is integer."""
        if isinstance(value, int) and not isinstance(value, bool):
            return True
        if isinstance(value, str):
            try:
                int(value)
                return True
            except ValueError:
                return False
        return False

    def _is_float(self, value: Any) -> bool:
        """Check if value is float."""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False

    def _is_datetime(self, value: Any) -> bool:
        """Check if value is datetime."""
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            # Try common datetime formats
            datetime_formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
            ]
            for fmt in datetime_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
        return False

    def _is_date(self, value: Any) -> bool:
        """Check if value is date (without time)."""
        if isinstance(value, str):
            # Try common date formats
            date_formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%m-%d-%Y",
            ]
            for fmt in date_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
        return False

    def _convert_types(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert record values to inferred types.

        Args:
            record: Input record with string values

        Returns:
            Record with converted types
        """
        if not self._column_types_cache:
            return record

        converted = {}
        for key, value in record.items():
            if key not in self._column_types_cache:
                converted[key] = value
                continue

            col_type = self._column_types_cache[key]

            try:
                if value in (None, "", "null", "NULL"):
                    converted[key] = None
                elif col_type == ColumnType.INTEGER:
                    converted[key] = int(value)
                elif col_type == ColumnType.FLOAT:
                    converted[key] = float(value)
                elif col_type == ColumnType.BOOLEAN:
                    converted[key] = self._parse_boolean(value)
                elif col_type == ColumnType.DATETIME:
                    converted[key] = self._parse_datetime(value)
                elif col_type == ColumnType.DATE:
                    converted[key] = self._parse_date(value)
                else:
                    converted[key] = str(value)
            except (ValueError, TypeError):
                # Keep original value if conversion fails
                converted[key] = value

        return converted

    def _parse_boolean(self, value: Any) -> bool:
        """Parse boolean value."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "t", "y")
        return bool(value)

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime value."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            datetime_formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
            ]
            for fmt in datetime_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse date value (returns ISO format string)."""
        if isinstance(value, str):
            date_formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%m-%d-%Y",
            ]
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
        return None

    def _check_nullable(self, sample_records: List[Dict[str, Any]], column: str) -> bool:
        """
        Check if column contains null values.

        Args:
            sample_records: Sample records
            column: Column name

        Returns:
            True if column has null values
        """
        for record in sample_records:
            value = record.get(column)
            if value in (None, "", "null", "NULL"):
                return True
        return False

    def _estimate_row_count(self) -> Optional[int]:
        """
        Estimate total row count in file.

        Returns:
            Estimated row count or None if cannot estimate
        """
        file_format = self._get_file_format()

        # For CSV/TSV, count lines
        if file_format in (FileFormat.CSV, FileFormat.TSV):
            try:
                encoding = self._get_encoding()
                with open(self.file_path, "r", encoding=encoding) as f:
                    row_count = sum(1 for _ in f)
                    # Subtract header and skip rows
                    if self.csv_config.has_header:
                        row_count -= 1
                    row_count -= self.csv_config.skip_rows
                    return max(0, row_count)
            except Exception:
                return None

        # For other formats, return None (would require full file read)
        return None
