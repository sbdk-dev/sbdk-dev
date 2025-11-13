# SBDK Quality Framework

## Overview

The SBDK Quality Framework provides comprehensive data quality validation for your data pipelines. It enables you to define quality rules, run validations, generate detailed reports, and automatically fix common issues.

## Features

- **Built-in Validators**: Null checks, uniqueness, schema validation, range checks, pattern matching
- **Custom Validators**: Define your own validation logic
- **Rule-Based Engine**: Define rules in YAML, Python, or programmatically
- **Detailed Reports**: Rich console output and JSON reports
- **Auto-Fix**: Automatically fix common quality issues
- **DuckDB Integration**: Native support for DuckDB databases
- **dbt Compatible**: Works seamlessly with dbt models

## Quick Start

### Basic Usage

```python
from sbdk.quality import QualityFramework, Rule, NotNullValidator

# Create framework instance
framework = QualityFramework(db_path="data.duckdb")

# Define a validation rule
rule = Rule(
    table="users",
    column="email",
    validator=NotNullValidator()
)

# Run validation
report = framework.validate_rules([rule])

# Display results
framework.display_report(report)

# Check if passed
if not report.passed:
    print(f"Found {report.total_issues} quality issues")
```

### Using YAML Rules

Create a `quality_rules.yaml` file:

```yaml
name: user_validation
rules:
  - table: users
    column: email
    validator: not_null
    severity: error
    description: Email must not be null
    tags:
      - critical
      - user_data

  - table: users
    column: id
    validator: unique
    severity: critical
    description: User ID must be unique

  - table: users
    column: age
    validator: range
    min_value: 0
    max_value: 150
    severity: error
    description: Age must be realistic
```

Load and run:

```python
from sbdk.quality import QualityFramework, RuleLoader, RuleEngine

# Load rules from YAML
rules = RuleLoader.from_yaml("quality_rules.yaml")

# Create framework and engine
framework = QualityFramework(db_path="data.duckdb")
engine = RuleEngine(framework=framework)

# Run validation
report = engine.run(rules)

# Display and save report
framework.display_report(report, verbose=True)
report.save("quality_report.json")
```

## Built-in Validators

### 1. NotNullValidator

Validates that a column contains no NULL values.

```python
from sbdk.quality import NotNullValidator

validator = NotNullValidator(
    severity=IssueSeverity.ERROR,
    allow_empty_string=False  # Treat empty strings as NULL
)
```

**YAML:**
```yaml
- table: users
  column: email
  validator: not_null
  severity: error
```

### 2. UniqueValidator

Validates that a column contains only unique values (no duplicates).

```python
from sbdk.quality import UniqueValidator

validator = UniqueValidator(
    severity=IssueSeverity.ERROR
)
```

**YAML:**
```yaml
- table: users
  column: id
  validator: unique
  severity: critical
```

### 3. RangeValidator

Validates that numeric column values fall within expected range.

```python
from sbdk.quality import RangeValidator

validator = RangeValidator(
    min_value=0,
    max_value=100,
    severity=IssueSeverity.ERROR
)
```

**YAML:**
```yaml
- table: products
  column: price
  validator: range
  min_value: 0
  max_value: 10000
  severity: error
```

### 4. PatternValidator

Validates that string column values match expected regex pattern.

```python
from sbdk.quality import PatternValidator

# Email validation
validator = PatternValidator(
    pattern=r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',
    severity=IssueSeverity.ERROR
)
```

**YAML:**
```yaml
- table: users
  column: email
  validator: pattern
  pattern: '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
  severity: error
```

### 5. SchemaValidator

Validates that table schema matches expected definition.

```python
from sbdk.quality import SchemaValidator

validator = SchemaValidator(
    expected_columns={
        "id": "INTEGER",
        "email": "VARCHAR",
        "age": "INTEGER",
    },
    allow_extra_columns=False,
    severity=IssueSeverity.ERROR
)
```

**YAML:**
```yaml
- table: users
  validator: schema
  expected_columns:
    id: INTEGER
    email: VARCHAR
    age: INTEGER
  allow_extra_columns: false
  severity: error
```

### 6. CustomValidator

Define your own validation logic.

