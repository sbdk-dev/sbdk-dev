"""
SBDK Quality Framework

A comprehensive data quality validation framework for SBDK pipelines.

Features:
- Built-in validators (nulls, uniqueness, schema, ranges)
- Custom validator support
- Rule-based validation engine
- Detailed quality reports
- Auto-fix capabilities
- DuckDB and dbt integration

Example:
    >>> from sbdk.quality import QualityFramework, Rule, NotNullValidator
    >>> framework = QualityFramework()
    >>> rule = Rule("users", "email", NotNullValidator())
    >>> report = framework.validate(rule)
    >>> print(report.passed)
    True
"""

from sbdk.quality.framework import (
    QualityFramework,
    QualityReport,
    ValidationResult,
    QualityIssue,
    IssueSeverity,
)
from sbdk.quality.validators import (
    BaseValidator,
    NotNullValidator,
    UniqueValidator,
    SchemaValidator,
    RangeValidator,
    PatternValidator,
    CustomValidator,
)
from sbdk.quality.rules import (
    Rule,
    RuleEngine,
    RuleSet,
    RuleLoader,
)

__all__ = [
    # Framework
    "QualityFramework",
    "QualityReport",
    "ValidationResult",
    "QualityIssue",
    "IssueSeverity",
    # Validators
    "BaseValidator",
    "NotNullValidator",
    "UniqueValidator",
    "SchemaValidator",
    "RangeValidator",
    "PatternValidator",
    "CustomValidator",
    # Rules
    "Rule",
    "RuleEngine",
    "RuleSet",
    "RuleLoader",
]
