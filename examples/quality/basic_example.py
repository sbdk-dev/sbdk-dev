"""
Basic example of using SBDK Quality Framework.

This example demonstrates:
1. Creating a simple database
2. Defining quality validation rules
3. Running validations
4. Displaying and saving reports
"""

import duckdb
from sbdk.quality import QualityFramework
from sbdk.quality.rules import not_null, unique, range_check, pattern_match


def main():
    # Create an in-memory database with sample data
    print("Creating sample database...")
    conn = duckdb.connect(":memory:")

    # Create users table
    conn.execute("""
        CREATE TABLE users (
            id INTEGER,
            email VARCHAR,
            username VARCHAR,
            age INTEGER
        )
    """)

    # Insert sample data (with some quality issues)
    conn.execute("""
        INSERT INTO users VALUES
        (1, 'alice@example.com', 'alice', 25),
        (2, 'bob@example.com', 'bob', 30),
        (3, NULL, 'charlie', 35),              -- Missing email
        (4, 'david@example.com', 'david', -5),  -- Invalid age
        (5, 'eve@example.com', 'eve', 150),     -- Invalid age
        (6, 'alice@example.com', 'alice', 28)   -- Duplicate email and username
    """)

    print("Sample data inserted.\n")

    # Create quality framework
    framework = QualityFramework()
    framework._connection = conn

    # Define validation rules
    print("Defining validation rules...")
    rules = [
        unique("users", "id", description="User IDs must be unique"),
        unique("users", "email", description="Email addresses must be unique"),
        unique("users", "username", description="Usernames must be unique"),
        not_null("users", "email", description="Email is required"),
        range_check("users", "age", min_value=0, max_value=120,
                    description="Age must be between 0 and 120"),
        pattern_match("users", "email", pattern=r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',
                      description="Email must be valid format"),
    ]

    print(f"Defined {len(rules)} validation rules.\n")

    # Run validation
    print("Running quality validation...")
    report = framework.validate_rules(rules)
    print()

    # Display report
    framework.display_report(report, verbose=True)
    print()

    # Analyze results
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Total validations: {report.total_validations}")
    print(f"Passed validations: {report.total_validations - report.failed_validations}")
    print(f"Failed validations: {report.failed_validations}")
    print(f"Total issues found: {report.total_issues}")
    print(f"  - Critical: {report.critical_issues}")
    print(f"  - Errors: {report.error_issues}")
    print(f"  - Warnings: {report.warning_issues}")
    print(f"Execution time: {report.execution_time_ms:.2f}ms")
    print()

    # Show fixable issues
    fixable_count = sum(
        len([i for i in r.issues if i.fixable])
        for r in report.results
        if not r.passed
    )

    if fixable_count > 0:
        print(f"Found {fixable_count} auto-fixable issues.")
        print("Run with auto_fix=True to fix automatically:")
        print("  report = framework.validate_rules(rules, auto_fix=True)")
        print()

    # Save report
    print("Saving report to quality_report.json...")
    report.save("quality_report.json")
    print("Report saved!")
    print()

    # Show how to access results programmatically
    print("Issues by table:")
    for result in report.results:
        if not result.passed:
            print(f"  {result.table}.{result.column}: {result.issue_count} issue(s)")
            for issue in result.issues:
                print(f"    - {issue.message}")

    conn.close()


if __name__ == "__main__":
    main()
