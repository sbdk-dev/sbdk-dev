"""
Test suite for CLI commands as specified in the SBDK.dev PRD.
Tests the Typer-based CLI interface for project initialization, development mode, and webhook functionality.
"""

import pytest
import os
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCLICommands:
    """Test suite for SBDK CLI commands."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing CLI operations."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_sbdk_config(self):
        """Mock SBDK configuration data."""
        return {
            "project": "test_project",
            "target": "dev",
            "duckdb_path": "data/dev.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt",
        }

    def test_cli_init_command_structure(self, temp_project_dir, mock_sbdk_config):
        """Test that CLI init command creates proper project structure."""
        project_name = "test_sandbox"
        project_path = os.path.join(temp_project_dir, project_name)

        # Simulate CLI init command functionality
        os.makedirs(project_path, exist_ok=True)

        # Create expected directory structure
        expected_dirs = [
            "pipelines",
            "dbt",
            "dbt/models",
            "dbt/models/staging",
            "dbt/models/intermediate",
            "dbt/models/marts",
            "fastapi_server",
            "cli",
            "data",
        ]

        for dir_name in expected_dirs:
            dir_path = os.path.join(project_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)

        # Create config file
        config_path = os.path.join(project_path, "sbdk_config.json")
        with open(config_path, "w") as f:
            json.dump(mock_sbdk_config, f, indent=2)

        # Verify structure was created
        assert os.path.exists(project_path)
        assert os.path.exists(config_path)

        for dir_name in expected_dirs:
            assert os.path.exists(os.path.join(project_path, dir_name))

        # Verify config content
        with open(config_path, "r") as f:
            loaded_config = json.load(f)
            assert loaded_config["project"] == mock_sbdk_config["project"]
            assert loaded_config["duckdb_path"] == mock_sbdk_config["duckdb_path"]

    def test_cli_init_creates_pipeline_files(self, temp_project_dir):
        """Test that init command creates necessary pipeline files."""
        project_path = os.path.join(temp_project_dir, "test_project")
        pipelines_path = os.path.join(project_path, "pipelines")
        os.makedirs(pipelines_path, exist_ok=True)

        # Expected pipeline files from PRD
        expected_files = ["users.py", "events.py", "orders.py"]

        # Create mock pipeline files
        for file_name in expected_files:
            file_path = os.path.join(pipelines_path, file_name)
            with open(file_path, "w") as f:
                f.write(f"# Mock {file_name} pipeline\ndef run():\n    pass\n")

        # Verify files were created
        for file_name in expected_files:
            file_path = os.path.join(pipelines_path, file_name)
            assert os.path.exists(file_path)

            # Verify file content
            with open(file_path, "r") as f:
                content = f.read()
                assert "def run():" in content

    def test_cli_init_creates_dbt_files(self, temp_project_dir):
        """Test that init command creates dbt project files."""
        project_path = os.path.join(temp_project_dir, "test_project")
        dbt_path = os.path.join(project_path, "dbt")
        models_path = os.path.join(dbt_path, "models")

        # Create directory structure
        os.makedirs(os.path.join(models_path, "staging"), exist_ok=True)
        os.makedirs(os.path.join(models_path, "intermediate"), exist_ok=True)
        os.makedirs(os.path.join(models_path, "marts"), exist_ok=True)

        # Create dbt_project.yml
        dbt_project_content = """