```python
from sbdk.quality import CustomValidator, QualityIssue, IssueSeverity

def check_email_domain(conn, table, column):
    """Validate email domains are from allowed list."""
    result = conn.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE {column} NOT LIKE '%@company.com'
          AND {column} IS NOT NULL
    """).fetchone()

    if result[0] == 0:
        return True, []

    issue = QualityIssue(
        severity=IssueSeverity.WARNING,
        message=f"Found {result[0]} emails with non-company domains",
        table=table,
        column=column,
        row_count=result[0],
    )
    return False, [issue]

validator = CustomValidator(
    validation_func=check_email_domain,
    name="EmailDomainCheck"
)
```

## Rule Definition

### Programmatic Rules

Use helper functions for concise rule definition:

```python
from sbdk.quality.rules import (
    not_null,
    unique,
    range_check,
    pattern_match,
    schema_check,
)

rules = [
    # Not null checks
    not_null("users", "email"),
    not_null("users", "username"),

    # Uniqueness checks
    unique("users", "id"),
    unique("users", "email"),

    # Range validation
    range_check("products", "price", min_value=0, max_value=100000),
    range_check("users", "age", min_value=0, max_value=150),

    # Pattern matching
    pattern_match("users", "email", pattern=r'^.+@.+\..+$'),
    pattern_match("products", "sku", pattern=r'^SKU-\d{6}$'),

    # Schema validation
    schema_check("users", {
        "id": "INTEGER",
        "email": "VARCHAR",
        "age": "INTEGER",
    }),
]
```

### YAML Rules

Complete YAML example:

```yaml
name: complete_validation
rules:
  # Critical checks
  - table: users
    column: id
    validator: unique
    severity: critical
    description: User ID must be unique
    tags:
      - critical
      - primary_key
    enabled: true

  - table: users
    column: email
    validator: not_null
    severity: error
    description: Email is required
    tags:
      - critical
      - required_field

  # Business rule checks
  - table: orders
    column: amount
    validator: range
    min_value: 0
    max_value: 1000000
    severity: error
    description: Order amount must be reasonable
    tags:
      - business_rule

  - table: users
    column: email
    validator: pattern
    pattern: '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    severity: warning
    description: Email must be valid format
    tags:
      - format_check

  # Schema validation
  - table: users
    validator: schema
    expected_columns:
      id: INTEGER
      email: VARCHAR
      username: VARCHAR
      age: INTEGER
      created_at: TIMESTAMP
    allow_extra_columns: true
    severity: error
    description: User table schema validation
    tags:
      - schema
```

## Quality Reports

### Console Output

The framework provides beautiful Rich console output:

```python
framework.display_report(report, verbose=True)
```

Output includes:
- Overall pass/fail status
- Summary statistics (total validations, failed validations, issues by severity)
- Detailed issue breakdown with affected rows and sample values
- Fix suggestions for each issue
- Execution time

### JSON Reports

Save reports for later analysis or integration:

```python
# Save to file
report.save("quality_reports/report_2024-01-15.json")

# Or get JSON string
json_str = report.to_json()

# Or get dictionary
report_dict = report.to_dict()
```

Report structure:

```json
{
  "passed": false,
  "timestamp": "2024-01-15T10:30:00",
  "database_path": "data.duckdb",
  "total_validations": 5,
  "failed_validations": 2,
  "total_issues": 3,
  "critical_issues": 0,
  "error_issues": 2,
  "warning_issues": 1,
  "execution_time_ms": 125.5,
  "results": [
    {
      "passed": false,
      "validator_name": "NotNullValidator",
      "table": "users",
      "column": "email",
      "issue_count": 1,
      "critical_count": 0,
      "error_count": 1,
      "warning_count": 0,
      "issues": [
        {
          "severity": "error",
          "message": "Found 5 NULL values in column 'email'",
          "table": "users",
          "column": "email",
          "row_count": 5,
          "sample_values": [null, null, null, null, null],
          "fixable": true,
          "fix_suggestion": "DELETE FROM users WHERE email IS NULL"
        }
      ],
      "execution_time_ms": 25.3
    }
  ]
}
```

## Auto-Fix

The framework can automatically fix common quality issues:

