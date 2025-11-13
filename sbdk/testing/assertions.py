"""
SBDK Testing Assertions

Custom assertions for data testing with clear, actionable error messages.
Extends pytest assertions with data-specific validation.

Usage:
    >>> from sbdk.testing.assertions import *
    >>> assert_dataframe_equal(actual_df, expected_df)
    >>> assert_row_count(result_df, expected=100)
"""

from typing import Optional, Union, Any, Sequence
import pandas as pd
import duckdb
from deepdiff import DeepDiff


class DataAssertionError(Exception):
    """Base exception for assertion failures with detailed messages."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize assertion error.

        Args:
            message: Human-readable error message
            details: Additional diagnostic information
        """
        self.message = message
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with details."""
        msg = f"Assertion failed: {self.message}"
        if self.details:
            msg += "\n\nDetails:"
            for key, value in self.details.items():
                msg += f"\n  {key}: {value}"
        return msg


def assert_dataframe_equal(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    check_dtype: bool = True,
    check_column_order: bool = True,
    rtol: float = 1e-5,
    atol: float = 1e-8,
) -> None:
    """
    Assert two DataFrames are equal with detailed error messages.

    Args:
        actual: Actual DataFrame
        expected: Expected DataFrame
        check_dtype: Whether to check data types
        check_column_order: Whether column order must match
        rtol: Relative tolerance for numeric comparisons
        atol: Absolute tolerance for numeric comparisons

    Raises:
        DataAssertionError: If DataFrames are not equal

    Example:
        >>> actual = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        >>> expected = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        >>> assert_dataframe_equal(actual, expected)
    """
    # Check shape
    if actual.shape != expected.shape:
        raise DataAssertionError(
            "DataFrame shapes do not match",
            details={
                "actual_shape": actual.shape,
                "expected_shape": expected.shape,
                "actual_rows": actual.shape[0],
                "expected_rows": expected.shape[0],
                "actual_columns": actual.shape[1],
                "expected_columns": expected.shape[1],
            },
        )

    # Check columns
    if check_column_order:
        if list(actual.columns) != list(expected.columns):
            raise DataAssertionError(
                "Column names or order do not match",
                details={
                    "actual_columns": list(actual.columns),
                    "expected_columns": list(expected.columns),
                    "missing_columns": list(
                        set(expected.columns) - set(actual.columns)
                    ),
                    "extra_columns": list(set(actual.columns) - set(expected.columns)),
                },
            )
    else:
        if set(actual.columns) != set(expected.columns):
            raise DataAssertionError(
                "Column names do not match",
                details={
                    "actual_columns": sorted(actual.columns),
                    "expected_columns": sorted(expected.columns),
                    "missing_columns": list(
                        set(expected.columns) - set(actual.columns)
                    ),
                    "extra_columns": list(set(actual.columns) - set(expected.columns)),
                },
            )
        # Reorder actual to match expected
        actual = actual[expected.columns]

    # Check dtypes
    if check_dtype:
        dtype_mismatches = []
        for col in expected.columns:
            if actual[col].dtype != expected[col].dtype:
                dtype_mismatches.append(
                    {
                        "column": col,
                        "actual_dtype": str(actual[col].dtype),
                        "expected_dtype": str(expected[col].dtype),
                    }
                )

        if dtype_mismatches:
            raise DataAssertionError(
                "Column data types do not match", details={"mismatches": dtype_mismatches}
            )

    # Check values
    try:
        pd.testing.assert_frame_equal(
            actual,
            expected,
            check_dtype=check_dtype,
            check_column_type=check_column_order,
            rtol=rtol,
            atol=atol,
        )
    except Exception as e:
        # Find specific differences
        diff = DeepDiff(
            expected.to_dict(orient="records"),
            actual.to_dict(orient="records"),
            ignore_order=False,
            significant_digits=6,
        )

        raise DataAssertionError(
            "DataFrame values do not match",
            details={"pandas_error": str(e), "differences": str(diff)[:500]},
        )


def assert_row_count(
    data: Union[pd.DataFrame, duckdb.DuckDBPyConnection],
    expected: int,
    query: Optional[str] = None,
) -> None:
    """
    Assert row count matches expected value.

    Args:
        data: DataFrame or DuckDB connection
        expected: Expected number of rows
        query: Optional SQL query (if data is DuckDB connection)

    Raises:
        AssertionError: If row count doesn't match

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> assert_row_count(df, expected=3)
    """
    if isinstance(data, pd.DataFrame):
        actual = len(data)
    elif isinstance(data, duckdb.DuckDBPyConnection):
        if query is None:
            raise ValueError("query is required when data is a DuckDB connection")
        actual = data.execute(f"SELECT COUNT(*) FROM ({query})").fetchone()[0]
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")

    if actual != expected:
        raise DataAssertionError(
            f"Row count mismatch",
            details={
                "expected_count": expected,
                "actual_count": actual,
                "difference": actual - expected,
            },
        )


def assert_column_exists(
    df: pd.DataFrame, column: str, column_type: Optional[type] = None
) -> None:
    """
    Assert column exists in DataFrame and optionally check type.

    Args:
        df: DataFrame to check
        column: Column name
        column_type: Optional expected column type

    Raises:
        AssertionError: If column doesn't exist or type doesn't match

    Example:
        >>> df = pd.DataFrame({'age': [25, 30]})
        >>> assert_column_exists(df, 'age', int)
    """
    if column not in df.columns:
        raise DataAssertionError(
            f"Column '{column}' does not exist",
            details={
                "available_columns": list(df.columns),
                "missing_column": column,
            },
        )

    if column_type is not None:
        actual_type = df[column].dtype
        # Convert numpy dtype to Python type for comparison
        if not pd.api.types.is_dtype_equal(actual_type, column_type):
            raise DataAssertionError(
                f"Column '{column}' has wrong type",
                details={
                    "expected_type": str(column_type),
                    "actual_type": str(actual_type),
                },
            )


def assert_columns_exist(df: pd.DataFrame, columns: Sequence[str]) -> None:
    """
    Assert multiple columns exist in DataFrame.

    Args:
        df: DataFrame to check
        columns: List of column names

    Raises:
        AssertionError: If any column doesn't exist

    Example:
        >>> df = pd.DataFrame({'a': [1], 'b': [2], 'c': [3]})
        >>> assert_columns_exist(df, ['a', 'b', 'c'])
    """
    missing = [col for col in columns if col not in df.columns]

    if missing:
        raise DataAssertionError(
            "Required columns are missing",
            details={
                "missing_columns": missing,
                "available_columns": list(df.columns),
                "required_columns": list(columns),
            },
        )


def assert_no_nulls(df: pd.DataFrame, columns: Optional[Sequence[str]] = None) -> None:
    """
    Assert no null values in specified columns.

    Args:
        df: DataFrame to check
        columns: Columns to check (default: all columns)

    Raises:
        AssertionError: If null values found

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        >>> assert_no_nulls(df)
    """
    check_columns = columns if columns is not None else df.columns

    null_counts = {}
    for col in check_columns:
        if col not in df.columns:
            raise DataAssertionError(
                f"Column '{col}' does not exist",
                details={"available_columns": list(df.columns)},
            )

        null_count = df[col].isna().sum()
        if null_count > 0:
            null_counts[col] = int(null_count)

    if null_counts:
        raise DataAssertionError(
            "Null values found in columns",
            details={
                "null_counts": null_counts,
                "total_rows": len(df),
                "null_percentage": {
                    col: f"{(count / len(df) * 100):.2f}%"
                    for col, count in null_counts.items()
                },
            },
        )


def assert_unique(df: pd.DataFrame, columns: Union[str, Sequence[str]]) -> None:
    """
    Assert values in column(s) are unique.

    Args:
        df: DataFrame to check
        columns: Column name or list of columns to check for uniqueness

    Raises:
        AssertionError: If duplicate values found

    Example:
        >>> df = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
        >>> assert_unique(df, 'id')
        >>> assert_unique(df, ['id', 'name'])
    """
    if isinstance(columns, str):
        columns = [columns]

    # Check columns exist
    for col in columns:
        if col not in df.columns:
            raise DataAssertionError(
                f"Column '{col}' does not exist",
                details={"available_columns": list(df.columns)},
            )

    # Check for duplicates
    duplicates = df[df.duplicated(subset=list(columns), keep=False)]

    if len(duplicates) > 0:
        duplicate_values = (
            duplicates[list(columns)].drop_duplicates().to_dict(orient="records")
        )

        raise DataAssertionError(
            f"Duplicate values found in {columns}",
            details={
                "duplicate_count": len(duplicates),
                "unique_duplicate_combinations": len(duplicate_values),
                "sample_duplicates": duplicate_values[:5],  # Show first 5
                "total_rows": len(df),
            },
        )


def assert_value_in_range(
    df: pd.DataFrame, column: str, min_value: Any, max_value: Any
) -> None:
    """
    Assert all values in column are within specified range.

    Args:
        df: DataFrame to check
        column: Column name
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Raises:
        AssertionError: If values outside range found

    Example:
        >>> df = pd.DataFrame({'age': [18, 25, 30, 45]})
        >>> assert_value_in_range(df, 'age', min_value=18, max_value=65)
    """
    if column not in df.columns:
        raise DataAssertionError(
            f"Column '{column}' does not exist",
            details={"available_columns": list(df.columns)},
        )

    out_of_range = df[(df[column] < min_value) | (df[column] > max_value)]

    if len(out_of_range) > 0:
        raise DataAssertionError(
            f"Values in '{column}' outside allowed range",
            details={
                "min_allowed": min_value,
                "max_allowed": max_value,
                "actual_min": df[column].min(),
                "actual_max": df[column].max(),
                "out_of_range_count": len(out_of_range),
                "sample_values": out_of_range[column].head(5).tolist(),
            },
        )


def assert_query_returns_data(
    conn: duckdb.DuckDBPyConnection, query: str, min_rows: int = 1
) -> None:
    """
    Assert query returns at least minimum number of rows.

    Args:
        conn: DuckDB connection
        query: SQL query to execute
        min_rows: Minimum number of rows expected (default: 1)

    Raises:
        AssertionError: If query returns fewer rows than expected

    Example:
        >>> assert_query_returns_data(conn, "SELECT * FROM users", min_rows=1)
    """
    try:
        result = conn.execute(query).df()
        actual_rows = len(result)

        if actual_rows < min_rows:
            raise DataAssertionError(
                "Query returned insufficient rows",
                details={
                    "query": query[:200],
                    "expected_min_rows": min_rows,
                    "actual_rows": actual_rows,
                },
            )
    except Exception as e:
        if isinstance(e, DataAssertionError):
            raise
        raise DataAssertionError(
            "Query execution failed",
            details={"query": query[:200], "error": str(e), "error_type": type(e).__name__},
        )


def assert_schema_matches(
    df: pd.DataFrame, expected_schema: dict[str, Union[type, str]]
) -> None:
    """
    Assert DataFrame schema matches expected schema.

    Args:
        df: DataFrame to check
        expected_schema: Dictionary mapping column names to expected types

    Raises:
        AssertionError: If schema doesn't match

    Example:
        >>> df = pd.DataFrame({'id': [1, 2], 'name': ['a', 'b']})
        >>> assert_schema_matches(df, {'id': 'int64', 'name': 'object'})
    """
    # Check for missing columns
    missing_columns = set(expected_schema.keys()) - set(df.columns)
    if missing_columns:
        raise DataAssertionError(
            "Schema validation failed: missing columns",
            details={
                "missing_columns": list(missing_columns),
                "actual_columns": list(df.columns),
                "expected_columns": list(expected_schema.keys()),
            },
        )

    # Check for extra columns
    extra_columns = set(df.columns) - set(expected_schema.keys())
    if extra_columns:
        raise DataAssertionError(
            "Schema validation failed: unexpected columns",
            details={
                "extra_columns": list(extra_columns),
                "actual_columns": list(df.columns),
                "expected_columns": list(expected_schema.keys()),
            },
        )

    # Check data types
    type_mismatches = []
    for col, expected_type in expected_schema.items():
        actual_type = str(df[col].dtype)
        expected_type_str = (
            expected_type if isinstance(expected_type, str) else expected_type.__name__
        )

        if actual_type != expected_type_str:
            type_mismatches.append(
                {
                    "column": col,
                    "expected_type": expected_type_str,
                    "actual_type": actual_type,
                }
            )

    if type_mismatches:
        raise DataAssertionError(
            "Schema validation failed: type mismatches",
            details={"mismatches": type_mismatches},
        )


def assert_partition_by_value_equals(
    df: pd.DataFrame,
    partition_column: str,
    partition_value: Any,
    expected_df: pd.DataFrame,
) -> None:
    """
    Assert specific partition of DataFrame matches expected data.

    Args:
        df: DataFrame to check
        partition_column: Column to partition by
        partition_value: Value to filter partition
        expected_df: Expected data for this partition

    Raises:
        AssertionError: If partition doesn't match expected

    Example:
        >>> df = pd.DataFrame({'country': ['US', 'US', 'UK'], 'count': [1, 2, 3]})
        >>> expected = pd.DataFrame({'country': ['US', 'US'], 'count': [1, 2]})
        >>> assert_partition_by_value_equals(df, 'country', 'US', expected)
    """
    if partition_column not in df.columns:
        raise DataAssertionError(
            f"Partition column '{partition_column}' does not exist",
            details={"available_columns": list(df.columns)},
        )

    partition_df = df[df[partition_column] == partition_value].reset_index(drop=True)

    try:
        assert_dataframe_equal(partition_df, expected_df)
    except DataAssertionError as e:
        e.details["partition_column"] = partition_column
        e.details["partition_value"] = partition_value
        raise


# Convenience function for common assertion combinations


def assert_valid_fact_table(
    df: pd.DataFrame,
    grain_columns: Sequence[str],
    required_columns: Optional[Sequence[str]] = None,
    no_null_columns: Optional[Sequence[str]] = None,
) -> None:
    """
    Assert DataFrame is a valid fact table with proper grain and no duplicates.

    Args:
        df: DataFrame to validate
        grain_columns: Columns defining the grain (must be unique together)
        required_columns: Columns that must exist (optional)
        no_null_columns: Columns that cannot have nulls (optional)

    Raises:
        AssertionError: If validation fails

    Example:
        >>> df = pd.DataFrame({
        ...     'date': ['2024-01-01', '2024-01-02'],
        ...     'user_id': [1, 2],
        ...     'revenue': [100, 200]
        ... })
        >>> assert_valid_fact_table(
        ...     df,
        ...     grain_columns=['date', 'user_id'],
        ...     no_null_columns=['revenue']
        ... )
    """
    # Check grain uniqueness
    assert_unique(df, grain_columns)

    # Check required columns exist
    if required_columns:
        assert_columns_exist(df, required_columns)

    # Check for nulls
    if no_null_columns:
        assert_no_nulls(df, no_null_columns)
