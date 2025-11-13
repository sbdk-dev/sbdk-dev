"""
SBDK Quality Validators

Built-in and custom validators for data quality checks.
Each validator checks a specific quality dimension (nulls, uniqueness, schema, ranges, etc.).
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

import duckdb

from sbdk.quality.framework import (
    IssueSeverity,
    QualityIssue,
    ValidationResult,
)


class BaseValidator(ABC):
    """
    Abstract base class for all quality validators.

    Subclasses must implement the validate() method to perform
    specific quality checks on data.
    """

    def __init__(self, severity: IssueSeverity = IssueSeverity.ERROR):
        """
        Initialize validator.

        Args:
            severity: Default severity for issues found by this validator
        """
        self.severity = severity

    @abstractmethod
    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """
        Execute validation check.

        Args:
            connection: DuckDB connection
            table: Table name to validate
            column: Column name (optional, for column-level checks)

        Returns:
            ValidationResult with pass/fail and any issues found
        """
        pass

    def _create_result(
        self,
        table: str,
        column: Optional[str] = None,
        passed: bool = True,
        issues: Optional[List[QualityIssue]] = None,
    ) -> ValidationResult:
        """
        Helper to create ValidationResult.

        Args:
            table: Table name
            column: Column name
            passed: Whether validation passed
            issues: List of issues found

        Returns:
            ValidationResult instance
        """
        return ValidationResult(
            passed=passed,
            validator_name=self.__class__.__name__,
            table=table,
            column=column,
            issues=issues or [],
        )


class NotNullValidator(BaseValidator):
    """
    Validates that a column contains no NULL values.

    Example:
        >>> validator = NotNullValidator()
        >>> result = validator.validate(conn, "users", "email")
        >>> print(result.passed)
        True
    """

    def __init__(
        self,
        severity: IssueSeverity = IssueSeverity.ERROR,
        allow_empty_string: bool = False,
    ):
        """
        Initialize not-null validator.

        Args:
            severity: Issue severity for null values
            allow_empty_string: Whether to treat empty strings as valid
        """
        super().__init__(severity)
        self.allow_empty_string = allow_empty_string

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Validate no NULL values in column."""
        if not column:
            return self._create_result(
                table,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message="NotNullValidator requires a column name",
                        table=table,
                    )
                ],
            )

        # Count NULL values
        if self.allow_empty_string:
            query = f"""
                SELECT COUNT(*) as null_count
                FROM {table}
                WHERE {column} IS NULL
            """
        else:
            query = f"""
                SELECT COUNT(*) as null_count
                FROM {table}
                WHERE {column} IS NULL OR TRIM(CAST({column} AS VARCHAR)) = ''
            """

        try:
            result = connection.execute(query).fetchone()
            null_count = result[0] if result else 0

            if null_count == 0:
                return self._create_result(table, column, passed=True)

            # Get sample NULL rows
            sample_query = f"""
                SELECT *
                FROM {table}
                WHERE {column} IS NULL
                LIMIT 5
            """
            samples = connection.execute(sample_query).fetchall()

            issue = QualityIssue(
                severity=self.severity,
                message=f"Found {null_count} NULL values in column '{column}'",
                table=table,
                column=column,
                row_count=null_count,
                sample_values=[None] * min(null_count, 5),
                fixable=True,
                fix_suggestion=f"DELETE FROM {table} WHERE {column} IS NULL",
            )

            return self._create_result(
                table,
                column,
                passed=False,
                issues=[issue],
            )

        except Exception as e:
            return self._create_result(
                table,
                column,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        table=table,
                        column=column,
                    )
                ],
            )


