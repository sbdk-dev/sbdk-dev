"""
Comprehensive tests for SBDK Quality Framework core functionality.
"""

import json
import tempfile
from pathlib import Path

import duckdb
import pytest

from sbdk.quality.framework import (
    IssueSeverity,
    QualityError,
    QualityFramework,
    QualityIssue,
    QualityReport,
    ValidationResult,
)
from sbdk.quality.validators import NotNullValidator, UniqueValidator
from sbdk.quality.rules import Rule


class TestQualityIssue:
    """Test QualityIssue data class."""

    def test_create_issue(self):
        """Test creating a quality issue."""
        issue = QualityIssue(
            severity=IssueSeverity.ERROR,
            message="Test issue",
            table="test_table",
            column="test_column",
            row_count=5,
        )

        assert issue.severity == IssueSeverity.ERROR
        assert issue.message == "Test issue"
        assert issue.table == "test_table"
        assert issue.column == "test_column"
        assert issue.row_count == 5
        assert not issue.fixable

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        issue = QualityIssue(
            severity=IssueSeverity.CRITICAL,
            message="Critical issue",
            table="users",
            column="email",
            row_count=10,
            sample_values=["test1", "test2"],
            fixable=True,
            fix_suggestion="Fix it",
        )

        issue_dict = issue.to_dict()

        assert issue_dict["severity"] == "critical"
        assert issue_dict["message"] == "Critical issue"
        assert issue_dict["table"] == "users"
        assert issue_dict["column"] == "email"
        assert issue_dict["row_count"] == 10
        assert issue_dict["sample_values"] == ["test1", "test2"]
        assert issue_dict["fixable"] is True
        assert issue_dict["fix_suggestion"] == "Fix it"


class TestValidationResult:
    """Test ValidationResult data class."""

    def test_create_result(self):
        """Test creating a validation result."""
        result = ValidationResult(
            passed=True,
            validator_name="TestValidator",
            table="test_table",
            column="test_column",
        )

        assert result.passed is True
        assert result.validator_name == "TestValidator"
        assert result.table == "test_table"
        assert result.column == "test_column"
        assert result.issue_count == 0

    def test_result_with_issues(self):
        """Test result with quality issues."""
        issues = [
            QualityIssue(
                severity=IssueSeverity.CRITICAL,
                message="Critical",
                table="test",
            ),
            QualityIssue(
                severity=IssueSeverity.ERROR,
                message="Error",
                table="test",
            ),
            QualityIssue(
                severity=IssueSeverity.WARNING,
                message="Warning",
                table="test",
            ),
        ]

        result = ValidationResult(
            passed=False,
            validator_name="TestValidator",
            table="test",
            issues=issues,
        )

        assert result.issue_count == 3
        assert result.critical_count == 1
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = ValidationResult(
            passed=False,
            validator_name="TestValidator",
            table="test_table",
            column="test_column",
            issues=[
                QualityIssue(
                    severity=IssueSeverity.ERROR,
                    message="Test error",
                    table="test_table",
                )
            ],
            execution_time_ms=100.5,
        )

        result_dict = result.to_dict()

        assert result_dict["passed"] is False
        assert result_dict["validator_name"] == "TestValidator"
        assert result_dict["table"] == "test_table"
        assert result_dict["column"] == "test_column"
        assert result_dict["issue_count"] == 1
        assert result_dict["execution_time_ms"] == 100.5
        assert len(result_dict["issues"]) == 1


