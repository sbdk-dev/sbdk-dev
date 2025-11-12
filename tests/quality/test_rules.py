"""
Comprehensive tests for SBDK Quality Rules Engine.
"""

import tempfile
from pathlib import Path

import duckdb
import pytest
import yaml

from sbdk.quality.framework import IssueSeverity, QualityFramework
from sbdk.quality.validators import (
    NotNullValidator,
    UniqueValidator,
    RangeValidator,
    PatternValidator,
    SchemaValidator,
)
from sbdk.quality.rules import (
    Rule,
    RuleSet,
    RuleEngine,
    RuleLoader,
    not_null,
    unique,
    range_check,
    pattern_match,
    schema_check,
)


class TestRule:
    """Test Rule data class."""

    def test_create_rule(self):
        """Test creating a rule."""
        validator = NotNullValidator()
        rule = Rule(
            table="users",
            column="email",
            validator=validator,
            description="Email must not be null",
        )

        assert rule.table == "users"
        assert rule.column == "email"
        assert rule.validator == validator
        assert rule.description == "Email must not be null"
        assert rule.enabled is True
        assert rule.tags == []

    def test_rule_with_tags(self):
        """Test creating a rule with tags."""
        rule = Rule(
            table="users",
            column="id",
            validator=UniqueValidator(),
            tags=["critical", "user_data"],
        )

        assert "critical" in rule.tags
        assert "user_data" in rule.tags

    def test_rule_disabled(self):
        """Test creating a disabled rule."""
        rule = Rule(
            table="users",
            column="email",
            validator=NotNullValidator(),
            enabled=False,
        )

        assert rule.enabled is False


class TestRuleSet:
    """Test RuleSet collection."""

    def test_create_empty_ruleset(self):
        """Test creating an empty rule set."""
        ruleset = RuleSet(name="test_rules")

        assert ruleset.name == "test_rules"
        assert len(ruleset) == 0

    def test_add_rule(self):
        """Test adding a rule to rule set."""
        ruleset = RuleSet()
        rule = Rule(
            table="users",
            column="email",
            validator=NotNullValidator(),
        )

        ruleset.add(rule)

        assert len(ruleset) == 1
        assert rule in ruleset.get_all()

    def test_extend_rules(self):
        """Test adding multiple rules at once."""
        ruleset = RuleSet()
        rules = [
            Rule(table="users", column="id", validator=UniqueValidator()),
            Rule(table="users", column="email", validator=NotNullValidator()),
        ]

        ruleset.extend(rules)

        assert len(ruleset) == 2

    def test_get_enabled_rules(self):
        """Test getting only enabled rules."""
        ruleset = RuleSet()
        ruleset.add(Rule(table="t1", column="c1", validator=NotNullValidator(), enabled=True))
        ruleset.add(Rule(table="t2", column="c2", validator=NotNullValidator(), enabled=False))
        ruleset.add(Rule(table="t3", column="c3", validator=NotNullValidator(), enabled=True))

        enabled = ruleset.get_enabled()

        assert len(enabled) == 2
        assert all(r.enabled for r in enabled)

    def test_get_by_table(self):
        """Test filtering rules by table."""
        ruleset = RuleSet()
        ruleset.add(Rule(table="users", column="id", validator=UniqueValidator()))
        ruleset.add(Rule(table="users", column="email", validator=NotNullValidator()))
        ruleset.add(Rule(table="products", column="id", validator=UniqueValidator()))

        users_rules = ruleset.get_by_table("users")

        assert len(users_rules) == 2
        assert all(r.table == "users" for r in users_rules)

    def test_get_by_tag(self):
        """Test filtering rules by tag."""
        ruleset = RuleSet()
        ruleset.add(Rule(
            table="users",
            column="id",
            validator=UniqueValidator(),
            tags=["critical"]
        ))
        ruleset.add(Rule(
            table="users",
            column="email",
            validator=NotNullValidator(),
            tags=["critical", "user_data"]
        ))
        ruleset.add(Rule(
            table="products",
            column="price",
            validator=RangeValidator(min_value=0),
            tags=["validation"]
        ))

        critical_rules = ruleset.get_by_tag("critical")

        assert len(critical_rules) == 2
        assert all("critical" in r.tags for r in critical_rules)

    def test_disable_enable_rule(self):
        """Test disabling and enabling rules by index."""
        ruleset = RuleSet()
        ruleset.add(Rule(table="users", column="id", validator=UniqueValidator()))

        ruleset.disable_rule(0)
        assert not ruleset.get_all()[0].enabled

        ruleset.enable_rule(0)
        assert ruleset.get_all()[0].enabled

    def test_iterate_ruleset(self):
        """Test iterating over rules in rule set."""
        ruleset = RuleSet()
        rules = [
            Rule(table="t1", column="c1", validator=NotNullValidator()),
            Rule(table="t2", column="c2", validator=UniqueValidator()),
        ]
        ruleset.extend(rules)

        count = 0
        for rule in ruleset:
            count += 1
            assert isinstance(rule, Rule)

        assert count == 2


