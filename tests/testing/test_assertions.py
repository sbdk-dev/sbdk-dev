"""
Tests for SBDK Testing Assertions

Comprehensive tests for all custom assertion functions.
"""

import pytest
import pandas as pd
import duckdb

from sbdk.testing.assertions import (
    DataAssertionError,
    assert_dataframe_equal,
    assert_row_count,
    assert_column_exists,
    assert_columns_exist,
    assert_no_nulls,
    assert_unique,
    assert_value_in_range,
    assert_query_returns_data,
    assert_schema_matches,
    assert_partition_by_value_equals,
    assert_valid_fact_table,
)


class TestDataAssertionError:
    """Test custom DataAssertionError class"""

    def test_assertion_error_basic(self):
        """Test basic assertion error"""
        error = DataAssertionError("Test failed")
        assert error.message == "Test failed"
        assert error.details == {}

    def test_assertion_error_with_details(self):
        """Test assertion error with details"""
        details = {"expected": 10, "actual": 5}
        error = DataAssertionError("Count mismatch", details=details)

        assert error.message == "Count mismatch"
        assert error.details == details

    def test_assertion_error_format_message(self):
        """Test error message formatting"""
        error = DataAssertionError(
            "Validation failed", details={"field": "age", "value": -5}
        )

        message = str(error)
        assert "Assertion failed" in message
        assert "Validation failed" in message
        assert "Details:" in message
        assert "field" in message
        assert "age" in message


