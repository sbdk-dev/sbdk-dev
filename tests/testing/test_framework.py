"""
Comprehensive tests for SBDK Testing Framework

Tests all core framework functionality including:
- TestResult and TestSuite classes
- DataTransformationTester
- SnapshotTester
- PipelineTester
- Test suite execution

Target: 95%+ code coverage
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import duckdb

from sbdk.testing.framework import (
    TestResult,
    TestSuite,
    DataTransformationTester,
    SnapshotTester,
    PipelineTester,
    run_test_suite,
)
from sbdk.exceptions import ValidationError


class TestTestResult:
    """Test TestResult class"""

    def test_test_result_creation(self):
        """Test creating a test result"""
        result = TestResult(
            name="test_example", status="passed", duration=1.5, message="Success"
        )

        assert result.name == "test_example"
        assert result.status == "passed"
        assert result.duration == 1.5
        assert result.message == "Success"
        assert isinstance(result.timestamp, datetime)

    def test_test_result_defaults(self):
        """Test TestResult default values"""
        result = TestResult(name="test", status="passed")

        assert result.duration == 0.0
        assert result.message is None
        assert result.details == {}

    def test_test_result_to_dict(self):
        """Test converting TestResult to dictionary"""
        result = TestResult(
            name="test_convert",
            status="failed",
            duration=2.3,
            message="Test failed",
            details={"error": "ValueError"},
        )

        result_dict = result.to_dict()

        assert result_dict["name"] == "test_convert"
        assert result_dict["status"] == "failed"
        assert result_dict["duration"] == 2.3
        assert result_dict["message"] == "Test failed"
        assert result_dict["details"] == {"error": "ValueError"}
        assert "timestamp" in result_dict

    def test_test_result_with_details(self):
        """Test TestResult with complex details"""
        details = {"query": "SELECT * FROM users", "rows": 100, "time_ms": 150}

        result = TestResult(
            name="query_test", status="passed", duration=0.15, details=details
        )

        assert result.details == details
        assert result.to_dict()["details"] == details


class TestTestSuite:
    """Test TestSuite class"""

    def test_test_suite_creation(self):
        """Test creating a test suite"""
        suite = TestSuite(name="My Test Suite")

        assert suite.name == "My Test Suite"
        assert suite.results == []
        assert suite.start_time is None
        assert suite.end_time is None

    def test_add_result(self):
        """Test adding results to suite"""
        suite = TestSuite(name="Suite")

        result1 = TestResult(name="test1", status="passed", duration=1.0)
        result2 = TestResult(name="test2", status="failed", duration=2.0)

        suite.add_result(result1)
        suite.add_result(result2)

        assert len(suite.results) == 2
        assert suite.results[0] == result1
        assert suite.results[1] == result2

    def test_suite_statistics(self):
        """Test suite statistics calculation"""
        suite = TestSuite(name="Stats Suite")

        suite.add_result(TestResult(name="test1", status="passed", duration=1.0))
        suite.add_result(TestResult(name="test2", status="passed", duration=1.5))
        suite.add_result(TestResult(name="test3", status="failed", duration=0.5))
        suite.add_result(TestResult(name="test4", status="skipped", duration=0.0))
        suite.add_result(TestResult(name="test5", status="error", duration=0.2))

        assert suite.total_tests == 5
        assert suite.passed == 2
        assert suite.failed == 1
        assert suite.skipped == 1
        assert suite.errors == 1
        assert suite.duration == 3.2
        assert suite.success_rate == 40.0  # 2/5 = 40%

    def test_suite_empty_statistics(self):
        """Test statistics for empty suite"""
        suite = TestSuite(name="Empty Suite")

        assert suite.total_tests == 0
        assert suite.passed == 0
        assert suite.failed == 0
        assert suite.skipped == 0
        assert suite.errors == 0
        assert suite.duration == 0.0
        assert suite.success_rate == 0.0

    def test_suite_to_dict(self):
        """Test converting suite to dictionary"""
        suite = TestSuite(
            name="Convert Suite",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
        )

        suite.add_result(TestResult(name="test1", status="passed", duration=1.0))
        suite.add_result(TestResult(name="test2", status="failed", duration=2.0))

        suite_dict = suite.to_dict()

        assert suite_dict["name"] == "Convert Suite"
        assert suite_dict["total_tests"] == 2
        assert suite_dict["passed"] == 1
        assert suite_dict["failed"] == 1
        assert suite_dict["duration"] == 3.0
        assert suite_dict["success_rate"] == 50.0
        assert len(suite_dict["results"]) == 2


class TestDataTransformationTester:
    """Test DataTransformationTester class"""

    def test_tester_creation_in_memory(self):
        """Test creating tester with in-memory database"""
        tester = DataTransformationTester()
        assert tester.connection is not None
        tester.close()

    def test_tester_creation_with_path(self, tmp_path):
        """Test creating tester with database file"""
        db_path = tmp_path / "test.db"
        tester = DataTransformationTester(db_path=str(db_path))

        assert tester.connection is not None
        tester.close()
        assert db_path.exists()

    def test_tester_creation_with_connection(self):
        """Test creating tester with existing connection"""
        conn = duckdb.connect(":memory:")
        tester = DataTransformationTester(connection=conn)

        assert tester.connection == conn
        tester.close()

    def test_tester_creation_both_path_and_connection_raises(self):
        """Test that providing both db_path and connection raises error"""
        conn = duckdb.connect(":memory:")

        with pytest.raises(ValidationError) as exc:
            DataTransformationTester(db_path="test.db", connection=conn)

        assert "Cannot specify both" in str(exc.value.message)
        conn.close()

    def test_query_test_with_count(self):
        """Test query validation with expected count"""
        tester = DataTransformationTester()
        tester.connection.execute(
            "CREATE TABLE users AS SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob'), (3, 'Charlie')) AS t(id, name)"
        )

        result = tester.test_query(
            "SELECT * FROM users", expected_count=3, name="count_test"
        )

        assert result.status == "passed"
        assert result.name == "count_test"
        assert result.duration > 0
        tester.close()

    def test_query_test_count_mismatch(self):
        """Test query validation with count mismatch"""
        tester = DataTransformationTester()
        tester.connection.execute("CREATE TABLE users AS SELECT 1 as id")

        result = tester.test_query("SELECT * FROM users", expected_count=5)

        assert result.status == "failed"
        assert "Row count mismatch" in result.message
        assert result.details["expected_count"] == 5
        assert result.details["actual_count"] == 1
        tester.close()

    def test_query_test_with_columns(self):
        """Test query validation with expected columns"""
        tester = DataTransformationTester()
        tester.connection.execute(
            "CREATE TABLE users AS SELECT 1 as id, 'Alice' as name, 25 as age"
        )

        result = tester.test_query(
            "SELECT id, name, age FROM users", expected_columns=["id", "name", "age"]
        )

        assert result.status == "passed"
        tester.close()

    def test_query_test_column_mismatch(self):
        """Test query validation with column mismatch"""
        tester = DataTransformationTester()
        tester.connection.execute("CREATE TABLE users AS SELECT 1 as id, 'Alice' as name")

        result = tester.test_query(
            "SELECT * FROM users", expected_columns=["id", "email"]
        )

        assert result.status == "failed"
        assert "Column mismatch" in result.message
        assert result.details["expected_columns"] == ["id", "email"]
        tester.close()

    def test_query_test_with_expected_data(self):
        """Test query validation with expected DataFrame"""
        tester = DataTransformationTester()
        tester.connection.execute(
            "CREATE TABLE users AS SELECT * FROM (VALUES (1, 'Alice'), (2, 'Bob')) AS t(id, name)"
        )

        # Get actual result to match dtypes
        actual_result = tester.connection.execute("SELECT * FROM users ORDER BY id").df()
        expected_df = actual_result.copy()

        result = tester.test_query(
            "SELECT * FROM users ORDER BY id", expected_data=expected_df
        )

        assert result.status == "passed"
        tester.close()

    def test_query_test_data_mismatch(self):
        """Test query validation with data mismatch"""
        tester = DataTransformationTester()
        tester.connection.execute(
            "CREATE TABLE users AS SELECT * FROM (VALUES (1, 'Alice')) AS t(id, name)"
        )

        expected_df = pd.DataFrame({"id": [1], "name": ["Bob"]})

        result = tester.test_query("SELECT * FROM users", expected_data=expected_df)

        assert result.status == "failed"
        assert "Data mismatch" in result.message
        tester.close()

    def test_query_test_with_error(self):
        """Test query that raises error"""
        tester = DataTransformationTester()

        result = tester.test_query("SELECT * FROM nonexistent_table")

        assert result.status == "error"
        assert result.message is not None
        assert "Catalog Error" in result.message or "not found" in result.message
        tester.close()


class TestSnapshotTester:
    """Test SnapshotTester class"""

    def test_snapshot_tester_creation(self, tmp_path):
        """Test creating snapshot tester"""
        snapshot_dir = tmp_path / ".snapshots"
        tester = SnapshotTester(snapshot_dir=snapshot_dir)

        assert tester.snapshot_dir == snapshot_dir
        assert snapshot_dir.exists()

    def test_capture_snapshot_dataframe(self, tmp_path):
        """Test capturing DataFrame snapshot"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        df = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})
        tester.capture_snapshot("test_df", df)

        snapshot_path = tester._get_snapshot_path("test_df")
        assert snapshot_path.exists()

    def test_capture_snapshot_dict(self, tmp_path):
        """Test capturing dict snapshot"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        data = {"key1": "value1", "key2": [1, 2, 3]}
        tester.capture_snapshot("test_dict", data)

        snapshot_path = tester._get_snapshot_path("test_dict")
        assert snapshot_path.exists()

    def test_load_snapshot(self, tmp_path):
        """Test loading snapshot"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        data = {"test": "data"}
        tester.capture_snapshot("loadtest", data)

        loaded = tester.load_snapshot("loadtest")

        assert loaded["type"] == "data"
        assert loaded["data"] == data
        assert "captured_at" in loaded
        assert "hash" in loaded

    def test_load_snapshot_not_found(self, tmp_path):
        """Test loading non-existent snapshot raises error"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        with pytest.raises(ValidationError) as exc:
            tester.load_snapshot("nonexistent")

        assert "not found" in str(exc.value.message)

    def test_assert_matches_snapshot_first_time(self, tmp_path):
        """Test snapshot match with update mode"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        result = tester.assert_matches_snapshot("new_snapshot", df, update_snapshots=True)

        assert result.status == "passed"
        assert "updated" in result.message.lower()

    def test_assert_matches_snapshot_success(self, tmp_path):
        """Test successful snapshot match"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})

        # Create snapshot
        tester.capture_snapshot("match_test", df)

        # Test match
        result = tester.assert_matches_snapshot("match_test", df, update_snapshots=False)

        assert result.status == "passed"

    def test_assert_matches_snapshot_mismatch(self, tmp_path):
        """Test snapshot mismatch"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        df1 = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        df2 = pd.DataFrame({"id": [1, 2], "name": ["a", "c"]})  # Different data

        # Create snapshot with df1
        tester.capture_snapshot("mismatch_test", df1)

        # Test with df2
        result = tester.assert_matches_snapshot(
            "mismatch_test", df2, update_snapshots=False
        )

        assert result.status == "failed"
        assert "mismatch" in result.message.lower()

    def test_assert_matches_snapshot_not_found(self, tmp_path):
        """Test snapshot match when snapshot doesn't exist"""
        tester = SnapshotTester(snapshot_dir=tmp_path)

        df = pd.DataFrame({"id": [1]})
        result = tester.assert_matches_snapshot("missing", df, update_snapshots=False)

        assert result.status == "error"
        assert "not found" in result.message.lower()