```python
# Run validation with auto-fix enabled
report = framework.validate_rules(rules, auto_fix=True)

# Or run auto-fix separately
report = framework.validate_rules(rules)
if not report.passed:
    framework.auto_fix(report)

# Preview fixes without applying (dry-run)
framework.auto_fix(report, dry_run=True)
```

**Fixable Issues:**
- NULL values (can be deleted or replaced with defaults)
- Duplicate values (can keep first occurrence)
- Out-of-range values (can be deleted or clamped)
- Missing schema columns (can be added)

**Note:** Auto-fix is conservative and only fixes issues when safe to do so. Always review changes before applying to production data.

## Integration with dbt

### Validate dbt Models

```python
from sbdk.quality import QualityFramework, RuleLoader

# After running dbt
# sbdk run --dbt-only

# Validate dbt models
framework = QualityFramework(db_path="data.duckdb")
rules = RuleLoader.from_yaml("dbt/quality_rules.yaml")

report = framework.validate_rules(rules.get_enabled())

if not report.passed:
    framework.display_report(report)
    exit(1)  # Fail CI/CD pipeline
```

### dbt Tests + Quality Framework

Combine dbt's built-in tests with SBDK quality framework:

```yaml
# dbt/models/schema.yml
version: 2

models:
  - name: users
    columns:
      - name: id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - not_null
```

```yaml
# quality_rules.yaml
rules:
  - table: users
    column: age
    validator: range
    min_value: 0
    max_value: 150

  - table: users
    column: email
    validator: pattern
    pattern: '^.+@.+\..+$'
```

Run both:

```bash
# Run dbt tests
dbt test

# Run SBDK quality checks
sbdk run --quality-check
```

## CLI Integration

Add quality checks to your SBDK pipeline:

```bash
# Run with quality checks
sbdk run --quality-check

# Use custom rules file
sbdk run --quality-check --quality-rules custom_rules.yaml

# Auto-fix issues
sbdk run --quality-check --auto-fix

# Generate report only
sbdk quality check --rules quality_rules.yaml --report quality_report.json
```

## Advanced Usage

### Rule Sets and Tagging

Organize rules with tags and rule sets:

```python
from sbdk.quality.rules import RuleSet

# Load rules
all_rules = RuleLoader.from_yaml("quality_rules.yaml")

# Filter by tag
critical_rules = all_rules.get_by_tag("critical")
business_rules = all_rules.get_by_tag("business_rule")

# Filter by table
user_rules = all_rules.get_by_table("users")

# Disable specific rules
all_rules.disable_rule(3)

# Run different rule sets
report_critical = engine.run(critical_rules)
report_business = engine.run(business_rules)
```

### Context Manager Usage

```python
with QualityFramework(db_path="data.duckdb") as framework:
    rules = RuleLoader.from_yaml("rules.yaml")
    report = framework.validate_rules(rules)
    framework.display_report(report)
# Connection automatically closed
```

### Programmatic Report Analysis

```python
report = framework.validate_rules(rules)

# Analyze results
print(f"Total validations: {report.total_validations}")
print(f"Failed: {report.failed_validations}")
print(f"Critical issues: {report.critical_issues}")
print(f"Error issues: {report.error_issues}")
print(f"Warning issues: {report.warning_issues}")

# Find specific failures
for result in report.results:
    if not result.passed:
        print(f"Failed: {result.table}.{result.column}")
        for issue in result.issues:
            print(f"  - {issue.message}")
            if issue.fixable:
                print(f"    Fix: {issue.fix_suggestion}")

# Export for analysis
import pandas as pd

issues_data = []
for result in report.results:
    for issue in result.issues:
        issues_data.append({
            "table": issue.table,
            "column": issue.column,
            "severity": issue.severity.value,
            "message": issue.message,
            "row_count": issue.row_count,
        })

df = pd.DataFrame(issues_data)
df.to_csv("quality_issues.csv", index=False)
```

## Best Practices

### 1. Start with Critical Checks

Begin with critical validations (primary keys, required fields):

```yaml
rules:
  - table: users
    column: id
    validator: unique
    severity: critical
    tags: [critical, primary_key]
```

### 2. Use Appropriate Severity Levels