class TestAssertDataframeEqual:
    """Test assert_dataframe_equal function"""

    def test_equal_dataframes(self):
        """Test that equal DataFrames pass assertion"""
        df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df2 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        # Should not raise
        assert_dataframe_equal(df1, df2)

    def test_shape_mismatch(self):
        """Test shape mismatch detection"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2]})

        with pytest.raises(DataAssertionError) as exc:
            assert_dataframe_equal(df1, df2)

        assert "shapes do not match" in str(exc.value).lower()
        assert exc.value.details["actual_rows"] == 3
        assert exc.value.details["expected_rows"] == 2

    def test_column_name_mismatch(self):
        """Test column name mismatch detection"""
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"a": [1, 2], "c": [3, 4]})

        with pytest.raises(DataAssertionError) as exc:
            assert_dataframe_equal(df1, df2)

        assert "column" in str(exc.value).lower()
        assert "missing_columns" in exc.value.details
        assert "c" in exc.value.details["missing_columns"]

    def test_column_order_mismatch(self):
        """Test column order checking"""
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"b": [3, 4], "a": [1, 2]})

        # Should fail with check_column_order=True
        with pytest.raises(DataAssertionError):
            assert_dataframe_equal(df1, df2, check_column_order=True)

        # Should pass with check_column_order=False
        assert_dataframe_equal(df1, df2, check_column_order=False)

    def test_dtype_mismatch(self):
        """Test dtype mismatch detection"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1.0, 2.0, 3.0]})

        # Should fail with check_dtype=True
        with pytest.raises(DataAssertionError) as exc:
            assert_dataframe_equal(df1, df2, check_dtype=True)

        assert "type" in str(exc.value).lower()

        # Should pass with check_dtype=False
        assert_dataframe_equal(df1, df2, check_dtype=False)

    def test_value_mismatch(self):
        """Test value mismatch detection"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2, 4]})

        with pytest.raises(DataAssertionError) as exc:
            assert_dataframe_equal(df1, df2)

        assert "values do not match" in str(exc.value).lower()


class TestAssertRowCount:
    """Test assert_row_count function"""

    def test_row_count_dataframe_success(self):
        """Test row count assertion with DataFrame"""
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        assert_row_count(df, expected=5)  # Should not raise

    def test_row_count_dataframe_failure(self):
        """Test row count mismatch with DataFrame"""
        df = pd.DataFrame({"a": [1, 2, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_row_count(df, expected=5)

        assert "Row count mismatch" in str(exc.value)
        assert exc.value.details["expected_count"] == 5
        assert exc.value.details["actual_count"] == 3
        assert exc.value.details["difference"] == -2

    def test_row_count_duckdb_success(self):
        """Test row count assertion with DuckDB connection"""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE test AS SELECT * FROM (VALUES (1), (2), (3)) AS t(id)")

        assert_row_count(conn, expected=3, query="SELECT * FROM test")
        conn.close()

    def test_row_count_duckdb_failure(self):
        """Test row count mismatch with DuckDB"""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE test AS SELECT * FROM (VALUES (1), (2)) AS t(id)")

        with pytest.raises(DataAssertionError):
            assert_row_count(conn, expected=5, query="SELECT * FROM test")

        conn.close()

    def test_row_count_duckdb_no_query_raises(self):
        """Test that DuckDB connection without query raises error"""
        conn = duckdb.connect(":memory:")

        with pytest.raises(ValueError) as exc:
            assert_row_count(conn, expected=5)

        assert "query is required" in str(exc.value)
        conn.close()


class TestAssertColumnExists:
    """Test assert_column_exists function"""

    def test_column_exists_success(self):
        """Test that existing column passes"""
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        assert_column_exists(df, "name")  # Should not raise

    def test_column_exists_failure(self):
        """Test missing column detection"""
        df = pd.DataFrame({"name": ["Alice", "Bob"]})

        with pytest.raises(DataAssertionError) as exc:
            assert_column_exists(df, "email")

        assert "does not exist" in str(exc.value)
        assert "email" in str(exc.value)
        assert "available_columns" in exc.value.details

    def test_column_exists_with_type(self):
        """Test column type validation"""
        df = pd.DataFrame({"age": [25, 30]})
        # Note: pandas dtypes are numpy dtypes, not Python types
        assert_column_exists(df, "age")  # Should pass


class TestAssertColumnsExist:
    """Test assert_columns_exist function"""

    def test_all_columns_exist_success(self):
        """Test that all columns exist"""
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        assert_columns_exist(df, ["a", "b", "c"])  # Should not raise

    def test_some_columns_missing(self):
        """Test missing columns detection"""
        df = pd.DataFrame({"a": [1], "b": [2]})

        with pytest.raises(DataAssertionError) as exc:
            assert_columns_exist(df, ["a", "b", "c", "d"])

        assert "missing" in str(exc.value).lower()
        assert exc.value.details["missing_columns"] == ["c", "d"]


class TestAssertNoNulls:
    """Test assert_no_nulls function"""

    def test_no_nulls_success(self):
        """Test DataFrame without nulls"""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert_no_nulls(df)  # Should not raise

    def test_nulls_detected(self):
        """Test null detection"""
        df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})

        with pytest.raises(DataAssertionError) as exc:
            assert_no_nulls(df)

        assert "Null values found" in str(exc.value)
        assert "null_counts" in exc.value.details
        assert exc.value.details["null_counts"]["a"] == 1
        assert exc.value.details["null_counts"]["b"] == 1

    def test_specific_columns_no_nulls(self):
        """Test checking specific columns for nulls"""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, None, 6], "c": [7, 8, 9]})

        # Should pass when checking only columns without nulls
        assert_no_nulls(df, columns=["a", "c"])

        # Should fail when checking column with nulls
        with pytest.raises(DataAssertionError):
            assert_no_nulls(df, columns=["b"])

    def test_column_not_found(self):
        """Test error when checking non-existent column"""
        df = pd.DataFrame({"a": [1, 2, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_no_nulls(df, columns=["nonexistent"])

        assert "does not exist" in str(exc.value)


class TestAssertUnique:
    """Test assert_unique function"""

    def test_unique_values_success(self):
        """Test unique values pass"""
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        assert_unique(df, "id")  # Should not raise

    def test_duplicate_values_detected(self):
        """Test duplicate detection"""
        df = pd.DataFrame({"id": [1, 2, 2, 3, 3, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_unique(df, "id")

        assert "Duplicate" in str(exc.value)
        assert exc.value.details["duplicate_count"] == 5  # 5 rows are duplicates (2 appears 2x, 3 appears 3x)

    def test_composite_uniqueness(self):
        """Test uniqueness across multiple columns"""
        df = pd.DataFrame(
            {"date": ["2024-01-01", "2024-01-01", "2024-01-02"], "user_id": [1, 2, 1]}
        )

        # Should pass - composite key is unique
        assert_unique(df, ["date", "user_id"])

        # Add duplicate composite key
        df2 = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                "user_id": [1, 2, 1],
            }
        )

        with pytest.raises(DataAssertionError):
            assert_unique(df2, ["date", "user_id"])

    def test_column_not_found(self):
        """Test error when column doesn't exist"""
        df = pd.DataFrame({"a": [1, 2, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_unique(df, "nonexistent")

        assert "does not exist" in str(exc.value)


class TestAssertValueInRange:
    """Test assert_value_in_range function"""

    def test_values_in_range_success(self):
        """Test values within range"""
        df = pd.DataFrame({"age": [18, 25, 30, 45, 65]})
        assert_value_in_range(df, "age", min_value=18, max_value=65)

    def test_values_out_of_range(self):
        """Test out of range detection"""
        df = pd.DataFrame({"age": [15, 25, 30, 70]})

        with pytest.raises(DataAssertionError) as exc:
            assert_value_in_range(df, "age", min_value=18, max_value=65)

        assert "outside allowed range" in str(exc.value)
        assert exc.value.details["min_allowed"] == 18
        assert exc.value.details["max_allowed"] == 65
        assert exc.value.details["actual_min"] == 15
        assert exc.value.details["actual_max"] == 70
        assert exc.value.details["out_of_range_count"] == 2

    def test_column_not_found(self):
        """Test error when column doesn't exist"""
        df = pd.DataFrame({"a": [1, 2, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_value_in_range(df, "nonexistent", min_value=0, max_value=10)

        assert "does not exist" in str(exc.value)


class TestAssertQueryReturnsData:
    """Test assert_query_returns_data function"""

    def test_query_returns_data_success(self):
        """Test query that returns data"""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE test AS SELECT * FROM (VALUES (1), (2), (3)) AS t(id)")

        assert_query_returns_data(conn, "SELECT * FROM test", min_rows=1)
        conn.close()

    def test_query_returns_insufficient_rows(self):
        """Test query with insufficient rows"""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE test AS SELECT * FROM (VALUES (1)) AS t(id)")

        with pytest.raises(DataAssertionError) as exc:
            assert_query_returns_data(conn, "SELECT * FROM test", min_rows=5)

        assert "insufficient rows" in str(exc.value).lower()
        assert exc.value.details["expected_min_rows"] == 5
        assert exc.value.details["actual_rows"] == 1

        conn.close()

    def test_query_execution_failure(self):
        """Test query that fails to execute"""
        conn = duckdb.connect(":memory:")

        with pytest.raises(DataAssertionError) as exc:
            assert_query_returns_data(conn, "SELECT * FROM nonexistent_table")

        assert "execution failed" in str(exc.value).lower()
        conn.close()


class TestAssertSchemaMatches:
    """Test assert_schema_matches function"""

    def test_schema_matches_success(self):
        """Test matching schema"""
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

        expected_schema = {"id": "int64", "name": "object"}

        assert_schema_matches(df, expected_schema)

    def test_missing_columns(self):
        """Test missing columns detection"""
        df = pd.DataFrame({"id": [1, 2, 3]})

        expected_schema = {"id": "int64", "name": "object"}

        with pytest.raises(DataAssertionError) as exc:
            assert_schema_matches(df, expected_schema)

        assert "missing columns" in str(exc.value).lower()
        assert "name" in exc.value.details["missing_columns"]

    def test_extra_columns(self):
        """Test extra columns detection"""
        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"], "extra": [3, 4]})

        expected_schema = {"id": "int64", "name": "object"}

        with pytest.raises(DataAssertionError) as exc:
            assert_schema_matches(df, expected_schema)

        assert "unexpected columns" in str(exc.value).lower()
        assert "extra" in exc.value.details["extra_columns"]

    def test_type_mismatch(self):
        """Test type mismatch detection"""
        df = pd.DataFrame({"id": [1.0, 2.0, 3.0]})  # float64 instead of int64

        expected_schema = {"id": "int64"}

        with pytest.raises(DataAssertionError) as exc:
            assert_schema_matches(df, expected_schema)

        assert "type mismatch" in str(exc.value).lower()
        assert len(exc.value.details["mismatches"]) == 1


class TestAssertPartitionByValueEquals:
    """Test assert_partition_by_value_equals function"""

    def test_partition_matches(self):
        """Test matching partition"""
        df = pd.DataFrame(
            {"country": ["US", "US", "UK", "UK"], "value": [1, 2, 3, 4]}
        )

        expected_us = pd.DataFrame({"country": ["US", "US"], "value": [1, 2]})

        assert_partition_by_value_equals(df, "country", "US", expected_us)

    def test_partition_mismatch(self):
        """Test partition mismatch"""
        df = pd.DataFrame({"country": ["US", "US"], "value": [1, 2]})

        expected_us = pd.DataFrame({"country": ["US", "US"], "value": [1, 3]})

        with pytest.raises(DataAssertionError) as exc:
            assert_partition_by_value_equals(df, "country", "US", expected_us)

        assert "values do not match" in str(exc.value).lower()
        assert exc.value.details["partition_column"] == "country"
        assert exc.value.details["partition_value"] == "US"

    def test_partition_column_not_found(self):
        """Test error when partition column doesn't exist"""
        df = pd.DataFrame({"value": [1, 2, 3]})
        expected = pd.DataFrame({"value": [1]})

        with pytest.raises(DataAssertionError) as exc:
            assert_partition_by_value_equals(df, "nonexistent", "value", expected)

        assert "does not exist" in str(exc.value)


class TestAssertValidFactTable:
    """Test assert_valid_fact_table function"""

    def test_valid_fact_table(self):
        """Test valid fact table"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "user_id": [1, 2, 3],
                "revenue": [100.0, 200.0, 300.0],
            }
        )

        assert_valid_fact_table(
            df,
            grain_columns=["date", "user_id"],
            required_columns=["revenue"],
            no_null_columns=["revenue"],
        )

    def test_fact_table_duplicate_grain(self):
        """Test fact table with duplicate grain"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-01"],  # Duplicate
                "user_id": [1, 1],  # Duplicate
                "revenue": [100.0, 200.0],
            }
        )

        with pytest.raises(DataAssertionError) as exc:
            assert_valid_fact_table(df, grain_columns=["date", "user_id"])

        assert "Duplicate" in str(exc.value)

    def test_fact_table_missing_required_columns(self):
        """Test fact table with missing required columns"""
        df = pd.DataFrame({"date": ["2024-01-01"], "user_id": [1]})

        with pytest.raises(DataAssertionError):
            assert_valid_fact_table(
                df, grain_columns=["date", "user_id"], required_columns=["revenue"]
            )

    def test_fact_table_with_nulls(self):
        """Test fact table with null values"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "user_id": [1, 2],
                "revenue": [100.0, None],
            }
        )

        with pytest.raises(DataAssertionError):
            assert_valid_fact_table(
                df, grain_columns=["date", "user_id"], no_null_columns=["revenue"]
            )
