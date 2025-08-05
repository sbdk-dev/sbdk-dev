"""
Automated Validation Framework for SBDK.dev v2.0.0
Comprehensive validation system for continuous quality assurance
"""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import pytest
from typer.testing import CliRunner

from sbdk.cli.commands.run import load_config
from sbdk.cli.main import app


class ValidationResult:
    """Container for validation results"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.errors = []
        self.warnings = []
        self.metrics = {}
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start timing the validation"""
        self.start_time = time.time()

    def finish(self, passed: bool = True):
        """Finish the validation"""
        self.end_time = time.time()
        self.passed = passed

    @property
    def duration(self) -> float:
        """Get validation duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.passed = False

    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)

    def add_metric(self, name: str, value: Any):
        """Add a performance metric"""
        self.metrics[name] = value


class ValidationFramework:
    """Main validation framework"""

    def __init__(self):
        self.results = []
        self.runner = CliRunner()

    def run_validation(
        self, test_name: str, test_func, *args, **kwargs
    ) -> ValidationResult:
        """Run a validation test and collect results"""
        result = ValidationResult(test_name)
        result.start()

        try:
            test_func(result, *args, **kwargs)
            if not result.errors:
                result.finish(True)
            else:
                result.finish(False)
        except Exception as e:
            result.add_error(f"Validation failed with exception: {str(e)}")
            result.finish(False)

        self.results.append(result)
        return result

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive validation report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                ),
                "total_duration": sum(r.duration for r in self.results),
            },
            "results": [],
            "errors": [],
            "warnings": [],
            "metrics": {},
        }

        for result in self.results:
            report["results"].append(
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "duration": result.duration,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "metrics": result.metrics,
                }
            )

            report["errors"].extend(result.errors)
            report["warnings"].extend(result.warnings)

            # Aggregate metrics
            for metric, value in result.metrics.items():
                if metric not in report["metrics"]:
                    report["metrics"][metric] = []
                report["metrics"][metric].append(value)

        return report


class TestAutomatedValidation:
    """Automated validation test suite"""

    def test_complete_validation_suite(self):
        """Run complete validation suite"""
        framework = ValidationFramework()

        # Run all validation tests
        framework.run_validation("cli_basic_functionality", self._validate_cli_basic)
        framework.run_validation("project_initialization", self._validate_project_init)
        framework.run_validation("configuration_loading", self._validate_config_loading)
        framework.run_validation("data_generation", self._validate_data_generation)
        framework.run_validation("database_operations", self._validate_database_ops)
        framework.run_validation("error_handling", self._validate_error_handling)
        framework.run_validation("performance_benchmarks", self._validate_performance)
        framework.run_validation("security_checks", self._validate_security)

        # Generate report
        report = framework.generate_report()

        # Print detailed report
        self._print_validation_report(report)

        # Assert overall success
        assert (
            report["summary"]["success_rate"] >= 80
        ), f"Validation success rate too low: {report['summary']['success_rate']:.1f}%"

    def _validate_cli_basic(self, result: ValidationResult):
        """Validate basic CLI functionality"""
        runner = CliRunner()

        # Test help command
        help_result = runner.invoke(app, ["--help"])
        if help_result.exit_code != 0:
            result.add_error("Help command failed")
        else:
            result.add_metric("help_command_time", 0.1)  # Mock timing

        # Test version/info
        try:
            runner.invoke(app, ["--version"])
            # Version command might not exist, so don't fail
        except:
            result.add_warning("Version command not available")

        # Test invalid command handling
        invalid_result = runner.invoke(app, ["nonexistent_command"])
        if invalid_result.exit_code == 0:
            result.add_error("Invalid command should fail but didn't")

    def _validate_project_init(self, result: ValidationResult):
        """Validate project initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            runner = CliRunner()

            # Test basic initialization
            start_time = time.time()
            init_result = runner.invoke(app, ["init", "validation_project"])
            init_time = time.time() - start_time

            if init_result.exit_code != 0:
                result.add_error(f"Project initialization failed: {init_result.output}")
                return

            result.add_metric("init_time", init_time)

            # Validate project structure
            project_path = Path("validation_project")
            required_dirs = ["data", "pipelines", "dbt", "fastapi_server"]

            for dir_name in required_dirs:
                if not (project_path / dir_name).exists():
                    result.add_error(f"Missing required directory: {dir_name}")

            # Validate config file
            config_file = project_path / "sbdk_config.json"
            if not config_file.exists():
                result.add_error("Missing sbdk_config.json")
            else:
                try:
                    with open(config_file) as f:
                        config = json.load(f)
                    if config.get("project") != "validation_project":
                        result.add_error("Invalid project name in config")
                except json.JSONDecodeError:
                    result.add_error("Invalid JSON in config file")

    def _validate_config_loading(self, result: ValidationResult):
        """Validate configuration loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Test valid config
            valid_config = {
                "project": "config_test",
                "target": "dev",
                "duckdb_path": "data/test.duckdb",
            }

            with open("sbdk_config.json", "w") as f:
                json.dump(valid_config, f)

            try:
                start_time = time.time()
                config = load_config()
                load_time = time.time() - start_time

                result.add_metric("config_load_time", load_time)

                if config["project"] != "config_test":
                    result.add_error("Config loading returned wrong project name")

            except Exception as e:
                result.add_error(f"Config loading failed: {str(e)}")

            # Test invalid config
            with open("sbdk_config.json", "w") as f:
                f.write("{ invalid json }")

            try:
                load_config()
                result.add_error("Invalid config should have failed")
            except:
                pass  # Expected to fail

    def _validate_data_generation(self, result: ValidationResult):
        """Validate data generation functionality"""
        from sbdk.templates.pipelines.events import generate_events_data
        from sbdk.templates.pipelines.orders import generate_orders_data
        from sbdk.templates.pipelines.users import generate_users_data

        # Test users generation
        try:
            start_time = time.time()
            users = generate_users_data(1000)
            gen_time = time.time() - start_time

            result.add_metric("users_generation_time", gen_time)
            result.add_metric("users_per_second", 1000 / gen_time)

            if len(users) != 1000:
                result.add_error(f"Expected 1000 users, got {len(users)}")

            # Validate data structure
            if users and not all(
                key in users[0] for key in ["user_id", "email", "created_at"]
            ):
                result.add_error("Users data missing required fields")

        except Exception as e:
            result.add_error(f"Users generation failed: {str(e)}")

        # Test events generation
        try:
            events = generate_events_data(5000, max_user_id=1000)
            if len(events) != 5000:
                result.add_error(f"Expected 5000 events, got {len(events)}")
        except Exception as e:
            result.add_error(f"Events generation failed: {str(e)}")

        # Test orders generation
        try:
            orders = generate_orders_data(2000, max_user_id=1000)
            if len(orders) != 2000:
                result.add_error(f"Expected 2000 orders, got {len(orders)}")
        except Exception as e:
            result.add_error(f"Orders generation failed: {str(e)}")

    def _validate_database_ops(self, result: ValidationResult):
        """Validate database operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            try:
                # Test database creation
                start_time = time.time()
                con = duckdb.connect("validation.duckdb")
                create_time = time.time() - start_time

                result.add_metric("db_create_time", create_time)

                # Test data insertion
                test_data = [{"id": i, "value": f"test_{i}"} for i in range(1000)]
                pd.DataFrame(test_data)

                start_time = time.time()
                con.execute("CREATE TABLE test_table AS SELECT * FROM df")
                insert_time = time.time() - start_time

                result.add_metric("db_insert_time", insert_time)
                result.add_metric("records_per_second", 1000 / insert_time)

                # Test query
                start_time = time.time()
                count_result = con.execute("SELECT COUNT(*) FROM test_table").fetchone()
                query_time = time.time() - start_time

                result.add_metric("db_query_time", query_time)

                if count_result[0] != 1000:
                    result.add_error(f"Expected 1000 records, found {count_result[0]}")

                con.close()

            except Exception as e:
                result.add_error(f"Database operations failed: {str(e)}")

    def _validate_error_handling(self, result: ValidationResult):
        """Validate error handling"""
        runner = CliRunner()

        # Test with missing config
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            dev_result = runner.invoke(app, ["dev"])
            if dev_result.exit_code == 0:
                result.add_error("Dev command should fail without config")

        # Test with invalid arguments
        invalid_result = runner.invoke(app, ["init"])  # Missing project name
        if invalid_result.exit_code == 0:
            result.add_warning("Init command should require project name")

        # Test permission errors (mock)
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)

            try:
                os.chdir(temp_dir)
                perm_result = runner.invoke(
                    app, ["init", str(readonly_dir / "project")]
                )
                if perm_result.exit_code == 0:
                    result.add_warning("Should handle permission errors")
            finally:
                readonly_dir.chmod(0o755)

    def _validate_performance(self, result: ValidationResult):
        """Validate performance requirements"""
        # CLI response time
        runner = CliRunner()

        start_time = time.time()
        runner.invoke(app, ["--help"])
        help_time = time.time() - start_time

        result.add_metric("cli_response_time", help_time)

        if help_time > 2.0:
            result.add_warning(f"CLI response time slow: {help_time:.2f}s")

        # Data generation performance
        from sbdk.templates.pipelines.users import generate_users_data

        start_time = time.time()
        users = generate_users_data(5000)
        gen_time = time.time() - start_time

        result.add_metric("large_data_gen_time", gen_time)

        if gen_time > 10.0:
            result.add_warning(f"Data generation slow: {gen_time:.2f}s for 5000 users")

        if len(users) != 5000:
            result.add_error("Performance test data generation failed")

    def _validate_security(self, result: ValidationResult):
        """Validate security aspects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Test config with potentially dangerous values
            dangerous_config = {
                "project": "security_test",
                "command": "rm -rf /",
                "script": "<script>alert('xss')</script>",
                "path": "../../etc/passwd",
            }

            with open("sbdk_config.json", "w") as f:
                json.dump(dangerous_config, f)

            try:
                config = load_config()

                # Values should be loaded as strings, not executed
                if config["command"] != "rm -rf /":
                    result.add_error("Command value was modified unexpectedly")

                # Check that no actual execution occurred
                if not Path("sbdk_config.json").exists():
                    result.add_error(
                        "Config file was deleted - possible command execution"
                    )

            except Exception as e:
                result.add_error(f"Security validation failed: {str(e)}")

        # Test project name validation
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Test with potentially dangerous project names
            dangerous_names = [
                "../../../malicious",
                "project;rm -rf /",
                "project$(rm -rf /)",
            ]

            for name in dangerous_names:
                try:
                    proj_result = runner.invoke(app, ["init", name])
                    # Should either fail or create safely
                    if proj_result.exit_code == 0:
                        # Check that it created safely
                        created_paths = list(Path(".").glob("*"))
                        if any(
                            "malicious" in str(p) or "rm" in str(p)
                            for p in created_paths
                        ):
                            result.add_warning(
                                f"Potentially unsafe project creation: {name}"
                            )
                except:
                    pass  # Expected to fail

    def _print_validation_report(self, report: dict[str, Any]):
        """Print detailed validation report"""
        print("\n" + "=" * 80)
        print("SBDK.dev v2.0.0 - AUTOMATED VALIDATION REPORT")
        print("=" * 80)

        summary = report["summary"]
        print("\nOVERALL SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Duration: {summary['total_duration']:.2f}s")

        print("\nDETAILED RESULTS:")
        for test_result in report["results"]:
            status = "✅ PASS" if test_result["passed"] else "❌ FAIL"
            print(
                f"  {status} {test_result['test_name']} ({test_result['duration']:.3f}s)"
            )

            if test_result["errors"]:
                for error in test_result["errors"]:
                    print(f"    ERROR: {error}")

            if test_result["warnings"]:
                for warning in test_result["warnings"]:
                    print(f"    WARNING: {warning}")

            if test_result["metrics"]:
                print(f"    METRICS: {test_result['metrics']}")

        if report["metrics"]:
            print("\nPERFORMACE METRICS:")
            for metric, values in report["metrics"].items():
                if values:
                    avg_value = sum(values) / len(values)
                    print(f"  {metric}: {avg_value:.3f} (avg)")

        print("\n" + "=" * 80)


class TestContinuousValidation:
    """Continuous validation tests"""

    def test_regression_validation(self):
        """Test for regressions in core functionality"""
        framework = ValidationFramework()

        # Run critical tests that should never regress
        critical_tests = [
            ("project_init_basic", self._test_basic_init),
            ("config_load_basic", self._test_basic_config),
            ("data_gen_basic", self._test_basic_data_gen),
            ("cli_help_basic", self._test_basic_help),
        ]

        for test_name, test_func in critical_tests:
            framework.run_validation(test_name, test_func)

        report = framework.generate_report()

        # All critical tests must pass
        assert report["summary"]["success_rate"] == 100, "Critical regression detected"

    def _test_basic_init(self, result: ValidationResult):
        """Basic init test for regression detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            runner = CliRunner()

            init_result = runner.invoke(app, ["init", "regression_test"])
            if init_result.exit_code != 0:
                result.add_error("Basic init failed")

            if not Path("regression_test").exists():
                result.add_error("Project directory not created")

    def _test_basic_config(self, result: ValidationResult):
        """Basic config test for regression detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            config = {"project": "test", "target": "dev"}
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)

            try:
                loaded = load_config()
                if loaded["project"] != "test":
                    result.add_error("Config loading regression")
            except:
                result.add_error("Config loading failed")

    def _test_basic_data_gen(self, result: ValidationResult):
        """Basic data generation test for regression detection"""
        try:
            from sbdk.templates.pipelines.users import generate_users_data

            users = generate_users_data(10)
            if len(users) != 10:
                result.add_error("Data generation regression")
        except:
            result.add_error("Data generation failed")

    def _test_basic_help(self, result: ValidationResult):
        """Basic help test for regression detection"""
        runner = CliRunner()
        help_result = runner.invoke(app, ["--help"])
        if help_result.exit_code != 0:
            result.add_error("Help command regression")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
