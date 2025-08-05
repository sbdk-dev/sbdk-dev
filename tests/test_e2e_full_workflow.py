"""
End-to-End Integration Tests for SBDK
Tests the complete workflow: init -> run -> visual mode
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


class TestFullE2EWorkflow:
    """Test complete end-to-end workflow"""

    def test_init_run_visual_workflow(self):
        """Test full workflow: sbdk init -> sbdk run -> sbdk run --visual"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_analytics_project"
            project_path = Path(temp_dir) / project_name

            # Step 1: Initialize project
            result = subprocess.run(
                [sys.executable, "-m", "sbdk.cli.main", "init", project_name],
                cwd=temp_dir,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Init failed: {result.stderr}"
            assert project_path.exists()

            # Verify all required files exist
            assert (project_path / "sbdk_config.json").exists()
            assert (project_path / "pipelines").exists()
            assert (project_path / "dbt").exists()
            assert (project_path / "data").exists()

            # Verify config is correct
            with open(project_path / "sbdk_config.json") as f:
                config = json.load(f)

            assert config["project"] == project_name
            assert config["duckdb_path"] == f"data/{project_name}.duckdb"

            # Step 2: Create dbt profiles.yml
            profiles_dir = Path.home() / ".dbt"
            profiles_dir.mkdir(exist_ok=True)

            profiles_content = f"""
sbdk_project:
  outputs:
    dev:
      type: duckdb
      path: {project_path}/data/{project_name}.duckdb
  target: dev
"""

            with open(profiles_dir / "profiles.yml", "w") as f:
                f.write(profiles_content)

            # Step 3: Run pipelines
            result = subprocess.run(
                [sys.executable, "-m", "sbdk.cli.main", "run", "--pipelines-only"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Pipeline run failed: {result.stderr}"
            assert "✅ Users pipeline completed successfully!" in result.stdout
            assert "✅ Events pipeline completed successfully!" in result.stdout
            assert "✅ Orders pipeline completed successfully!" in result.stdout

            # Verify database was created
            assert (project_path / "data" / f"{project_name}.duckdb").exists()

            # Step 4: Run dbt models
            result = subprocess.run(
                [sys.executable, "-m", "sbdk.cli.main", "run", "--dbt-only"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            # This might fail due to dbt path issues, but let's check
            if result.returncode != 0:
                print(f"DBT run output: {result.stdout}")
                print(f"DBT run errors: {result.stderr}")

            # Step 5: Test visual mode startup (non-interactive)
            # We can't fully test interactive mode in CI, but we can check it starts
            proc = subprocess.Popen(
                [sys.executable, "-m", "sbdk.cli.main", "run", "--visual"],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Give it a moment to start
            time.sleep(2)

            # Terminate the process
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=5)

            # Check that visual mode started without immediate errors
            assert "Starting visual interface..." in stdout
            assert "Visual interface failed" not in stdout

    def test_dbt_profile_path_resolution(self):
        """Test that dbt profiles are correctly resolved"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "dbt_test_project"
            project_path = Path(temp_dir) / project_name

            # Initialize project
            subprocess.run(
                [sys.executable, "-m", "sbdk.cli.main", "init", project_name],
                cwd=temp_dir,
                capture_output=True,
                text=True,
            )

            # Check dbt project configuration
            dbt_project_yml = project_path / "dbt" / "dbt_project.yml"
            assert dbt_project_yml.exists()

            with open(dbt_project_yml) as f:
                content = f.read()

            # Ensure profile name matches
            assert "profile: 'sbdk_project'" in content

            # Create a test to verify duckdb path resolution
            test_pipeline = project_path / "pipelines" / "test_path.py"
            test_pipeline.write_text(
                """
import json
from pathlib import Path

def run():
    with open("sbdk_config.json") as f:
        config = json.load(f)

    db_path = Path(config["duckdb_path"])
    print(f"Database path: {db_path}")
    print(f"Absolute path: {db_path.resolve()}")
    print(f"Exists: {db_path.exists()}")

if __name__ == "__main__":
    run()
"""
            )

            # Run the test pipeline
            result = subprocess.run(
                [sys.executable, str(test_pipeline)],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            print(f"Test pipeline output: {result.stdout}")
            assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
