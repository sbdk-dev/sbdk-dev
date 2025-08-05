"""
Test the sbdk init command functionality
"""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sbdk.cli.main import app


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def runner():
    """Create a CLI runner"""
    return CliRunner()


def test_init_creates_project_structure(runner, temp_dir):
    """Test that init command creates correct project structure"""
    project_name = "test_analytics"

    # Change to temp directory
    with runner.isolated_filesystem():
        # Run init command
        result = runner.invoke(app, ["init", project_name])

        assert result.exit_code == 0
        assert f"Successfully initialized SBDK project: {project_name}" in result.output

        # Check project directory exists
        project_path = Path(project_name)
        assert project_path.exists()

        # Check required directories
        assert (project_path / "data").exists()
        assert (project_path / "pipelines").exists()
        assert (project_path / "dbt").exists()
        assert (project_path / "fastapi_server").exists()

        # Check config file
        config_path = project_path / "sbdk_config.json"
        assert config_path.exists()

        with open(config_path) as f:
            config = json.load(f)

        assert config["project"] == project_name
        assert config["duckdb_path"] == f"data/{project_name}.duckdb"
        assert config["pipelines_path"] == "./pipelines"
        assert config["dbt_path"] == "./dbt"


def test_init_updates_dbt_project_yml(runner, temp_dir):
    """Test that init updates dbt_project.yml with correct project name"""
    project_name = "my_data_project"

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 0

        # Check dbt_project.yml was updated
        dbt_project_path = Path(project_name) / "dbt" / "dbt_project.yml"
        assert dbt_project_path.exists()

        with open(dbt_project_path) as f:
            content = f.read()

        # Check that project name was replaced
        assert f"name: '{project_name}'" in content
        assert f"profile: '{project_name}'" in content
        assert "sbdk_project" not in content  # Original template name should be gone

        # Check models configuration uses correct project name
        assert f"models:\n  {project_name}:" in content


def test_init_creates_dbt_profile(runner, temp_dir):
    """Test that init creates correct dbt profile"""
    project_name = "analytics_pipeline"

    with runner.isolated_filesystem():
        # Create a fake home directory for testing
        fake_home = Path.cwd() / "fake_home"
        fake_home.mkdir()

        # Temporarily override home directory
        import os

        original_home = os.environ.get("HOME")
        os.environ["HOME"] = str(fake_home)

        try:
            result = runner.invoke(app, ["init", project_name])
            assert result.exit_code == 0

            # Check profiles.yml was created
            profiles_path = fake_home / ".dbt" / "profiles.yml"
            assert profiles_path.exists()

            with open(profiles_path) as f:
                content = f.read()

            # Check profile content
            assert f"{project_name}:" in content
            assert "type: duckdb" in content
            assert (
                f"path: {Path.cwd().absolute()}/{project_name}/data/{project_name}.duckdb"
                in content
            )

        finally:
            # Restore original home
            if original_home:
                os.environ["HOME"] = original_home
            else:
                del os.environ["HOME"]


def test_pipelines_use_config_for_duckdb_path(runner, temp_dir):
    """Test that pipeline templates use config for DuckDB path"""
    project_name = "test_project"

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 0

        # Check each pipeline file
        for pipeline in ["users", "events", "orders"]:
            pipeline_path = Path(project_name) / "pipelines" / f"{pipeline}.py"
            assert pipeline_path.exists()

            with open(pipeline_path) as f:
                content = f.read()

            # Check that pipelines load config
            assert "def load_config() -> dict:" in content
            assert 'with open("sbdk_config.json") as f:' in content
            assert "config = load_config()" in content
            assert 'db_path = Path(config["duckdb_path"])' in content
            assert "con = duckdb.connect(str(db_path))" in content

            # Make sure old hardcoded path is gone
            assert 'duckdb.connect("data/dev.duckdb")' not in content


def test_init_with_force_overwrites(runner, temp_dir):
    """Test that init with --force overwrites existing directory"""
    project_name = "existing_project"

    with runner.isolated_filesystem():
        # Create existing directory
        existing_path = Path(project_name)
        existing_path.mkdir()
        (existing_path / "old_file.txt").write_text("old content")

        # Try without force - should fail
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 1
        assert "already exists" in result.output

        # Try with force - should succeed
        result = runner.invoke(app, ["init", project_name, "--force"])
        assert result.exit_code == 0
        assert f"Successfully initialized SBDK project: {project_name}" in result.output

        # Check new structure exists
        assert (existing_path / "sbdk_config.json").exists()
        assert (existing_path / "pipelines").exists()


def test_init_pipeline_templates_valid(runner, temp_dir):
    """Test that generated pipeline files are valid Python"""
    project_name = "syntax_test"

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 0

        # Try to compile each pipeline file
        import py_compile

        for pipeline in ["users", "events", "orders"]:
            pipeline_path = Path(project_name) / "pipelines" / f"{pipeline}.py"

            # This will raise if syntax is invalid
            py_compile.compile(str(pipeline_path), doraise=True)


def test_init_creates_valid_config(runner, temp_dir):
    """Test that created config file has all required fields"""
    project_name = "config_test"

    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", project_name])
        assert result.exit_code == 0

        config_path = Path(project_name) / "sbdk_config.json"
        with open(config_path) as f:
            config = json.load(f)

        # Check all required fields exist
        required_fields = [
            "project",
            "target",
            "duckdb_path",
            "pipelines_path",
            "dbt_path",
            "profiles_dir",
        ]
        for field in required_fields:
            assert field in config, f"Config missing required field: {field}"

        # Check values are reasonable
        assert config["project"] == project_name
        assert config["target"] == "dev"
        assert config["duckdb_path"] == f"data/{project_name}.duckdb"
        assert config["pipelines_path"] == "./pipelines"
        assert config["dbt_path"] == "./dbt"
        assert config["profiles_dir"] == "~/.dbt"
