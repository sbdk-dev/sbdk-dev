"""
SBDK Quality Rules Engine

Define and load quality validation rules from YAML or Python.
Provides a declarative way to specify data quality requirements.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

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


@dataclass
class Rule:
    """
    A single data quality validation rule.

    Attributes:
        table: Table name to validate
        column: Column name (optional, for column-level validators)
        validator: Validator instance to use
        description: Human-readable rule description
        enabled: Whether rule is enabled
        tags: Tags for rule organization
    """
    table: str
    validator: BaseValidator
    column: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    tags: List[str] = None

    def __post_init__(self):
        """Initialize tags if not provided."""
        if self.tags is None:
            self.tags = []


class RuleSet:
    """
    Collection of validation rules.

    Provides methods to add, filter, and organize rules.

    Example:
        >>> ruleset = RuleSet(name="user_validation")
        >>> ruleset.add(Rule("users", "email", NotNullValidator()))
        >>> ruleset.add(Rule("users", "id", UniqueValidator()))
        >>> active_rules = ruleset.get_enabled()
    """

    def __init__(self, name: str = "default", rules: Optional[List[Rule]] = None):
        """
        Initialize rule set.

        Args:
            name: Name for this rule set
            rules: Initial list of rules
        """
        self.name = name
        self._rules: List[Rule] = rules or []

    def add(self, rule: Rule) -> None:
        """
        Add a rule to the set.

        Args:
            rule: Rule to add
        """
        self._rules.append(rule)

    def extend(self, rules: List[Rule]) -> None:
        """
        Add multiple rules to the set.

        Args:
            rules: List of rules to add
        """
        self._rules.extend(rules)

    def get_all(self) -> List[Rule]:
        """
        Get all rules.

        Returns:
            List of all rules
        """
        return self._rules.copy()

    def get_enabled(self) -> List[Rule]:
        """
        Get only enabled rules.

        Returns:
            List of enabled rules
        """
        return [r for r in self._rules if r.enabled]

    def get_by_table(self, table: str) -> List[Rule]:
        """
        Get rules for a specific table.

        Args:
            table: Table name

        Returns:
            List of rules for the table
        """
        return [r for r in self._rules if r.table == table]

    def get_by_tag(self, tag: str) -> List[Rule]:
        """
        Get rules with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of rules with the tag
        """
        return [r for r in self._rules if tag in r.tags]

    def disable_rule(self, index: int) -> None:
        """
        Disable a rule by index.

        Args:
            index: Rule index
        """
        if 0 <= index < len(self._rules):
            self._rules[index].enabled = False

    def enable_rule(self, index: int) -> None:
        """
        Enable a rule by index.

        Args:
            index: Rule index
        """
        if 0 <= index < len(self._rules):
            self._rules[index].enabled = True

    def __len__(self) -> int:
        """Get number of rules."""
        return len(self._rules)

    def __iter__(self):
        """Iterate over rules."""
        return iter(self._rules)


class RuleEngine:
    """
    Engine for executing quality rules.

    Provides high-level interface for rule-based validation.

    Example:
        >>> from sbdk.quality import QualityFramework
        >>> engine = RuleEngine(framework=QualityFramework())
        >>> rules = RuleLoader.from_yaml("quality_rules.yaml")
        >>> report = engine.run(rules)
    """

    def __init__(self, framework: Any = None):
        """
        Initialize rule engine.

        Args:
            framework: QualityFramework instance (created if not provided)
        """
        if framework is None:
            from sbdk.quality.framework import QualityFramework
            framework = QualityFramework()

        self.framework = framework

    def run(
        self,
        rules: Union[RuleSet, List[Rule]],
        auto_fix: bool = False,
    ) -> Any:
        """
        Run quality validation with rules.

        Args:
            rules: RuleSet or list of rules
            auto_fix: Automatically fix issues

        Returns:
            QualityReport with validation results
        """
        if isinstance(rules, RuleSet):
            rule_list = rules.get_enabled()
        else:
            rule_list = [r for r in rules if r.enabled]

        return self.framework.validate_rules(rule_list, auto_fix=auto_fix)


class RuleLoader:
    """
    Load validation rules from various formats.

    Supports:
    - YAML files
    - Python dictionaries
    - Programmatic rule building
    """

    @staticmethod
    def from_yaml(path: Union[str, Path]) -> RuleSet:
        """
        Load rules from YAML file.

        YAML format:
            rules:
              - table: users
                column: email
                validator: not_null
                severity: error
                description: Email must not be null
                enabled: true
                tags:
                  - critical
                  - user_data

              - table: users
                column: id
                validator: unique
                severity: error

              - table: products
                column: price
                validator: range
                min_value: 0
                max_value: 100000
                severity: error

        Args:
            path: Path to YAML file

        Returns:
            RuleSet with loaded rules
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or "rules" not in data:
            raise ValueError("Invalid rules YAML: must contain 'rules' key")

        rules = []
        for rule_data in data["rules"]:
            rule = RuleLoader._parse_rule_dict(rule_data)
            if rule:
                rules.append(rule)

        ruleset_name = data.get("name", path.stem)
        return RuleSet(name=ruleset_name, rules=rules)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> RuleSet:
        """
        Load rules from dictionary.

        Args:
            data: Dictionary with 'rules' key containing list of rule dicts

        Returns:
            RuleSet with loaded rules
        """
        if "rules" not in data:
            raise ValueError("Invalid rules dict: must contain 'rules' key")

        rules = []
        for rule_data in data["rules"]:
            rule = RuleLoader._parse_rule_dict(rule_data)
            if rule:
                rules.append(rule)

        ruleset_name = data.get("name", "default")
        return RuleSet(name=ruleset_name, rules=rules)

    @staticmethod
    def from_python(rules: List[Rule]) -> RuleSet:
        """
        Create rule set from Python rule objects.

        Args:
            rules: List of Rule instances

        Returns:
            RuleSet containing the rules
        """
        return RuleSet(name="python", rules=rules)

    @staticmethod
    def _parse_rule_dict(rule_data: Dict[str, Any]) -> Optional[Rule]:
        """
        Parse a single rule from dictionary.

        Args:
            rule_data: Rule dictionary

        Returns:
            Rule instance or None if invalid
        """
        # Required fields
        table = rule_data.get("table")
        validator_type = rule_data.get("validator")

        if not table or not validator_type:
            return None

        # Optional fields
        column = rule_data.get("column")
        description = rule_data.get("description")
        enabled = rule_data.get("enabled", True)
        tags = rule_data.get("tags", [])

        # Parse severity
        severity_str = rule_data.get("severity", "error").lower()
        severity_map = {
            "critical": IssueSeverity.CRITICAL,
            "error": IssueSeverity.ERROR,
            "warning": IssueSeverity.WARNING,
            "info": IssueSeverity.INFO,
        }
        severity = severity_map.get(severity_str, IssueSeverity.ERROR)

        # Create validator based on type
        validator = RuleLoader._create_validator(
            validator_type,
            rule_data,
            severity,
        )

        if not validator:
            return None

        return Rule(
            table=table,
            column=column,
            validator=validator,
            description=description,
            enabled=enabled,
            tags=tags,
        )

    @staticmethod
    def _create_validator(
        validator_type: str,
        rule_data: Dict[str, Any],
        severity: IssueSeverity,
    ) -> Optional[BaseValidator]:
        """
        Create validator instance from type and config.

        Args:
            validator_type: Validator type name
            rule_data: Rule configuration
            severity: Issue severity

        Returns:
            Validator instance or None if invalid type
        """
        validator_type = validator_type.lower()

        if validator_type == "not_null":
            return NotNullValidator(
                severity=severity,
                allow_empty_string=rule_data.get("allow_empty_string", False),
            )

        elif validator_type == "unique":
            return UniqueValidator(severity=severity)

        elif validator_type == "schema":
            expected_columns = rule_data.get("expected_columns", {})
            allow_extra = rule_data.get("allow_extra_columns", False)
            return SchemaValidator(
                expected_columns=expected_columns,
                severity=severity,
                allow_extra_columns=allow_extra,
            )

        elif validator_type == "range":
            min_value = rule_data.get("min_value")
            max_value = rule_data.get("max_value")

            if min_value is None and max_value is None:
                return None

            return RangeValidator(
                min_value=min_value,
                max_value=max_value,
                severity=severity,
            )

        elif validator_type == "pattern":
            pattern = rule_data.get("pattern")
            if not pattern:
                return None

            return PatternValidator(
                pattern=pattern,
                severity=severity,
            )

        else:
            # Unknown validator type
            return None


