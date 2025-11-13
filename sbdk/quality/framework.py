"""
SBDK Quality Framework Core

Central quality validation framework for data pipelines.
Provides validation, reporting, and auto-fix capabilities.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from sbdk.exceptions import SBDKError


class QualityError(SBDKError):
    """Base exception for quality framework errors."""
    exit_code = 4


class ValidationExecutionError(QualityError):
    """Raised when validation execution fails."""
    pass


class IssueSeverity(str, Enum):
    """Severity levels for quality issues."""
    CRITICAL = "critical"  # Data corruption, blocking issues
    ERROR = "error"        # Data quality violations
    WARNING = "warning"    # Potential issues
    INFO = "info"          # Informational findings


@dataclass
class QualityIssue:
    """
    Represents a single data quality issue.

    Attributes:
        severity: Issue severity level
        message: Human-readable issue description
        table: Table name where issue was found
        column: Column name (optional)
        row_count: Number of affected rows
        sample_values: Sample of problematic values
        fixable: Whether issue can be auto-fixed
        fix_suggestion: Suggested fix action
    """
    severity: IssueSeverity
    message: str
    table: str
    column: Optional[str] = None
    row_count: int = 0
    sample_values: List[Any] = field(default_factory=list)
    fixable: bool = False
    fix_suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "table": self.table,
            "column": self.column,
            "row_count": self.row_count,
            "sample_values": self.sample_values,
            "fixable": self.fixable,
            "fix_suggestion": self.fix_suggestion,
            "metadata": self.metadata,
        }


@dataclass
class ValidationResult:
    """
    Result of a single validation check.

    Attributes:
        passed: Whether validation passed
        validator_name: Name of validator that ran
        table: Table name validated
        column: Column name (optional)
        issues: List of quality issues found
        execution_time_ms: Validation execution time
        metadata: Additional result metadata
    """
    passed: bool
    validator_name: str
    table: str
    column: Optional[str] = None
    issues: List[QualityIssue] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def issue_count(self) -> int:
        """Total number of issues found."""
        return len(self.issues)

    @property
    def critical_count(self) -> int:
        """Number of critical issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)

    @property
    def error_count(self) -> int:
        """Number of error issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Number of warning issues."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "passed": self.passed,
            "validator_name": self.validator_name,
            "table": self.table,
            "column": self.column,
            "issue_count": self.issue_count,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [issue.to_dict() for issue in self.issues],
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class QualityReport:
    """
    Comprehensive quality validation report.

    Attributes:
        passed: Whether all validations passed
        results: List of validation results
        timestamp: Report generation timestamp
        database_path: Path to database validated
        total_validations: Total number of validations run
        execution_time_ms: Total execution time
    """
    passed: bool
    results: List[ValidationResult]
    timestamp: datetime = field(default_factory=datetime.now)
    database_path: Optional[str] = None
    total_validations: int = 0
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        """Total number of issues across all validations."""
        return sum(r.issue_count for r in self.results)

    @property
    def critical_issues(self) -> int:
        """Total critical issues."""
        return sum(r.critical_count for r in self.results)

    @property
    def error_issues(self) -> int:
        """Total error issues."""
        return sum(r.error_count for r in self.results)

    @property
    def warning_issues(self) -> int:
        """Total warning issues."""
        return sum(r.warning_count for r in self.results)

    @property
    def failed_validations(self) -> int:
        """Number of failed validations."""
        return sum(1 for r in self.results if not r.passed)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "passed": self.passed,
            "timestamp": self.timestamp.isoformat(),
            "database_path": self.database_path,
            "total_validations": self.total_validations,
            "failed_validations": self.failed_validations,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "error_issues": self.error_issues,
            "warning_issues": self.warning_issues,
            "execution_time_ms": self.execution_time_ms,
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Union[str, Path]) -> None:
        """
        Save report to file.

        Args:
            path: Path to save report (JSON format)
        """
        path = Path(path) if isinstance(path, str) else path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())


class QualityFramework:
    """
    Main quality validation framework.

    Orchestrates data quality validation, reporting, and auto-fixing.
    Integrates with DuckDB and dbt for pipeline validation.

    Example:
        >>> framework = QualityFramework(db_path="data.duckdb")
        >>> from sbdk.quality.rules import RuleLoader
        >>> rules = RuleLoader.from_yaml("quality_rules.yaml")
        >>> report = framework.validate_rules(rules)
        >>> if not report.passed:
        ...     framework.display_report(report)
        ...     framework.auto_fix(report)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize quality framework.

        Args:
            db_path: Path to DuckDB database
            console: Rich console for output (default: create new)
        """
        self.db_path = db_path
        self.console = console or Console()
        self._connection: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._connection is None:
            if self.db_path:
                self._connection = duckdb.connect(self.db_path)
            else:
                self._connection = duckdb.connect(":memory:")
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def validate_rules(
        self,
        rules: List[Any],  # Will be typed as List[Rule] from rules.py
        auto_fix: bool = False,
    ) -> QualityReport:
        """
        Validate data quality using provided rules.

        Args:
            rules: List of validation rules
            auto_fix: Automatically fix issues when possible

        Returns:
            Quality report with validation results
        """
        from sbdk.quality.rules import Rule

        start_time = datetime.now()
        results: List[ValidationResult] = []

        for rule in rules:
            if not isinstance(rule, Rule):
                self.console.print(
                    f"[yellow]Skipping invalid rule: {rule}[/yellow]"
                )
                continue

            try:
                result = self._validate_rule(rule)
                results.append(result)

                # Auto-fix if enabled and issues are fixable
                if auto_fix and not result.passed:
                    self._auto_fix_result(result)

            except Exception as e:
                # Create error result
                error_result = ValidationResult(
                    passed=False,
                    validator_name=rule.validator.__class__.__name__,
                    table=rule.table,
                    column=rule.column,
                    issues=[
                        QualityIssue(
                            severity=IssueSeverity.CRITICAL,
                            message=f"Validation execution failed: {str(e)}",
                            table=rule.table,
                            column=rule.column,
                        )
                    ],
                )
                results.append(error_result)

        end_time = datetime.now()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Determine overall pass/fail
        passed = all(r.passed for r in results)

        report = QualityReport(
            passed=passed,
            results=results,
            timestamp=end_time,
            database_path=self.db_path,
            total_validations=len(results),
            execution_time_ms=execution_time_ms,
        )

        return report

    def _validate_rule(self, rule: Any) -> ValidationResult:
        """
        Execute a single validation rule.

        Args:
            rule: Validation rule to execute

        Returns:
            Validation result
        """
        start_time = datetime.now()

        # Execute validator
        result = rule.validator.validate(
            connection=self.connection,
            table=rule.table,
            column=rule.column,
        )

        end_time = datetime.now()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

        return result

    def _auto_fix_result(self, result: ValidationResult) -> None:
        """
        Attempt to auto-fix issues in validation result.

        Args:
            result: Validation result with issues
        """
        fixable_issues = [i for i in result.issues if i.fixable]

        if not fixable_issues:
            return

        self.console.print(
            f"[yellow]Auto-fixing {len(fixable_issues)} issues in {result.table}.{result.column}...[/yellow]"
        )

        for issue in fixable_issues:
            try:
                # Execute fix (implementation depends on issue type)
                if issue.fix_suggestion:
                    self.console.print(f"[dim]  {issue.fix_suggestion}[/dim]")
                    # Here you would execute the actual fix
                    # For now, just log the suggestion

            except Exception as e:
                self.console.print(f"[red]  Fix failed: {e}[/red]")

    def display_report(
        self,
        report: QualityReport,
        verbose: bool = False,
    ) -> None:
        """
        Display quality report with rich formatting.

        Args:
            report: Quality report to display
            verbose: Show detailed information
        """
        # Header
        status_color = "green" if report.passed else "red"
        status_text = "PASSED" if report.passed else "FAILED"

        self.console.print()
        self.console.print(
            Panel(
                f"[{status_color}]Quality Validation {status_text}[/{status_color}]",
                title="SBDK Quality Report",
                border_style=status_color,
            )
        )

        # Summary table
        summary = Table(show_header=False, box=None)
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="bold")

        summary.add_row("Total Validations", str(report.total_validations))
        summary.add_row("Failed Validations", str(report.failed_validations))
        summary.add_row("Total Issues", str(report.total_issues))

        if report.critical_issues > 0:
            summary.add_row(
                "Critical Issues",
                f"[red]{report.critical_issues}[/red]",
            )
        if report.error_issues > 0:
            summary.add_row(
                "Errors",
                f"[orange1]{report.error_issues}[/orange1]",
            )
        if report.warning_issues > 0:
            summary.add_row(
                "Warnings",
                f"[yellow]{report.warning_issues}[/yellow]",
            )

        summary.add_row(
            "Execution Time",
            f"{report.execution_time_ms:.2f}ms",
        )

        self.console.print(summary)
        self.console.print()

        # Failed validations
        if not report.passed:
            self.console.print("[bold]Failed Validations:[/bold]")

            for result in report.results:
                if result.passed:
                    continue

                # Create tree for each failed validation
                tree = Tree(
                    f"[red]✗[/red] {result.table}.{result.column or '*'} "
                    f"({result.validator_name})"
                )

                for issue in result.issues:
                    severity_color = {
                        IssueSeverity.CRITICAL: "red",
                        IssueSeverity.ERROR: "orange1",
                        IssueSeverity.WARNING: "yellow",
                        IssueSeverity.INFO: "blue",
                    }[issue.severity]

                    issue_text = f"[{severity_color}]{issue.severity.value.upper()}[/{severity_color}]: {issue.message}"
                    issue_branch = tree.add(issue_text)

                    if issue.row_count > 0:
                        issue_branch.add(f"Affected rows: {issue.row_count}")

                    if verbose and issue.sample_values:
                        samples = ", ".join(str(v) for v in issue.sample_values[:5])
                        issue_branch.add(f"Sample values: {samples}")

                    if issue.fixable:
                        issue_branch.add(
                            f"[green]✓ Fixable:[/green] {issue.fix_suggestion}"
                        )

                self.console.print(tree)
                self.console.print()

        # Success message
        if report.passed:
            self.console.print(
                "[green]✓ All quality validations passed![/green]"
            )

    def auto_fix(
        self,
        report: QualityReport,
        dry_run: bool = False,
    ) -> None:
        """
        Attempt to automatically fix issues in report.

        Args:
            report: Quality report with issues to fix
            dry_run: Preview fixes without applying
        """
        if report.passed:
            self.console.print("[green]No issues to fix![/green]")
            return

        fixable_count = sum(
            len([i for i in r.issues if i.fixable])
            for r in report.results
            if not r.passed
        )

        if fixable_count == 0:
            self.console.print(
                "[yellow]No auto-fixable issues found.[/yellow]"
            )
            return

        mode = "Preview" if dry_run else "Applying"
        self.console.print(
            f"[cyan]{mode} {fixable_count} auto-fixes...[/cyan]"
        )

        for result in report.results:
            if result.passed:
                continue

            if not dry_run:
                self._auto_fix_result(result)
            else:
                # Just show what would be fixed
                for issue in result.issues:
                    if issue.fixable:
                        self.console.print(
                            f"[dim]  Would fix: {issue.fix_suggestion}[/dim]"
                        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