class TestQualityReport:
    """Test QualityReport data class."""

    def test_create_report(self):
        """Test creating a quality report."""
        results = [
            ValidationResult(
                passed=True,
                validator_name="Validator1",
                table="table1",
            ),
            ValidationResult(
                passed=False,
                validator_name="Validator2",
                table="table2",
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.ERROR,
                        message="Error",
                        table="table2",
                    )
                ],
            ),
        ]

        report = QualityReport(
            passed=False,
            results=results,
            total_validations=2,
            execution_time_ms=200.0,
        )

        assert report.passed is False
        assert report.total_validations == 2
        assert report.failed_validations == 1
        assert report.total_issues == 1
        assert report.execution_time_ms == 200.0

    def test_report_issue_counts(self):
        """Test report aggregates issue counts correctly."""
        results = [
            ValidationResult(
                passed=False,
                validator_name="V1",
                table="t1",
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message="C1",
                        table="t1",
                    ),
                    QualityIssue(
                        severity=IssueSeverity.ERROR,
                        message="E1",
                        table="t1",
                    ),
                ],
            ),
            ValidationResult(
                passed=False,
                validator_name="V2",
                table="t2",
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.WARNING,
                        message="W1",
                        table="t2",
                    ),
                ],
            ),
        ]

        report = QualityReport(
            passed=False,
            results=results,
            total_validations=2,
        )

        assert report.critical_issues == 1
        assert report.error_issues == 1
        assert report.warning_issues == 1
        assert report.total_issues == 3

    def test_report_to_json(self):
        """Test converting report to JSON."""
        report = QualityReport(
            passed=True,
            results=[],
            total_validations=0,
        )

        json_str = report.to_json()
        data = json.loads(json_str)

        assert data["passed"] is True
        assert data["total_validations"] == 0
        assert "timestamp" in data
        assert "results" in data

    def test_report_save_to_file(self):
        """Test saving report to file."""
        report = QualityReport(
            passed=True,
            results=[],
            total_validations=0,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "reports" / "quality_report.json"
            report.save(report_path)

            assert report_path.exists()

            with open(report_path) as f:
                data = json.load(f)

            assert data["passed"] is True


class TestQualityFramework:
    """Test QualityFramework main class."""

    @pytest.fixture
    def sample_db(self):
        """Create sample database for testing."""
        conn = duckdb.connect(":memory:")

        # Create test table with data
        conn.execute("""
            CREATE TABLE users (
                id INTEGER,
                email VARCHAR,
                age INTEGER
            )
        """)

        conn.execute("""
            INSERT INTO users VALUES
            (1, 'alice@example.com', 25),
            (2, 'bob@example.com', 30),
            (3, 'charlie@example.com', 35),
            (4, NULL, 40),
            (5, 'eve@example.com', 45)
        """)

        yield conn
        conn.close()

    def test_framework_init(self):
        """Test framework initialization."""
        framework = QualityFramework()
        assert framework.console is not None
        assert framework._connection is None

    def test_framework_with_db_path(self):
        """Test framework with database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.duckdb")

            framework = QualityFramework(db_path=db_path)
            assert framework.db_path == db_path

            # Access connection (will create the database)
            conn = framework.connection
            assert conn is not None

            framework.close()

    def test_validate_rules_success(self, sample_db):
        """Test validating rules that all pass."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="id",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)

        assert report.passed is True
        assert report.total_validations == 1
        assert report.failed_validations == 0
        assert report.total_issues == 0

    def test_validate_rules_with_failures(self, sample_db):
        """Test validating rules with failures."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="email",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)

        assert report.passed is False
        assert report.total_validations == 1
        assert report.failed_validations == 1
        assert report.total_issues >= 1

    def test_validate_multiple_rules(self, sample_db):
        """Test validating multiple rules."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="id",
                validator=UniqueValidator(),
            ),
            Rule(
                table="users",
                column="email",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)

        assert report.total_validations == 2
        assert report.failed_validations == 1  # email has null

    def test_context_manager(self):
        """Test framework as context manager."""
        with QualityFramework() as framework:
            assert framework.console is not None

        # Connection should be closed after exit
        # (if it was opened)

    def test_display_report_passed(self, sample_db, capsys):
        """Test displaying passed report."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="id",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)
        framework.display_report(report)

        # Just check it doesn't crash
        # Output will contain ANSI codes from Rich

    def test_display_report_failed(self, sample_db):
        """Test displaying failed report."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="email",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)
        framework.display_report(report)

        # Just check it doesn't crash

    def test_auto_fix_no_issues(self, sample_db):
        """Test auto-fix with no issues."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="id",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)
        framework.auto_fix(report)

        # Should complete without errors

    def test_auto_fix_with_issues(self, sample_db):
        """Test auto-fix with fixable issues."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="email",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)
        framework.auto_fix(report)

        # Should attempt to fix (though actual fixing is not implemented yet)

    def test_auto_fix_dry_run(self, sample_db):
        """Test auto-fix in dry-run mode."""
        framework = QualityFramework()
        framework._connection = sample_db

        rules = [
            Rule(
                table="users",
                column="email",
                validator=NotNullValidator(),
            ),
        ]

        report = framework.validate_rules(rules)
        framework.auto_fix(report, dry_run=True)

        # Should preview fixes without applying


class TestQualityFrameworkIntegration:
    """Integration tests for quality framework."""

    def test_full_workflow(self):
        """Test complete validation workflow."""
        # Create in-memory database
        conn = duckdb.connect(":memory:")

        # Create tables
        conn.execute("""
            CREATE TABLE products (
                id INTEGER,
                name VARCHAR,
                price DOUBLE,
                category VARCHAR
            )
        """)

        conn.execute("""
            INSERT INTO products VALUES
            (1, 'Product A', 10.99, 'Electronics'),
            (2, 'Product B', 20.50, 'Books'),
            (3, 'Product C', -5.00, 'Electronics'),
            (4, 'Product D', 15.00, NULL)
        """)

        # Create framework
        framework = QualityFramework()
        framework._connection = conn

        # Define validation rules
        from sbdk.quality.rules import not_null, range_check, unique

        rules = [
            unique("products", "id"),
            not_null("products", "name"),
            not_null("products", "category"),
            range_check("products", "price", min_value=0),
        ]

        # Run validation
        report = framework.validate_rules(rules)

        # Verify results
        assert report.total_validations == 4
        assert not report.passed  # Should fail due to negative price and null category
        assert report.failed_validations >= 2

        # Display report
        framework.display_report(report, verbose=True)

        # Save report
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report.save(report_path)
            assert report_path.exists()

        conn.close()