- **CRITICAL**: Data corruption, blocking issues (duplicates in primary keys)
- **ERROR**: Data quality violations (null in required fields, out-of-range values)
- **WARNING**: Potential issues (format inconsistencies, suspicious patterns)
- **INFO**: Informational findings (data distribution, statistics)

### 3. Organize Rules by Domain

```yaml
name: user_domain_validation
rules:
  # Identity checks
  - table: users
    column: id
    validator: unique
    tags: [identity]

  # Contact info checks
  - table: users
    column: email
    validator: pattern
    pattern: '^.+@.+\..+$'
    tags: [contact_info]

  # Business rules
  - table: users
    column: age
    validator: range
    min_value: 18
    tags: [business_rule]
```

### 4. Version Your Rules

Keep rules in version control alongside your dbt models:

```
project/
├── dbt/
│   ├── models/
│   └── schema.yml
├── quality/
│   ├── rules_v1.yaml
│   ├── rules_v2.yaml
│   └── custom_validators.py
└── sbdk_config.json
```

### 5. Run Quality Checks in CI/CD

```yaml
# .github/workflows/quality.yml
- name: Run Quality Checks
  run: |
    sbdk run --quality-check

    if [ $? -ne 0 ]; then
      echo "Quality checks failed!"
      exit 1
    fi
```

### 6. Monitor Quality Over Time

Track quality metrics:

```python
import json
from datetime import datetime

# Run daily quality checks
report = framework.validate_rules(rules)

# Save with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report.save(f"quality_reports/report_{timestamp}.json")

# Track trends
quality_metrics = {
    "date": timestamp,
    "total_issues": report.total_issues,
    "critical": report.critical_issues,
    "errors": report.error_issues,
    "warnings": report.warning_issues,
}

with open("quality_metrics.jsonl", "a") as f:
    f.write(json.dumps(quality_metrics) + "\n")
```

## Troubleshooting

### Issue: Validator fails with "table not found"

**Solution:** Ensure the table exists in the database and the connection is established:

```python
framework = QualityFramework(db_path="data.duckdb")

# Check table exists
tables = framework.connection.execute("SHOW TABLES").fetchall()
print("Available tables:", tables)
```

### Issue: Pattern validator fails on valid values

**Solution:** Check regex escaping in YAML. Use single quotes and double backslashes:

```yaml
# Correct
pattern: '^SKU-\\d{3}$'

# Incorrect
pattern: "^SKU-\d{3}$"  # Backslash gets interpreted
```

### Issue: Auto-fix doesn't fix issues

**Solution:** Not all issues are auto-fixable. Check if the issue is marked as fixable:

```python
for result in report.results:
    for issue in result.issues:
        if not issue.fixable:
            print(f"Cannot auto-fix: {issue.message}")
            print(f"Suggestion: {issue.fix_suggestion}")
```

### Issue: Performance slow on large tables

**Solution:** Add indexes on columns being validated:

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_products_sku ON products(sku);
```

## API Reference

See individual class documentation:

- [QualityFramework](../sbdk/quality/framework.py)
- [Validators](../sbdk/quality/validators.py)
- [Rules Engine](../sbdk/quality/rules.py)

## Examples

See [examples/quality/](../../examples/quality/) for complete working examples:

- `basic_validation.py` - Simple validation workflow
- `yaml_rules.py` - Using YAML rules
- `custom_validators.py` - Creating custom validators
- `dbt_integration.py` - Integrating with dbt
- `ci_pipeline.py` - CI/CD integration example

## Contributing

To add new validators:

1. Inherit from `BaseValidator`
2. Implement `validate()` method
3. Return `ValidationResult` with issues
4. Add tests in `tests/quality/`
5. Update documentation

Example:

```python
class MyCustomValidator(BaseValidator):
    def validate(self, connection, table, column=None):
        # Your validation logic
        issues = []

        # Check something...
        if problem_found:
            issues.append(QualityIssue(
                severity=self.severity,
                message="Problem description",
                table=table,
                column=column,
            ))

        return self._create_result(
            table,
            column,
            passed=len(issues) == 0,
            issues=issues,
        )
```

## License

Part of SBDK - see main project license.
