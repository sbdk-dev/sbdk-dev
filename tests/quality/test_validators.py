"""
Comprehensive tests for SBDK Quality Validators.
"""

import pytest
import duckdb

from sbdk.quality.framework import IssueSeverity
from sbdk.quality.validators import (
    BaseValidator,
    NotNullValidator,
    UniqueValidator,
    SchemaValidator,
    RangeValidator,
    PatternValidator,
    CustomValidator,
)


@pytest.fixture
def test_db():
    """Create test database with sample data."""
    conn = duckdb.connect(":memory:")

    # Users table with various data quality issues
    conn.execute("""
        CREATE TABLE users (
            id INTEGER,
            email VARCHAR,
            age INTEGER,
            username VARCHAR
        )
    """)

    conn.execute("""
        INSERT INTO users VALUES
        (1, 'alice@example.com', 25, 'alice'),
        (2, 'bob@example.com', 30, 'bob'),
        (3, NULL, 35, 'charlie'),
        (4, 'david@example.com', -5, 'david'),
        (5, 'eve@example.com', 150, 'eve'),
        (6, 'alice@example.com', 28, 'alice')  -- Duplicate email and username
    """)

    # Products table
    conn.execute("""
        CREATE TABLE products (
            id INTEGER,
            name VARCHAR,
            price DOUBLE,
            sku VARCHAR
        )
    """)

    conn.execute("""
        INSERT INTO products VALUES
        (1, 'Product A', 10.99, 'SKU-001'),
        (2, 'Product B', 20.50, 'INVALID'),
        (3, 'Product C', -5.00, 'SKU-003'),
        (4, NULL, 15.00, 'SKU-004')
    """)

    yield conn
    conn.close()


class TestNotNullValidator:
    """Test NotNullValidator."""

    def test_not_null_passes(self, test_db):
        """Test not-null validation passes when no nulls."""
        validator = NotNullValidator()
        result = validator.validate(test_db, "users", "id")

        assert result.passed is True
        assert result.issue_count == 0

    def test_not_null_fails_with_nulls(self, test_db):
        """Test not-null validation fails with null values."""
        validator = NotNullValidator()
        result = validator.validate(test_db, "users", "email")

        assert result.passed is False
        assert result.issue_count == 1
        assert result.issues[0].severity == IssueSeverity.ERROR
        assert "NULL" in result.issues[0].message
        assert result.issues[0].row_count == 1

    def test_not_null_fixable(self, test_db):
        """Test not-null validation marks issues as fixable."""
        validator = NotNullValidator()
        result = validator.validate(test_db, "users", "email")

        assert result.passed is False
        assert result.issues[0].fixable is True
        assert result.issues[0].fix_suggestion is not None

    def test_not_null_requires_column(self, test_db):
        """Test not-null validation requires column name."""
        validator = NotNullValidator()
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert "requires a column" in result.issues[0].message

    def test_not_null_with_custom_severity(self, test_db):
        """Test not-null validator with custom severity."""
        validator = NotNullValidator(severity=IssueSeverity.CRITICAL)
        result = validator.validate(test_db, "users", "email")

        assert result.passed is False
        assert result.issues[0].severity == IssueSeverity.CRITICAL

    def test_not_null_allow_empty_string(self, test_db):
        """Test not-null validator allowing empty strings."""
        # Add row with empty string
        test_db.execute("INSERT INTO users VALUES (7, '', 40, 'frank')")

        validator_strict = NotNullValidator(allow_empty_string=False)
        result_strict = validator_strict.validate(test_db, "users", "email")

        validator_lenient = NotNullValidator(allow_empty_string=True)
        result_lenient = validator_lenient.validate(test_db, "users", "email")

        # Strict should catch empty string
        assert result_strict.passed is False
        assert result_strict.issues[0].row_count >= 2  # NULL + empty string

        # Lenient should only catch NULL
        assert result_lenient.passed is False
        assert result_lenient.issues[0].row_count == 1  # Only NULL


class TestUniqueValidator:
    """Test UniqueValidator."""

    def test_unique_passes(self, test_db):
        """Test uniqueness validation passes when all unique."""
        validator = UniqueValidator()
        result = validator.validate(test_db, "users", "id")

        assert result.passed is True
        assert result.issue_count == 0

    def test_unique_fails_with_duplicates(self, test_db):
        """Test uniqueness validation fails with duplicates."""
        validator = UniqueValidator()
        result = validator.validate(test_db, "users", "email")

        assert result.passed is False
        assert result.issue_count == 1
        assert "duplicate" in result.issues[0].message.lower()
        assert result.issues[0].row_count > 0

    def test_unique_sample_values(self, test_db):
        """Test uniqueness validation includes sample duplicate values."""
        validator = UniqueValidator()
        result = validator.validate(test_db, "users", "email")

        assert result.passed is False
        assert len(result.issues[0].sample_values) > 0
        assert "alice@example.com" in result.issues[0].sample_values

    def test_unique_fixable(self, test_db):
        """Test uniqueness validation marks issues as fixable."""
        validator = UniqueValidator()
        result = validator.validate(test_db, "users", "username")

        assert result.passed is False
        assert result.issues[0].fixable is True
        assert result.issues[0].fix_suggestion is not None

    def test_unique_requires_column(self, test_db):
        """Test unique validation requires column name."""
        validator = UniqueValidator()
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert "requires a column" in result.issues[0].message


