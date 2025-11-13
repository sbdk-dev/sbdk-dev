"""
SBDK Test Command

Run tests for SBDK projects using the testing framework.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sbdk.formatters import create_formatter
from sbdk.exceptions import ValidationError, PipelineError

console = Console()

cli_test = typer.Typer(
    name="test",
    help="Run tests for SBDK project",
    rich_markup_mode="rich"
)


@cli_test.command("run")
def test_run(
    path: Optional[str] = typer.Argument(
        None,
        help="Path to test file or directory (default: tests/)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output with detailed test information"
    ),
    coverage: bool = typer.Option(
        False,
        "--coverage",
        "-c",
        help="Generate coverage report"
    ),
    markers: Optional[str] = typer.Option(
        None,
        "--markers",
        "-m",
        help="Run tests matching markers (e.g., 'dbt', 'not slow')"
    ),
    keyword: Optional[str] = typer.Option(
        None,
        "--keyword",
        "-k",
        help="Run tests matching keyword expression"
    ),
    html_report: bool = typer.Option(
        False,
        "--html",
        help="Generate HTML coverage report"
    ),
    fail_under: Optional[int] = typer.Option(
        None,
        "--fail-under",
        help="Fail if coverage is below this percentage"
    ),
):
    """
    Run tests using pytest with SBDK testing framework.

    Examples:
        # Run all tests
        sbdk test run

        # Run specific test file
        sbdk test run tests/test_pipeline.py

        # Run with coverage
        sbdk test run --coverage

        # Run only dbt tests
        sbdk test run --markers dbt

        # Run tests excluding slow tests
        sbdk test run --markers "not slow"

        # Run tests with keyword
        sbdk test run --keyword "user"

        # Generate HTML coverage report
        sbdk test run --coverage --html

        # Fail if coverage below 95%
        sbdk test run --coverage --fail-under 95
    """
    formatter = create_formatter(quiet=False)

    # Default test path
    test_path = path or "tests/"

    # Build pytest command
    pytest_args = [sys.executable, "-m", "pytest"]

    # Add test path
    pytest_args.append(test_path)

    # Add verbosity
    if verbose:
        pytest_args.append("-vv")
    else:
        pytest_args.append("-v")

    # Add coverage options
    if coverage:
        pytest_args.extend([
            "--cov=sbdk",
            "--cov-report=term-missing",
        ])

        if html_report:
            pytest_args.append("--cov-report=html")

        if fail_under:
            pytest_args.append(f"--cov-fail-under={fail_under}")

    # Add markers
    if markers:
        pytest_args.extend(["-m", markers])

    # Add keyword filter
    if keyword:
        pytest_args.extend(["-k", keyword])

    # Show command being run
    if verbose:
        formatter.info("Running pytest", details={"command": " ".join(pytest_args)})

    # Run pytest
    try:
        result = subprocess.run(pytest_args, cwd=Path.cwd())

        if result.returncode == 0:
            formatter.success(
                "All tests passed!",
                details={"test_path": test_path}
            )
        else:
            formatter.warning(
                "Some tests failed",
                details={"exit_code": result.returncode}
            )
            raise typer.Exit(result.returncode)

    except FileNotFoundError:
        formatter.error(
            "pytest not found",
            suggestion="Install pytest: uv add --dev pytest pytest-cov"
        )
        raise typer.Exit(2)

    except Exception as e:
        formatter.error(
            f"Test execution failed: {str(e)}",
            suggestion="Check pytest installation and test files"
        )
        raise typer.Exit(1)


@cli_test.command("create")
def test_create(
    name: str = typer.Argument(..., help="Test file name (without .py extension)"),
    test_type: str = typer.Option(
        "unit",
        "--type",
        "-t",
        help="Test type: unit, integration, dbt, pipeline"
    ),
    output_dir: str = typer.Option(
        "tests",
        "--output",
        "-o",
        help="Output directory for test file"
    ),
):
    """
    Create a new test file with template code.

    Examples:
        # Create unit test
        sbdk test create test_users

        # Create dbt test
        sbdk test create test_user_metrics --type dbt

        # Create pipeline test
        sbdk test create test_etl_pipeline --type pipeline
    """
    formatter = create_formatter(quiet=False)

    # Ensure name doesn't have .py extension
    if name.endswith(".py"):
        name = name[:-3]

    # Ensure name starts with test_
    if not name.startswith("test_"):
        name = f"test_{name}"

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create test file
    test_file_path = output_path / f"{name}.py"

    if test_file_path.exists():
        raise ValidationError(
            f"Test file already exists: {test_file_path}",
            suggestion="Use a different name or delete the existing file"
        )

    # Generate template based on type
    template = _get_test_template(name, test_type)

    # Write test file
    test_file_path.write_text(template)

    formatter.success(
        f"Test file created: {test_file_path}",
        details={
            "type": test_type,
            "path": str(test_file_path)
        }
    )


@cli_test.command("list-fixtures")
def list_fixtures():
    """
    List available SBDK testing fixtures.

    Shows all pytest fixtures provided by the SBDK testing framework.
    """
    formatter = create_formatter(quiet=False)

    # Create table of fixtures
    table = Table(title="SBDK Testing Fixtures", show_header=True)
    table.add_column("Fixture", style="cyan", width=25)
    table.add_column("Description", style="white")
    table.add_column("Returns", style="green")

    fixtures = [
        ("temp_db", "In-memory DuckDB connection", "DuckDBConnection"),
        ("temp_db_file", "File-based DuckDB connection", "(Path, DuckDBConnection)"),
        ("sample_users_df", "Sample user data (100 rows)", "DataFrame"),
        ("sample_orders_df", "Sample order data (200 rows)", "DataFrame"),
        ("sample_events_df", "Sample event data (500 rows)", "DataFrame"),
        ("populated_db", "DuckDB with sample data loaded", "DuckDBConnection"),
        ("temp_project_dir", "Temporary SBDK project structure", "Path"),
        ("snapshot_dir", "Directory for snapshot testing", "Path"),
        ("mock_dbt_project", "Mock dbt project with models", "Path"),
        ("test_data_generator", "Faker instance for test data", "Faker"),
        ("time_series_data", "Time series data (90 days)", "DataFrame"),
    ]

    for fixture_name, description, returns in fixtures:
        table.add_row(fixture_name, description, returns)

    console.print()
    console.print(table)
    console.print()

    console.print("[bold]Usage:[/bold]")
    console.print("  Import in your test files:")
    console.print("  [cyan]from sbdk.testing.fixtures import *[/cyan]")
    console.print()
    console.print("  Then use in tests:")
    console.print("  [cyan]def test_example(temp_db, sample_users_df):[/cyan]")
    console.print("      [dim]# Test code here[/dim]")
    console.print()


def _get_test_template(name: str, test_type: str) -> str:
    """Generate test template based on type."""

    if test_type == "unit":
        return f'''"""