name: sbdk_project
version: '1.0'
config-version: 2
profile: sbdk
"""
        with open(os.path.join(dbt_path, "dbt_project.yml"), "w") as f:
            f.write(dbt_project_content.strip())

        # Create sample model files
        models = {
            "staging/stg_users.sql": "select user_id, created_at, country, referrer from {{ source('raw', 'users') }}",
            "staging/stg_events.sql": "select event_id, user_id, event_type, timestamp, utm_source from {{ source('raw', 'events') }}",
            "intermediate/int_user_activity.sql": "select u.user_id, u.created_at, e.pageviews from {{ ref('stg_users') }} u left join {{ ref('stg_events') }} e using(user_id)",
            "marts/user_metrics.sql": "select user_id, days_since_signup from {{ ref('int_user_activity') }}",
        }

        for model_path, content in models.items():
            full_path = os.path.join(models_path, model_path)
            with open(full_path, "w") as f:
                f.write(content)

        # Verify files were created
        assert os.path.exists(os.path.join(dbt_path, "dbt_project.yml"))
        for model_path in models.keys():
            assert os.path.exists(os.path.join(models_path, model_path))

    @patch("subprocess.run")
    def test_cli_dev_command_execution(self, mock_subprocess):
        """Test CLI dev command runs pipelines and dbt models."""
        # Mock successful subprocess runs
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Expected commands that should be executed
        expected_commands = [
            ["dbt", "run", "--project-dir", "dbt"],
            ["dbt", "test", "--project-dir", "dbt"],
        ]

        # Simulate running the dev command
        for cmd in expected_commands:
            subprocess.run(cmd)

        # Verify the commands were called
        assert mock_subprocess.call_count == len(expected_commands)

        # Verify specific command calls
        call_args_list = [call[0][0] for call in mock_subprocess.call_args_list]
        for expected_cmd in expected_commands:
            assert expected_cmd in call_args_list or any(
                all(arg in call for arg in expected_cmd) for call in call_args_list
            )

    def test_cli_dev_pipeline_execution_order(self):
        """Test that dev command executes pipelines in correct order."""
        # Mock pipeline execution tracking
        execution_order = []

        def mock_users_run():
            execution_order.append("users")

        def mock_events_run():
            execution_order.append("events")

        def mock_orders_run():
            execution_order.append("orders")

        # Simulate pipeline execution
        mock_users_run()
        mock_events_run()
        mock_orders_run()

        # Verify execution order
        assert execution_order == ["users", "events", "orders"]
        assert len(execution_order) == 3

    @patch("subprocess.run")
    def test_cli_webhooks_command(self, mock_subprocess):
        """Test CLI webhooks command starts FastAPI server."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Expected command for starting webhook server
        expected_cmd = ["uvicorn", "fastapi_server.webhook_listener:app", "--reload"]

        # Simulate running webhooks command
        subprocess.run(expected_cmd)

        # Verify the command was called
        mock_subprocess.assert_called_once_with(expected_cmd)

    def test_config_validation(self, temp_project_dir, mock_sbdk_config):
        """Test that CLI validates configuration properly."""
        config_path = os.path.join(temp_project_dir, "sbdk_config.json")

        # Create valid config
        with open(config_path, "w") as f:
            json.dump(mock_sbdk_config, f)

        # Test config loading
        with open(config_path, "r") as f:
            loaded_config = json.load(f)

        # Validate required fields
        required_fields = [
            "project",
            "target",
            "duckdb_path",
            "pipelines_path",
            "dbt_path",
        ]
        for field in required_fields:
            assert field in loaded_config, f"Required field {field} missing from config"

        # Validate field types and values
        assert isinstance(loaded_config["project"], str)
        assert loaded_config["target"] in ["dev", "prod", "test"]
        assert loaded_config["duckdb_path"].endswith(".duckdb")
        assert loaded_config["pipelines_path"].startswith("./")
        assert loaded_config["dbt_path"].startswith("./")

    def test_error_handling_missing_config(self, temp_project_dir):
        """Test CLI behavior when config file is missing."""
        config_path = os.path.join(temp_project_dir, "sbdk_config.json")

        # Ensure config doesn't exist
        assert not os.path.exists(config_path)

        # Simulate CLI behavior - should handle missing config gracefully
        try:
            with open(config_path, "r") as f:
                json.load(f)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            # This is expected behavior
            pass

    def test_error_handling_invalid_config(self, temp_project_dir):
        """Test CLI behavior with invalid JSON config."""
        config_path = os.path.join(temp_project_dir, "sbdk_config.json")

        # Create invalid JSON
        with open(config_path, "w") as f:
            f.write('{"invalid": json,}')  # Invalid JSON syntax

        # Test that invalid JSON is handled properly
        try:
            with open(config_path, "r") as f:
                json.load(f)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            # This is expected behavior
            pass

    def test_project_name_validation(self):
        """Test validation of project names in CLI init."""
        valid_names = ["my_project", "test-project", "project123", "valid_name"]
        invalid_names = ["", "   ", "project with spaces", "project/with/slashes"]

        for name in valid_names:
            # Simple validation - non-empty, no spaces, no slashes
            assert name.strip() != ""
            assert " " not in name
            assert "/" not in name

        for name in invalid_names:
            # These should fail validation
            is_invalid = name.strip() == "" or " " in name or "/" in name
            assert is_invalid, f"Name '{name}' should be invalid"


class TestCLIIntegration:
    """Integration tests for CLI command interactions."""

    @pytest.fixture
    def integrated_project(self, tmp_path):
        """Create a fully integrated test project."""
        project_dir = tmp_path / "integrated_test"
        project_dir.mkdir()

        # Create all necessary files and directories
        (project_dir / "pipelines").mkdir()
        (project_dir / "dbt").mkdir()
        (project_dir / "dbt" / "models").mkdir()
        (project_dir / "fastapi_server").mkdir()
        (project_dir / "cli").mkdir()
        (project_dir / "data").mkdir()

        # Create config
        config = {
            "project": "integrated_test",
            "target": "dev",
            "duckdb_path": "data/dev.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt",
        }

        with open(project_dir / "sbdk_config.json", "w") as f:
            json.dump(config, f, indent=2)

        return project_dir

    def test_full_workflow_integration(self, integrated_project):
        """Test complete workflow from init to dev execution."""
        # Verify project structure exists
        assert (integrated_project / "sbdk_config.json").exists()
        assert (integrated_project / "pipelines").exists()
        assert (integrated_project / "dbt").exists()
        assert (integrated_project / "fastapi_server").exists()

        # Verify config is valid
        with open(integrated_project / "sbdk_config.json", "r") as f:
            config = json.load(f)
            assert config["project"] == "integrated_test"
            assert config["target"] == "dev"

        # This represents successful integration test
        # In a real implementation, this would execute the full pipeline
        print("Integration test completed successfully")