class TestSchemaValidator:
    """Test SchemaValidator."""

    def test_schema_exact_match(self, test_db):
        """Test schema validation with exact match."""
        expected = {
            "id": "INTEGER",
            "email": "VARCHAR",
            "age": "INTEGER",
            "username": "VARCHAR",
        }

        validator = SchemaValidator(expected)
        result = validator.validate(test_db, "users")

        assert result.passed is True
        assert result.issue_count == 0

    def test_schema_missing_column(self, test_db):
        """Test schema validation detects missing columns."""
        expected = {
            "id": "INTEGER",
            "email": "VARCHAR",
            "age": "INTEGER",
            "username": "VARCHAR",
            "phone": "VARCHAR",  # Missing column
        }

        validator = SchemaValidator(expected)
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert result.issue_count == 1
        assert "Missing column 'phone'" in result.issues[0].message

    def test_schema_type_mismatch(self, test_db):
        """Test schema validation detects type mismatches."""
        expected = {
            "id": "VARCHAR",  # Wrong type (should be INTEGER)
            "email": "VARCHAR",
            "age": "INTEGER",
            "username": "VARCHAR",
        }

        validator = SchemaValidator(expected)
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert any("type" in issue.message.lower() for issue in result.issues)

    def test_schema_extra_columns(self, test_db):
        """Test schema validation detects extra columns."""
        expected = {
            "id": "INTEGER",
            "email": "VARCHAR",
        }

        validator = SchemaValidator(expected, allow_extra_columns=False)
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert result.issue_count >= 2  # age and username are extra

    def test_schema_allow_extra_columns(self, test_db):
        """Test schema validation allowing extra columns."""
        expected = {
            "id": "INTEGER",
            "email": "VARCHAR",
        }

        validator = SchemaValidator(expected, allow_extra_columns=True)
        result = validator.validate(test_db, "users")

        assert result.passed is True

    def test_schema_type_compatibility(self, test_db):
        """Test schema validator recognizes compatible types."""
        # INT should be compatible with INTEGER
        expected = {
            "id": "INT",
            "email": "VARCHAR",
            "age": "INT",
            "username": "VARCHAR",
        }

        validator = SchemaValidator(expected)
        result = validator.validate(test_db, "users")

        assert result.passed is True