Unit tests for {name}
"""

import pytest
from sbdk.testing import assert_row_count, assert_dataframe_equal


class Test{name.replace("test_", "").title().replace("_", "")}:
    """Test class for {name}"""

    def test_example(self):
        """Example test case"""
        # Arrange
        expected = 42

        # Act
        actual = 42

        # Assert
        assert actual == expected

    def test_with_fixture(self, temp_db):
        """Example test using SBDK fixture"""
        # Create test data
        temp_db.execute("CREATE TABLE test AS SELECT 1 as id, 'Alice' as name")

        # Query data
        result = temp_db.execute("SELECT COUNT(*) FROM test").fetchone()

        # Assert
        assert result == (1,)
'''

    elif test_type == "dbt":
        return f'''"""
dbt model tests for {name}
"""

import pytest
from sbdk.testing import (
    DataTransformationTester,
    assert_row_count,
    assert_no_nulls,
    assert_unique
)


@pytest.mark.dbt
class Test{name.replace("test_", "").title().replace("_", "")}:
    """Test dbt models"""

    def test_model_execution(self, populated_db):
        """Test that dbt model executes successfully"""
        tester = DataTransformationTester(connection=populated_db)

        # Test query (replace with your model logic)
        result = tester.test_query(
            "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id",
            expected_count=None  # Will vary based on data
        )

        assert result.status == "passed"

    def test_model_data_quality(self, populated_db):
        """Test data quality of model output"""
        # Execute model query
        result_df = populated_db.execute(
            "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id"
        ).df()

        # Assert data quality
        assert_no_nulls(result_df, columns=["user_id"])
        assert_unique(result_df, "user_id")
        assert_row_count(result_df, expected=len(result_df))  # Flexible count
'''

    elif test_type == "pipeline":
        return f'''"""
Pipeline tests for {name}
"""

import pytest
from sbdk.testing import PipelineTester, assert_row_count


@pytest.mark.pipeline
class Test{name.replace("test_", "").title().replace("_", "")}:
    """Test pipeline execution"""

    def test_pipeline_success(self, temp_db):
        """Test successful pipeline execution"""
        tester = PipelineTester()

        # Define pipeline stages
        def setup():
            temp_db.execute("CREATE TABLE source AS SELECT 1 as id")

        def execute():
            # Run your pipeline logic
            temp_db.execute(
                "CREATE TABLE target AS SELECT id, id * 2 as doubled FROM source"
            )
            return "Pipeline completed"

        def validate():
            result = temp_db.execute("SELECT COUNT(*) FROM target").fetchone()
            return result[0] > 0

        # Run pipeline test
        result = tester.run_pipeline_test(
            setup=setup,
            execute=execute,
            validate=validate,
            name="pipeline_execution"
        )

        assert result.status == "passed"
'''

    elif test_type == "integration":
        return f'''"""
Integration tests for {name}
"""

import pytest
from sbdk.testing import DataTransformationTester, SnapshotTester


@pytest.mark.integration
class Test{name.replace("test_", "").title().replace("_", "")}:
    """Integration tests"""

    def test_end_to_end(self, populated_db, snapshot_dir):
        """Test end-to-end data flow"""
        # Run query
        result_df = populated_db.execute(
            \"\"\"
            SELECT
                u.user_id,
                u.name,
                COUNT(o.order_id) as total_orders,
                SUM(o.amount) as total_amount
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.name
            \"\"\"
        ).df()

        # Test with snapshot
        tester = SnapshotTester(snapshot_dir)
        snapshot_result = tester.assert_matches_snapshot(
            "end_to_end_result",
            result_df,
            update_snapshots=False  # Set to True to update snapshot
        )

        assert snapshot_result.status == "passed"
'''

    else:
        # Default template
        return f'''"""
Tests for {name}
"""

import pytest


class Test{name.replace("test_", "").title().replace("_", "")}:
    """Test class for {name}"""

    def test_placeholder(self):
        """Placeholder test"""
        assert True
'''


# Export the app
app = cli_test


if __name__ == "__main__":
    cli_test()
