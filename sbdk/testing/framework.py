"""
SBDK Testing Framework

Core testing framework for data transformations, pipeline logic, and query results.
Extends pytest with SBDK-specific functionality for testing data pipelines.

Features:
    - Data transformation testing (dbt models)
    - Pipeline execution testing
    - Snapshot testing for query results
    - Data comparison utilities
    - Test result collection and reporting
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime

import duckdb
import pandas as pd
from deepdiff import DeepDiff

from sbdk.exceptions import ValidationError, PipelineError


@dataclass
class TestResult:
    """
    Represents the result of a single test execution.

    Attributes:
        name: Test name
        status: Test status (passed, failed, skipped, error)
        duration: Test execution duration in seconds
        message: Optional message (e.g., failure reason)
        details: Additional test details
        timestamp: Test execution timestamp
    """

    name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float = 0.0
    message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert test result to dictionary representation."""
        return {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TestSuite:
    """
    Collection of test results with summary statistics.

    Attributes:
        name: Test suite name
        results: List of test results
        start_time: Suite start time
        end_time: Suite end time
    """

    name: str
    results: list[TestResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def add_result(self, result: TestResult) -> None:
        """Add a test result to the suite."""
        self.results.append(result)

    @property
    def total_tests(self) -> int:
        """Total number of tests."""
        return len(self.results)

    @property
    def passed(self) -> int:
        """Number of passed tests."""
        return sum(1 for r in self.results if r.status == "passed")

    @property
    def failed(self) -> int:
        """Number of failed tests."""
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def skipped(self) -> int:
        """Number of skipped tests."""
        return sum(1 for r in self.results if r.status == "skipped")

    @property
    def errors(self) -> int:
        """Number of errored tests."""
        return sum(1 for r in self.results if r.status == "error")

    @property
    def duration(self) -> float:
        """Total duration of all tests in seconds."""
        return sum(r.duration for r in self.results)

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert test suite to dictionary representation."""
        return {
            "name": self.name,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration": self.duration,
            "success_rate": self.success_rate,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": [r.to_dict() for r in self.results],
        }


class DataTransformationTester:
    """
    Test data transformations (dbt models, SQL queries, etc.).

    Provides utilities for testing data transformations with configurable
    comparison options and clear failure messages.

    Example:
        >>> tester = DataTransformationTester(db_path="test.db")
        >>> result = tester.test_query(
        ...     "SELECT * FROM users WHERE age > 18",
        ...     expected_count=5
        ... )
        >>> assert result.status == "passed"
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        connection: Optional[duckdb.DuckDBPyConnection] = None,
    ):
        """
        Initialize data transformation tester.

        Args:
            db_path: Path to DuckDB database file (default: in-memory)
            connection: Existing DuckDB connection to use

        Raises:
            ValidationError: If both db_path and connection are provided
        """
        if db_path and connection:
            raise ValidationError(
                "Cannot specify both db_path and connection",
                suggestion="Provide either db_path or connection, not both",
            )

        self.connection = connection or duckdb.connect(db_path or ":memory:")

    def test_query(
        self,
        query: str,
        expected_count: Optional[int] = None,
        expected_columns: Optional[list[str]] = None,
        expected_data: Optional[pd.DataFrame] = None,
        name: Optional[str] = None,
    ) -> TestResult:
        """
        Test a SQL query against expectations.

        Args:
            query: SQL query to execute
            expected_count: Expected number of rows (optional)
            expected_columns: Expected column names (optional)
            expected_data: Expected result DataFrame (optional)
            name: Test name (defaults to query)

        Returns:
            TestResult indicating pass/fail status

        Example:
            >>> result = tester.test_query(
            ...     "SELECT id, name FROM users",
            ...     expected_count=10,
            ...     expected_columns=["id", "name"]
            ... )
        """
        test_name = name or query[:50]
        start_time = datetime.now()

        try:
            # Execute query
            result_df = self.connection.execute(query).df()

            # Validate row count
            if expected_count is not None:
                actual_count = len(result_df)
                if actual_count != expected_count:
                    return TestResult(
                        name=test_name,
                        status="failed",
                        duration=(datetime.now() - start_time).total_seconds(),
                        message=f"Row count mismatch: expected {expected_count}, got {actual_count}",
                        details={
                            "query": query,
                            "expected_count": expected_count,
                            "actual_count": actual_count,
                        },
                    )

            # Validate columns
            if expected_columns is not None:
                actual_columns = list(result_df.columns)
                if actual_columns != expected_columns:
                    return TestResult(
                        name=test_name,
                        status="failed",
                        duration=(datetime.now() - start_time).total_seconds(),
                        message=f"Column mismatch: expected {expected_columns}, got {actual_columns}",
                        details={
                            "query": query,
                            "expected_columns": expected_columns,
                            "actual_columns": actual_columns,
                        },
                    )

            # Validate data
            if expected_data is not None:
                if not result_df.equals(expected_data):
                    diff = DeepDiff(
                        expected_data.to_dict(), result_df.to_dict(), ignore_order=True
                    )
                    return TestResult(
                        name=test_name,
                        status="failed",
                        duration=(datetime.now() - start_time).total_seconds(),
                        message="Data mismatch",
                        details={
                            "query": query,
                            "diff": str(diff),
                        },
                    )

            # All checks passed
            return TestResult(
                name=test_name,
                status="passed",
                duration=(datetime.now() - start_time).total_seconds(),
            )

        except Exception as e:
            return TestResult(
                name=test_name,
                status="error",
                duration=(datetime.now() - start_time).total_seconds(),
                message=str(e),
                details={"query": query, "error_type": type(e).__name__},
            )

    def close(self) -> None:
        """Close database connection."""
        self.connection.close()


class SnapshotTester:
    """
    Snapshot testing for query results and data transformations.

    Captures query results as snapshots and compares against them in future runs.
    Useful for regression testing of data transformations.

    Example:
        >>> tester = SnapshotTester(snapshot_dir=".snapshots")
        >>> tester.assert_matches_snapshot(
        ...     "user_metrics",
        ...     df,
        ...     update_snapshots=False
        ... )
    """

    def __init__(self, snapshot_dir: Union[str, Path] = ".snapshots"):
        """
        Initialize snapshot tester.

        Args:
            snapshot_dir: Directory to store snapshot files
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _get_snapshot_path(self, name: str) -> Path:
        """Get path to snapshot file."""
        # Sanitize name for filesystem
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return self.snapshot_dir / f"{safe_name}.json"

    def _compute_hash(self, data: Any) -> str:
        """Compute hash of data for comparison."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def capture_snapshot(
        self, name: str, data: Union[pd.DataFrame, dict[str, Any], list[Any]]
    ) -> None:
        """
        Capture data as a snapshot.

        Args:
            name: Snapshot name
            data: Data to snapshot (DataFrame, dict, or list)
        """
        snapshot_path = self._get_snapshot_path(name)

        # Convert DataFrame to dict for JSON serialization
        if isinstance(data, pd.DataFrame):
            snapshot_data = {
                "type": "dataframe",
                "data": data.to_dict(orient="records"),
                "columns": list(data.columns),
                "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
            }
        else:
            snapshot_data = {"type": "data", "data": data}

        # Add metadata
        snapshot_data["captured_at"] = datetime.now().isoformat()
        snapshot_data["hash"] = self._compute_hash(snapshot_data["data"])

        # Write snapshot
        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2, default=str)

    def load_snapshot(self, name: str) -> dict[str, Any]:
        """
        Load snapshot from file.

        Args:
            name: Snapshot name

        Returns:
            Snapshot data dictionary

        Raises:
            ValidationError: If snapshot not found
        """
        snapshot_path = self._get_snapshot_path(name)

        if not snapshot_path.exists():
            raise ValidationError(
                f"Snapshot '{name}' not found",
                suggestion=f"Create snapshot with update_snapshots=True or check path: {snapshot_path}",
            )

        with open(snapshot_path, "r") as f:
            return json.load(f)

    def assert_matches_snapshot(
        self,
        name: str,
        data: Union[pd.DataFrame, dict[str, Any], list[Any]],
        update_snapshots: bool = False,
    ) -> TestResult:
        """
        Assert that data matches saved snapshot.

        Args:
            name: Snapshot name
            data: Data to compare
            update_snapshots: If True, update snapshot instead of comparing

        Returns:
            TestResult indicating match status

        Example:
            >>> result = tester.assert_matches_snapshot(
            ...     "user_summary",
            ...     summary_df,
            ...     update_snapshots=False
            ... )
        """
        start_time = datetime.now()

        # Convert data format
        if isinstance(data, pd.DataFrame):
            current_data = data.to_dict(orient="records")
        else:
            current_data = data

        # Update mode: save new snapshot
        if update_snapshots:
            self.capture_snapshot(name, data)
            return TestResult(
                name=f"snapshot:{name}",
                status="passed",
                duration=(datetime.now() - start_time).total_seconds(),
                message="Snapshot updated",
            )

        # Compare mode: load and compare
        try:
            snapshot = self.load_snapshot(name)
            snapshot_data = snapshot["data"]

            # Compare data
            diff = DeepDiff(snapshot_data, current_data, ignore_order=True)

            if diff:
                return TestResult(
                    name=f"snapshot:{name}",
                    status="failed",
                    duration=(datetime.now() - start_time).total_seconds(),
                    message="Snapshot mismatch",
                    details={
                        "diff": str(diff),
                        "snapshot_hash": snapshot.get("hash"),
                        "current_hash": self._compute_hash(current_data),
                    },
                )

            return TestResult(
                name=f"snapshot:{name}",
                status="passed",
                duration=(datetime.now() - start_time).total_seconds(),
            )

        except ValidationError as e:
            return TestResult(
                name=f"snapshot:{name}",
                status="error",
                duration=(datetime.now() - start_time).total_seconds(),
                message=str(e.message),
            )