class UniqueValidator(BaseValidator):
    """
    Validates that a column contains only unique values (no duplicates).

    Example:
        >>> validator = UniqueValidator()
        >>> result = validator.validate(conn, "users", "email")
        >>> print(result.passed)
        True
    """

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Validate uniqueness of column values."""
        if not column:
            return self._create_result(
                table,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message="UniqueValidator requires a column name",
                        table=table,
                    )
                ],
            )

        try:
            # Find duplicate values
            query = f"""
                SELECT {column}, COUNT(*) as count
                FROM {table}
                WHERE {column} IS NOT NULL
                GROUP BY {column}
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """

            duplicates = connection.execute(query).fetchall()

            if not duplicates:
                return self._create_result(table, column, passed=True)

            # Count total duplicate rows
            dup_count_query = f"""
                SELECT SUM(count - 1) as total_dups
                FROM (
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE {column} IS NOT NULL
                    GROUP BY {column}
                    HAVING COUNT(*) > 1
                ) dups
            """
            total_dups = connection.execute(dup_count_query).fetchone()[0]

            duplicate_values = [dup[0] for dup in duplicates]

            issue = QualityIssue(
                severity=self.severity,
                message=f"Found {total_dups} duplicate values in column '{column}'",
                table=table,
                column=column,
                row_count=int(total_dups),
                sample_values=duplicate_values,
                fixable=True,
                fix_suggestion=f"Keep only first occurrence: DELETE FROM {table} WHERE rowid NOT IN (SELECT MIN(rowid) FROM {table} GROUP BY {column})",
            )

            return self._create_result(
                table,
                column,
                passed=False,
                issues=[issue],
            )

        except Exception as e:
            return self._create_result(
                table,
                column,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        table=table,
                        column=column,
                    )
                ],
            )


class SchemaValidator(BaseValidator):
    """
    Validates that table schema matches expected definition.

    Example:
        >>> validator = SchemaValidator(expected_columns={"id": "INTEGER", "name": "VARCHAR"})
        >>> result = validator.validate(conn, "users")
        >>> print(result.passed)
        True
    """

    def __init__(
        self,
        expected_columns: Dict[str, str],
        severity: IssueSeverity = IssueSeverity.ERROR,
        allow_extra_columns: bool = False,
    ):
        """
        Initialize schema validator.

        Args:
            expected_columns: Dict of column_name -> expected_type
            severity: Issue severity for schema mismatches
            allow_extra_columns: Whether to allow additional columns not in expected
        """
        super().__init__(severity)
        self.expected_columns = expected_columns
        self.allow_extra_columns = allow_extra_columns

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Validate table schema matches expected definition."""
        try:
            # Get actual schema
            schema_query = f"DESCRIBE {table}"
            schema_result = connection.execute(schema_query).fetchall()

            actual_columns = {
                row[0]: row[1] for row in schema_result
            }

            issues: List[QualityIssue] = []

            # Check for missing columns
            for col_name, expected_type in self.expected_columns.items():
                if col_name not in actual_columns:
                    issues.append(
                        QualityIssue(
                            severity=self.severity,
                            message=f"Missing column '{col_name}' (expected type: {expected_type})",
                            table=table,
                            column=col_name,
                            fixable=True,
                            fix_suggestion=f"ALTER TABLE {table} ADD COLUMN {col_name} {expected_type}",
                        )
                    )
                elif not self._types_compatible(actual_columns[col_name], expected_type):
                    issues.append(
                        QualityIssue(
                            severity=self.severity,
                            message=f"Column '{col_name}' has type '{actual_columns[col_name]}' but expected '{expected_type}'",
                            table=table,
                            column=col_name,
                            fixable=False,
                            fix_suggestion=f"Consider recreating table or using CAST in queries",
                        )
                    )

            # Check for extra columns
            if not self.allow_extra_columns:
                for col_name in actual_columns:
                    if col_name not in self.expected_columns:
                        issues.append(
                            QualityIssue(
                                severity=IssueSeverity.WARNING,
                                message=f"Unexpected column '{col_name}' (type: {actual_columns[col_name]})",
                                table=table,
                                column=col_name,
                                fixable=True,
                                fix_suggestion=f"ALTER TABLE {table} DROP COLUMN {col_name}",
                            )
                        )

            passed = len(issues) == 0

            return self._create_result(
                table,
                passed=passed,
                issues=issues,
            )

        except Exception as e:
            return self._create_result(
                table,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        table=table,
                    )
                ],
            )

    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual type is compatible with expected type."""
        # Normalize types for comparison
        actual = actual.upper()
        expected = expected.upper()

        # Exact match
        if actual == expected:
            return True

        # Common compatible types
        compatible_types = {
            "VARCHAR": ["TEXT", "STRING", "CHAR"],
            "INTEGER": ["INT", "BIGINT", "SMALLINT"],
            "DOUBLE": ["FLOAT", "REAL", "NUMERIC"],
            "TIMESTAMP": ["DATETIME", "DATE"],
        }

        for base_type, aliases in compatible_types.items():
            if expected == base_type and actual in aliases:
                return True
            if actual == base_type and expected in aliases:
                return True

        return False


class RangeValidator(BaseValidator):
    """
    Validates that numeric column values fall within expected range.

    Example:
        >>> validator = RangeValidator(min_value=0, max_value=100)
        >>> result = validator.validate(conn, "products", "price")
        >>> print(result.passed)
        True
    """

    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        severity: IssueSeverity = IssueSeverity.ERROR,
    ):
        """
        Initialize range validator.

        Args:
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
            severity: Issue severity for out-of-range values
        """
        super().__init__(severity)
        self.min_value = min_value
        self.max_value = max_value

        if min_value is None and max_value is None:
            raise ValueError("At least one of min_value or max_value must be specified")

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Validate column values are within range."""
        if not column:
            return self._create_result(
                table,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message="RangeValidator requires a column name",
                        table=table,
                    )
                ],
            )

        try:
            # Build WHERE clause for out-of-range values
            conditions = []
            if self.min_value is not None:
                conditions.append(f"{column} < {self.min_value}")
            if self.max_value is not None:
                conditions.append(f"{column} > {self.max_value}")

            where_clause = " OR ".join(conditions)

            # Count out-of-range values
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table}
                WHERE {column} IS NOT NULL AND ({where_clause})
            """

            count_result = connection.execute(count_query).fetchone()
            out_of_range_count = count_result[0] if count_result else 0

            if out_of_range_count == 0:
                return self._create_result(table, column, passed=True)

            # Get sample out-of-range values
            sample_query = f"""
                SELECT {column}
                FROM {table}
                WHERE {column} IS NOT NULL AND ({where_clause})
                ORDER BY {column}
                LIMIT 5
            """
            samples = connection.execute(sample_query).fetchall()
            sample_values = [row[0] for row in samples]

            range_desc = f"range [{self.min_value}, {self.max_value}]"
            if self.min_value is None:
                range_desc = f"<= {self.max_value}"
            elif self.max_value is None:
                range_desc = f">= {self.min_value}"

            issue = QualityIssue(
                severity=self.severity,
                message=f"Found {out_of_range_count} values outside {range_desc} in column '{column}'",
                table=table,
                column=column,
                row_count=out_of_range_count,
                sample_values=sample_values,
                fixable=True,
                fix_suggestion=f"DELETE FROM {table} WHERE {where_clause}",
            )

            return self._create_result(
                table,
                column,
                passed=False,
                issues=[issue],
            )

        except Exception as e:
            return self._create_result(
                table,
                column,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        table=table,
                        column=column,
                    )
                ],
            )


class PatternValidator(BaseValidator):
    """
    Validates that string column values match expected regex pattern.

    Example:
        >>> validator = PatternValidator(pattern=r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
        >>> result = validator.validate(conn, "users", "email")
        >>> print(result.passed)
        True
    """

    def __init__(
        self,
        pattern: str,
        severity: IssueSeverity = IssueSeverity.ERROR,
    ):
        """
        Initialize pattern validator.

        Args:
            pattern: Regex pattern to match
            severity: Issue severity for non-matching values
        """
        super().__init__(severity)
        self.pattern = pattern

        # Validate regex pattern
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Validate column values match pattern."""
        if not column:
            return self._create_result(
                table,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message="PatternValidator requires a column name",
                        table=table,
                    )
                ],
            )

        try:
            # Count values that don't match pattern
            # DuckDB uses regexp_matches for regex matching
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table}
                WHERE {column} IS NOT NULL
                  AND NOT regexp_matches({column}, '{self.pattern}')
            """

            count_result = connection.execute(count_query).fetchone()
            non_matching_count = count_result[0] if count_result else 0

            if non_matching_count == 0:
                return self._create_result(table, column, passed=True)

            # Get sample non-matching values
            sample_query = f"""
                SELECT {column}
                FROM {table}
                WHERE {column} IS NOT NULL
                  AND NOT regexp_matches({column}, '{self.pattern}')
                LIMIT 5
            """
            samples = connection.execute(sample_query).fetchall()
            sample_values = [row[0] for row in samples]

            issue = QualityIssue(
                severity=self.severity,
                message=f"Found {non_matching_count} values not matching pattern '{self.pattern}' in column '{column}'",
                table=table,
                column=column,
                row_count=non_matching_count,
                sample_values=sample_values,
                fixable=False,
                fix_suggestion=f"Review and correct values that don't match the expected pattern",
            )

            return self._create_result(
                table,
                column,
                passed=False,
                issues=[issue],
            )

        except Exception as e:
            return self._create_result(
                table,
                column,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Validation failed: {str(e)}",
                        table=table,
                        column=column,
                    )
                ],
            )


class CustomValidator(BaseValidator):
    """
    Allows custom validation logic via user-provided function.

    Example:
        >>> def check_age(conn, table, column):
        ...     # Custom validation logic
        ...     return True, []  # passed, issues
        >>> validator = CustomValidator(check_age)
        >>> result = validator.validate(conn, "users", "age")
    """

    def __init__(
        self,
        validation_func: Callable[
            [duckdb.DuckDBPyConnection, str, Optional[str]],
            tuple[bool, List[QualityIssue]],
        ],
        name: str = "CustomValidator",
        severity: IssueSeverity = IssueSeverity.ERROR,
    ):
        """
        Initialize custom validator.

        Args:
            validation_func: Function that performs validation
                Should return (passed: bool, issues: List[QualityIssue])
            name: Name for the validator
            severity: Default severity for issues
        """
        super().__init__(severity)
        self.validation_func = validation_func
        self.name = name

    def validate(
        self,
        connection: duckdb.DuckDBPyConnection,
        table: str,
        column: Optional[str] = None,
    ) -> ValidationResult:
        """Execute custom validation function."""
        try:
            passed, issues = self.validation_func(connection, table, column)

            return ValidationResult(
                passed=passed,
                validator_name=self.name,
                table=table,
                column=column,
                issues=issues,
            )

        except Exception as e:
            return self._create_result(
                table,
                column,
                passed=False,
                issues=[
                    QualityIssue(
                        severity=IssueSeverity.CRITICAL,
                        message=f"Custom validation failed: {str(e)}",
                        table=table,
                        column=column,
                    )
                ],
            )