# Helper functions for building rules programmatically

def not_null(
    table: str,
    column: str,
    severity: IssueSeverity = IssueSeverity.ERROR,
    description: Optional[str] = None,
) -> Rule:
    """
    Create a not-null validation rule.

    Args:
        table: Table name
        column: Column name
        severity: Issue severity
        description: Rule description

    Returns:
        Rule instance
    """
    return Rule(
        table=table,
        column=column,
        validator=NotNullValidator(severity=severity),
        description=description or f"{column} must not be null",
    )


def unique(
    table: str,
    column: str,
    severity: IssueSeverity = IssueSeverity.ERROR,
    description: Optional[str] = None,
) -> Rule:
    """
    Create a uniqueness validation rule.

    Args:
        table: Table name
        column: Column name
        severity: Issue severity
        description: Rule description

    Returns:
        Rule instance
    """
    return Rule(
        table=table,
        column=column,
        validator=UniqueValidator(severity=severity),
        description=description or f"{column} must be unique",
    )


def range_check(
    table: str,
    column: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    severity: IssueSeverity = IssueSeverity.ERROR,
    description: Optional[str] = None,
) -> Rule:
    """
    Create a range validation rule.

    Args:
        table: Table name
        column: Column name
        min_value: Minimum value
        max_value: Maximum value
        severity: Issue severity
        description: Rule description

    Returns:
        Rule instance
    """
    return Rule(
        table=table,
        column=column,
        validator=RangeValidator(
            min_value=min_value,
            max_value=max_value,
            severity=severity,
        ),
        description=description or f"{column} must be in range [{min_value}, {max_value}]",
    )


def pattern_match(
    table: str,
    column: str,
    pattern: str,
    severity: IssueSeverity = IssueSeverity.ERROR,
    description: Optional[str] = None,
) -> Rule:
    """
    Create a pattern matching validation rule.

    Args:
        table: Table name
        column: Column name
        pattern: Regex pattern
        severity: Issue severity
        description: Rule description

    Returns:
        Rule instance
    """
    return Rule(
        table=table,
        column=column,
        validator=PatternValidator(pattern=pattern, severity=severity),
        description=description or f"{column} must match pattern {pattern}",
    )


def schema_check(
    table: str,
    expected_columns: Dict[str, str],
    allow_extra_columns: bool = False,
    severity: IssueSeverity = IssueSeverity.ERROR,
    description: Optional[str] = None,
) -> Rule:
    """
    Create a schema validation rule.

    Args:
        table: Table name
        expected_columns: Dict of column_name -> type
        allow_extra_columns: Allow additional columns
        severity: Issue severity
        description: Rule description

    Returns:
        Rule instance
    """
    return Rule(
        table=table,
        validator=SchemaValidator(
            expected_columns=expected_columns,
            severity=severity,
            allow_extra_columns=allow_extra_columns,
        ),
        description=description or f"{table} schema validation",
    )
