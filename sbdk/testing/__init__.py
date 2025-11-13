"""
SBDK Testing Framework

Comprehensive testing utilities for data transformations, pipelines, and queries.

This module provides:
    - DataTransformationTester: Test SQL queries and dbt models
    - SnapshotTester: Regression testing with snapshots
    - PipelineTester: Test complete pipeline execution
    - Custom assertions: Data-specific assertions with clear errors
    - Pytest fixtures: Reusable test fixtures for common scenarios

Quick Start:
    >>> from sbdk.testing import DataTransformationTester, assert_row_count
    >>>
    >>> # Test a query
    >>> tester = DataTransformationTester()
    >>> result = tester.test_query(
    ...     "SELECT * FROM users WHERE age > 18",
    ...     expected_count=100
    ... )
    >>> assert result.status == "passed"
    >>>
    >>> # Use assertions
    >>> import pandas as pd
    >>> df = pd.DataFrame({'id': [1, 2, 3]})
    >>> assert_row_count(df, expected=3)

Testing Features:
    - Query result validation
    - Data transformation testing
    - Snapshot-based regression testing
    - Pipeline execution testing
    - Schema validation
    - Data quality assertions

See Also:
    - sbdk.testing.framework: Core testing classes
    - sbdk.testing.assertions: Custom assertion functions
    - sbdk.testing.fixtures: Pytest fixtures
"""

# Framework classes
from sbdk.testing.framework import (
    TestResult,
    TestSuite,
    DataTransformationTester,
    SnapshotTester,
    PipelineTester,
    run_test_suite,
)

# Assertion functions
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

# Version
__version__ = "1.0.0"

# Public API
__all__ = [
    # Core framework
    "TestResult",
    "TestSuite",
    "DataTransformationTester",
    "SnapshotTester",
    "PipelineTester",
    "run_test_suite",
    # Assertions
    "DataAssertionError",
    "assert_dataframe_equal",
    "assert_row_count",
    "assert_column_exists",
    "assert_columns_exist",
    "assert_no_nulls",
    "assert_unique",
    "assert_value_in_range",
    "assert_query_returns_data",
    "assert_schema_matches",
    "assert_partition_by_value_equals",
    "assert_valid_fact_table",
]