class TestRangeValidator:
    """Test RangeValidator."""

    def test_range_passes(self, test_db):
        """Test range validation passes when all in range."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False  # Has -5 and 150
        assert result.issue_count == 1

    def test_range_min_only(self, test_db):
        """Test range validation with only minimum."""
        validator = RangeValidator(min_value=0)
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False  # Has -5
        assert result.issues[0].row_count == 1

    def test_range_max_only(self, test_db):
        """Test range validation with only maximum."""
        validator = RangeValidator(max_value=100)
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False  # Has 150
        assert result.issues[0].row_count == 1

    def test_range_sample_values(self, test_db):
        """Test range validation includes sample out-of-range values."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False
        assert len(result.issues[0].sample_values) > 0
        assert -5 in result.issues[0].sample_values or 150 in result.issues[0].sample_values

    def test_range_requires_column(self, test_db):
        """Test range validation requires column name."""
        validator = RangeValidator(min_value=0)
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert "requires a column" in result.issues[0].message

    def test_range_requires_min_or_max(self):
        """Test range validator requires at least min or max."""
        with pytest.raises(ValueError):
            RangeValidator()

    def test_range_fixable(self, test_db):
        """Test range validation marks issues as fixable."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False
        assert result.issues[0].fixable is True


class TestPatternValidator:
    """Test PatternValidator."""

    def test_pattern_email_validation(self, test_db):
        """Test pattern validation for email format."""
        email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        validator = PatternValidator(email_pattern)

        # All non-null emails should match (they're all valid)
        result = validator.validate(test_db, "users", "email")

        assert result.passed is True

    def test_pattern_sku_validation(self, test_db):
        """Test pattern validation for SKU format."""
        sku_pattern = r'^SKU-\d{3}$'
        validator = PatternValidator(sku_pattern)

        result = validator.validate(test_db, "products", "sku")

        assert result.passed is False  # 'INVALID' doesn't match
        assert result.issue_count == 1
        assert result.issues[0].row_count == 1

    def test_pattern_sample_values(self, test_db):
        """Test pattern validation includes sample non-matching values."""
        sku_pattern = r'^SKU-\d{3}$'
        validator = PatternValidator(sku_pattern)

        result = validator.validate(test_db, "products", "sku")

        assert result.passed is False
        assert "INVALID" in result.issues[0].sample_values

    def test_pattern_requires_column(self, test_db):
        """Test pattern validation requires column name."""
        validator = PatternValidator(r'^test$')
        result = validator.validate(test_db, "users")

        assert result.passed is False
        assert "requires a column" in result.issues[0].message

    def test_pattern_invalid_regex(self):
        """Test pattern validator rejects invalid regex."""
        with pytest.raises(ValueError):
            PatternValidator(r'[invalid(regex')

    def test_pattern_not_fixable(self, test_db):
        """Test pattern validation marks issues as not auto-fixable."""
        validator = PatternValidator(r'^SKU-\d{3}$')
        result = validator.validate(test_db, "products", "sku")

        assert result.passed is False
        assert result.issues[0].fixable is False


class TestCustomValidator:
    """Test CustomValidator."""

    def test_custom_validator_success(self, test_db):
        """Test custom validator with passing validation."""
        def check_age_reasonable(conn, table, column):
            # Check that all ages are between 0 and 120
            result = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} < 0 OR {column} > 120"
            ).fetchone()

            if result[0] == 0:
                return True, []
            else:
                from sbdk.quality.framework import QualityIssue, IssueSeverity
                issue = QualityIssue(
                    severity=IssueSeverity.ERROR,
                    message=f"Found {result[0]} unreasonable age values",
                    table=table,
                    column=column,
                    row_count=result[0],
                )
                return False, [issue]

        validator = CustomValidator(
            check_age_reasonable,
            name="ReasonableAgeCheck"
        )
        result = validator.validate(test_db, "users", "age")

        assert result.passed is False  # Has -5 and 150
        assert result.validator_name == "ReasonableAgeCheck"

    def test_custom_validator_with_issues(self, test_db):
        """Test custom validator returning issues."""
        def always_fail(conn, table, column):
            from sbdk.quality.framework import QualityIssue, IssueSeverity
            return False, [
                QualityIssue(
                    severity=IssueSeverity.WARNING,
                    message="Custom check failed",
                    table=table,
                    column=column,
                )
            ]

        validator = CustomValidator(always_fail, name="AlwaysFail")
        result = validator.validate(test_db, "users", "id")

        assert result.passed is False
        assert result.issue_count == 1
        assert result.issues[0].message == "Custom check failed"

    def test_custom_validator_exception_handling(self, test_db):
        """Test custom validator handles exceptions."""
        def raises_error(conn, table, column):
            raise ValueError("Intentional error")

        validator = CustomValidator(raises_error, name="ErrorValidator")
        result = validator.validate(test_db, "users", "id")

        assert result.passed is False
        assert result.issue_count == 1
        assert "failed" in result.issues[0].message.lower()


class TestBaseValidator:
    """Test BaseValidator abstract class."""

    def test_base_validator_cannot_instantiate(self):
        """Test that BaseValidator cannot be instantiated directly."""
        # BaseValidator is abstract and cannot be instantiated
        with pytest.raises(TypeError, match="abstract"):
            BaseValidator()

    def test_base_validator_create_result_helper(self):
        """Test BaseValidator._create_result helper method."""
        class TestValidator(BaseValidator):
            def validate(self, connection, table, column=None):
                return self._create_result(table, column, passed=True)

        validator = TestValidator()
        result = validator.validate(None, "test_table", "test_column")

        assert result.passed is True
        assert result.table == "test_table"
        assert result.column == "test_column"
        assert result.validator_name == "TestValidator"


class TestValidatorIntegration:
    """Integration tests for validators."""

    def test_multiple_validators_same_column(self, test_db):
        """Test running multiple validators on same column."""
        validators = [
            NotNullValidator(),
            UniqueValidator(),
        ]

        results = []
        for validator in validators:
            result = validator.validate(test_db, "users", "email")
            results.append(result)

        # email has null and duplicates
        assert not results[0].passed  # NotNull fails
        assert not results[1].passed  # Unique fails

    def test_validators_on_different_tables(self, test_db):
        """Test validators work across different tables."""
        user_validator = NotNullValidator()
        product_validator = NotNullValidator()

        user_result = user_validator.validate(test_db, "users", "email")
        product_result = product_validator.validate(test_db, "products", "name")

        assert not user_result.passed  # users.email has null
        assert not product_result.passed  # products.name has null

    def test_validator_with_empty_table(self):
        """Test validators handle empty tables gracefully."""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE empty_table (id INTEGER, name VARCHAR)")

        validator = NotNullValidator()
        result = validator.validate(conn, "empty_table", "name")

        assert result.passed is True  # No rows means no nulls
        conn.close()