class TestPipelineTester:
    """Test PipelineTester class"""

    def test_pipeline_tester_creation(self):
        """Test creating pipeline tester"""
        tester = PipelineTester()
        assert tester is not None

    def test_run_pipeline_test_success(self):
        """Test successful pipeline execution"""
        tester = PipelineTester()

        setup_called = []
        execute_called = []
        validate_called = []
        teardown_called = []

        def setup():
            setup_called.append(True)

        def execute():
            execute_called.append(True)
            return "success"

        def validate():
            validate_called.append(True)
            return True

        def teardown():
            teardown_called.append(True)

        result = tester.run_pipeline_test(
            setup=setup,
            execute=execute,
            validate=validate,
            teardown=teardown,
            name="test_pipeline",
        )

        assert result.status == "passed"
        assert result.name == "test_pipeline"
        assert len(setup_called) == 1
        assert len(execute_called) == 1
        assert len(validate_called) == 1
        assert len(teardown_called) == 1

    def test_run_pipeline_test_no_execute_raises(self):
        """Test that missing execute function raises error"""
        tester = PipelineTester()

        with pytest.raises(ValidationError) as exc:
            tester.run_pipeline_test(execute=None, name="no_execute")

        assert "execute function is required" in str(exc.value.message)

    def test_run_pipeline_test_validation_failure(self):
        """Test pipeline with failed validation"""
        tester = PipelineTester()

        def execute():
            return "executed"

        def validate():
            return False  # Validation fails

        result = tester.run_pipeline_test(
            execute=execute, validate=validate, name="fail_validation"
        )

        assert result.status == "failed"
        assert "Validation failed" in result.message

    def test_run_pipeline_test_execution_error(self):
        """Test pipeline with execution error"""
        tester = PipelineTester()

        def execute():
            raise ValueError("Something went wrong")

        result = tester.run_pipeline_test(execute=execute, name="error_test")

        assert result.status == "error"
        assert "Something went wrong" in result.message

    def test_run_pipeline_test_teardown_always_runs(self):
        """Test that teardown runs even if execution fails"""
        tester = PipelineTester()

        teardown_called = []

        def execute():
            raise ValueError("Execution failed")

        def teardown():
            teardown_called.append(True)

        result = tester.run_pipeline_test(
            execute=execute, teardown=teardown, name="teardown_test"
        )

        assert result.status == "error"
        assert len(teardown_called) == 1  # Teardown still ran

    def test_run_pipeline_test_without_setup_validate_teardown(self):
        """Test pipeline with only execute function"""
        tester = PipelineTester()

        def execute():
            return "minimal"

        result = tester.run_pipeline_test(execute=execute, name="minimal_test")

        assert result.status == "passed"
        assert result.name == "minimal_test"