class TestRuleEngine:
    """Test RuleEngine execution."""

    @pytest.fixture
    def test_db(self):
        """Create test database."""
        conn = duckdb.connect(":memory:")
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
            (3, NULL, 35)
        """)
        yield conn
        conn.close()

    def test_engine_init(self):
        """Test rule engine initialization."""
        engine = RuleEngine()
        assert engine.framework is not None

    def test_engine_with_framework(self):
        """Test rule engine with provided framework."""
        framework = QualityFramework()
        engine = RuleEngine(framework=framework)
        assert engine.framework == framework

    def test_engine_run_with_ruleset(self, test_db):
        """Test running validation with rule set."""
        framework = QualityFramework()
        framework._connection = test_db

        engine = RuleEngine(framework=framework)

        ruleset = RuleSet()
        ruleset.add(Rule(table="users", column="id", validator=NotNullValidator()))

        report = engine.run(ruleset)

        assert report.total_validations == 1
        assert report.passed is True

    def test_engine_run_with_rule_list(self, test_db):
        """Test running validation with list of rules."""
        framework = QualityFramework()
        framework._connection = test_db

        engine = RuleEngine(framework=framework)

        rules = [
            Rule(table="users", column="id", validator=NotNullValidator()),
            Rule(table="users", column="email", validator=NotNullValidator()),
        ]

        report = engine.run(rules)

        assert report.total_validations == 2
        assert not report.passed  # email has null

    def test_engine_respects_disabled_rules(self, test_db):
        """Test engine skips disabled rules."""
        framework = QualityFramework()
        framework._connection = test_db

        engine = RuleEngine(framework=framework)

        rules = [
            Rule(table="users", column="id", validator=NotNullValidator(), enabled=True),
            Rule(table="users", column="email", validator=NotNullValidator(), enabled=False),
        ]

        report = engine.run(rules)

        assert report.total_validations == 1  # Only enabled rule ran


class TestRuleLoader:
    """Test RuleLoader for loading rules from files."""

    def test_load_from_yaml(self):
        """Test loading rules from YAML file."""
        yaml_content = """
name: test_rules
rules:
  - table: users
    column: email
    validator: not_null
    severity: error
    description: Email must not be null
    enabled: true
    tags:
      - critical

  - table: users
    column: id
    validator: unique
    severity: error
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            ruleset = RuleLoader.from_yaml(yaml_path)

            assert ruleset.name == "test_rules"
            assert len(ruleset) == 2

            rules = ruleset.get_all()
            assert rules[0].table == "users"
            assert rules[0].column == "email"
            assert isinstance(rules[0].validator, NotNullValidator)
            assert rules[0].description == "Email must not be null"
            assert "critical" in rules[0].tags

        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_with_range_validator(self):
        """Test loading range validator from YAML."""
        yaml_content = """
rules:
  - table: products
    column: price
    validator: range
    min_value: 0
    max_value: 10000
    severity: error
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            ruleset = RuleLoader.from_yaml(yaml_path)

            assert len(ruleset) == 1
            rule = ruleset.get_all()[0]
            assert isinstance(rule.validator, RangeValidator)

        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_with_pattern_validator(self):
        """Test loading pattern validator from YAML."""
        yaml_content = """