class PipelineTester:
    """
    Test pipeline execution and validation.

    Provides utilities for testing entire pipeline runs, including setup,
    execution, and validation of results.

    Example:
        >>> tester = PipelineTester()
        >>> result = tester.run_pipeline_test(
        ...     setup=lambda: setup_test_data(),
        ...     execute=lambda: run_pipeline(),
        ...     validate=lambda: check_results()
        ... )
    """

    def run_pipeline_test(
        self,
        setup: Optional[Callable[[], None]] = None,
        execute: Callable[[], Any] = None,
        validate: Optional[Callable[[], bool]] = None,
        teardown: Optional[Callable[[], None]] = None,
        name: str = "pipeline_test",
    ) -> TestResult:
        """
        Run a complete pipeline test with setup, execution, and validation.

        Args:
            setup: Optional setup function to run before execution
            execute: Pipeline execution function (required)
            validate: Optional validation function (returns True for pass)
            teardown: Optional teardown function to run after test
            name: Test name

        Returns:
            TestResult indicating success/failure

        Example:
            >>> result = tester.run_pipeline_test(
            ...     setup=lambda: conn.execute("CREATE TABLE test AS SELECT 1"),
            ...     execute=lambda: run_dbt_model("test_model"),
            ...     validate=lambda: conn.execute("SELECT COUNT(*) FROM result").fetchone()[0] > 0
            ... )
        """
        if execute is None:
            raise ValidationError(
                "execute function is required",
                suggestion="Provide an execute function that runs your pipeline",
            )

        start_time = datetime.now()

        try:
            # Setup phase
            if setup:
                setup()

            # Execute phase
            result = execute()

            # Validate phase
            if validate:
                is_valid = validate()
                if not is_valid:
                    return TestResult(
                        name=name,
                        status="failed",
                        duration=(datetime.now() - start_time).total_seconds(),
                        message="Validation failed",
                    )

            return TestResult(
                name=name,
                status="passed",
                duration=(datetime.now() - start_time).total_seconds(),
                details={"result": str(result)[:100] if result else None},
            )

        except Exception as e:
            return TestResult(
                name=name,
                status="error",
                duration=(datetime.now() - start_time).total_seconds(),
                message=str(e),
                details={"error_type": type(e).__name__},
            )

        finally:
            # Teardown phase (always runs)
            if teardown:
                try:
                    teardown()
                except Exception as e:
                    # Log teardown errors but don't fail the test
                    pass


def run_test_suite(
    tests: list[Callable[[], TestResult]], suite_name: str = "SBDK Test Suite"
) -> TestSuite:
    """
    Run a collection of tests and return results.

    Args:
        tests: List of test functions that return TestResult
        suite_name: Name for the test suite

    Returns:
        TestSuite with all results

    Example:
        >>> def test_users():
        ...     tester = DataTransformationTester()
        ...     return tester.test_query("SELECT * FROM users", expected_count=10)
        >>>
        >>> suite = run_test_suite([test_users], suite_name="User Tests")
        >>> print(f"Passed: {suite.passed}/{suite.total_tests}")
    """
    suite = TestSuite(name=suite_name, start_time=datetime.now())

    for test_func in tests:
        try:
            result = test_func()
            suite.add_result(result)
        except Exception as e:
            # Catch any unexpected errors and record them
            suite.add_result(
                TestResult(
                    name=getattr(test_func, "__name__", "unknown_test"),
                    status="error",
                    message=f"Test function raised exception: {str(e)}",
                    details={"error_type": type(e).__name__},
                )
            )

    suite.end_time = datetime.now()
    return suite