class TestRunTestSuite:
    """Test run_test_suite function"""

    def test_run_test_suite_success(self):
        """Test running a suite of successful tests"""

        def test1():
            return TestResult(name="test1", status="passed", duration=1.0)

        def test2():
            return TestResult(name="test2", status="passed", duration=1.5)

        suite = run_test_suite([test1, test2], suite_name="Success Suite")

        assert suite.name == "Success Suite"
        assert suite.total_tests == 2
        assert suite.passed == 2
        assert suite.failed == 0
        assert suite.start_time is not None
        assert suite.end_time is not None

    def test_run_test_suite_mixed_results(self):
        """Test running suite with mixed results"""

        def test_pass():
            return TestResult(name="pass", status="passed")

        def test_fail():
            return TestResult(name="fail", status="failed")

        def test_skip():
            return TestResult(name="skip", status="skipped")

        suite = run_test_suite(
            [test_pass, test_fail, test_skip], suite_name="Mixed Suite"
        )

        assert suite.total_tests == 3
        assert suite.passed == 1
        assert suite.failed == 1
        assert suite.skipped == 1

    def test_run_test_suite_with_exception(self):
        """Test running suite where a test raises exception"""

        def test_ok():
            return TestResult(name="ok", status="passed")

        def test_raises():
            raise ValueError("Test function crashed")

        suite = run_test_suite([test_ok, test_raises], suite_name="Exception Suite")

        assert suite.total_tests == 2
        assert suite.passed == 1
        assert suite.errors == 1

        error_result = [r for r in suite.results if r.status == "error"][0]
        assert "Test function raised exception" in error_result.message

    def test_run_test_suite_empty(self):
        """Test running empty test suite"""
        suite = run_test_suite([], suite_name="Empty Suite")

        assert suite.total_tests == 0
        assert suite.passed == 0
        assert suite.failed == 0