rules:
  - table: users
    column: email
    validator: pattern
    pattern: '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$'
    severity: error
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            ruleset = RuleLoader.from_yaml(yaml_path)

            assert len(ruleset) == 1
            rule = ruleset.get_all()[0]
            assert isinstance(rule.validator, PatternValidator)

        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_with_schema_validator(self):
        """Test loading schema validator from YAML."""
        yaml_content = """
rules:
  - table: users
    validator: schema
    expected_columns:
      id: INTEGER
      email: VARCHAR
      age: INTEGER
    allow_extra_columns: false
    severity: error
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            ruleset = RuleLoader.from_yaml(yaml_path)

            assert len(ruleset) == 1
            rule = ruleset.get_all()[0]
            assert isinstance(rule.validator, SchemaValidator)

        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_file_not_found(self):
        """Test loading from non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            RuleLoader.from_yaml("nonexistent.yaml")

    def test_load_from_yaml_invalid_format(self):
        """Test loading from YAML with invalid format."""
        yaml_content = """
invalid_key: value
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            with pytest.raises(ValueError, match="must contain 'rules' key"):
                RuleLoader.from_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_load_from_dict(self):
        """Test loading rules from dictionary."""
        rules_dict = {
            "name": "dict_rules",
            "rules": [
                {
                    "table": "users",
                    "column": "email",
                    "validator": "not_null",
                    "severity": "error",
                },
                {
                    "table": "users",
                    "column": "id",
                    "validator": "unique",
                },
            ]
        }

        ruleset = RuleLoader.from_dict(rules_dict)

        assert ruleset.name == "dict_rules"
        assert len(ruleset) == 2

    def test_load_from_dict_invalid(self):
        """Test loading from dict without rules key."""
        with pytest.raises(ValueError, match="must contain 'rules' key"):
            RuleLoader.from_dict({"invalid": "data"})

    def test_load_from_python(self):
        """Test loading from Python rule objects."""
        rules = [
            Rule(table="users", column="id", validator=UniqueValidator()),
            Rule(table="users", column="email", validator=NotNullValidator()),
        ]

        ruleset = RuleLoader.from_python(rules)

        assert len(ruleset) == 2
        assert ruleset.get_all() == rules


class TestRuleHelperFunctions:
    """Test helper functions for building rules."""

    def test_not_null_helper(self):
        """Test not_null helper function."""
        rule = not_null("users", "email")

        assert rule.table == "users"
        assert rule.column == "email"
        assert isinstance(rule.validator, NotNullValidator)
        assert rule.description is not None

    def test_unique_helper(self):
        """Test unique helper function."""
        rule = unique("users", "id", severity=IssueSeverity.CRITICAL)

        assert rule.table == "users"
        assert rule.column == "id"
        assert isinstance(rule.validator, UniqueValidator)
        assert rule.validator.severity == IssueSeverity.CRITICAL

    def test_range_check_helper(self):
        """Test range_check helper function."""
        rule = range_check("products", "price", min_value=0, max_value=1000)

        assert rule.table == "products"
        assert rule.column == "price"
        assert isinstance(rule.validator, RangeValidator)

    def test_pattern_match_helper(self):
        """Test pattern_match helper function."""
        rule = pattern_match("users", "email", pattern=r'^.+@.+\..+$')

        assert rule.table == "users"
        assert rule.column == "email"
        assert isinstance(rule.validator, PatternValidator)

    def test_schema_check_helper(self):
        """Test schema_check helper function."""
        expected_cols = {"id": "INTEGER", "name": "VARCHAR"}
        rule = schema_check("users", expected_cols)

        assert rule.table == "users"
        assert isinstance(rule.validator, SchemaValidator)


class TestRulesIntegration:
    """Integration tests for rules engine."""

    def test_full_yaml_workflow(self):
        """Test complete workflow with YAML rules."""
        # Create test database
        conn = duckdb.connect(":memory:")
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
            (2, 'Product B', -5.00, 'SKU-002'),
            (3, NULL, 15.00, 'INVALID')
        """)

        # Create YAML rules
        yaml_content = """
name: product_validation
rules:
  - table: products
    column: id
    validator: unique
    severity: critical
    tags:
      - primary_key

  - table: products
    column: name
    validator: not_null
    severity: error
    tags:
      - required

  - table: products
    column: price
    validator: range
    min_value: 0
    severity: error
    description: Price must be non-negative

  - table: products
    column: sku
    validator: pattern
    pattern: '^SKU-\\d{3}$'
    severity: warning
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            # Load rules
            ruleset = RuleLoader.from_yaml(yaml_path)

            assert len(ruleset) == 4

            # Create framework and engine
            framework = QualityFramework()
            framework._connection = conn

            engine = RuleEngine(framework=framework)

            # Run validation
            report = engine.run(ruleset)

            # Verify results
            assert report.total_validations == 4
            assert not report.passed  # Should fail on name null, negative price, invalid SKU
            assert report.failed_validations >= 2

            # Save report
            with tempfile.TemporaryDirectory() as tmpdir:
                report_path = Path(tmpdir) / "report.json"
                report.save(report_path)
                assert report_path.exists()

        finally:
            Path(yaml_path).unlink()
            conn.close()

    def test_programmatic_rules_workflow(self):
        """Test workflow with programmatically defined rules."""
        # Create test database
        conn = duckdb.connect(":memory:")
        conn.execute("""
            CREATE TABLE orders (
                order_id INTEGER,
                customer_email VARCHAR,
                amount DOUBLE
            )
        """)
        conn.execute("""
            INSERT INTO orders VALUES
            (1, 'alice@example.com', 100.00),
            (2, 'bob@example.com', 200.00),
            (3, 'charlie@example.com', -50.00)
        """)

        # Define rules programmatically
        rules = [
            unique("orders", "order_id"),
            not_null("orders", "customer_email"),
            range_check("orders", "amount", min_value=0),
        ]

        # Create and run engine
        framework = QualityFramework()
        framework._connection = conn

        engine = RuleEngine(framework=framework)
        report = engine.run(rules)

        # Verify
        assert report.total_validations == 3
        assert not report.passed  # Negative amount

        conn.close()
