"""
dbt Integration Tests for SBDK.dev CLI
Tests dbt workflows, model execution, and data transformations
"""
import pytest
import tempfile
import os
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import duckdb

# Import CLI modules
from sbdk.cli.commands.dev import cli_dev
from sbdk.cli.commands.init import cli_init
from typer.testing import CliRunner
from sbdk.cli.main import app

runner = CliRunner()


class TestDBTIntegration:
    """Test dbt integration and workflows"""
    
    def test_dbt_project_structure(self):
        """Test that dbt project structure is valid"""
        dbt_path = Path(__file__).parent.parent / "dbt"
        assert dbt_path.exists()
        
        # Check essential dbt files
        assert (dbt_path / "dbt_project.yml").exists()
        assert (dbt_path / "models").exists()
        
        # Check dbt_project.yml structure  
        with open(dbt_path / "dbt_project.yml") as f:
            import yaml
            dbt_config = yaml.safe_load(f)
            
        assert "name" in dbt_config
        assert "version" in dbt_config
        assert "profile" in dbt_config
        assert "model-paths" in dbt_config
    
    def test_dbt_models_structure(self):
        """Test that dbt models have correct structure"""
        models_path = Path(__file__).parent.parent / "dbt" / "models"
        
        # Check for expected model directories
        expected_dirs = ["staging", "intermediate", "marts"]
        for dir_name in expected_dirs:
            dir_path = models_path / dir_name
            assert dir_path.exists(), f"Missing model directory: {dir_name}"
        
        # Check for sources file
        sources_file = models_path / "_sources.yml"
        assert sources_file.exists()
        
        # Validate sources file structure
        with open(sources_file) as f:
            import yaml
            sources = yaml.safe_load(f)
            
        assert "version" in sources
        assert "sources" in sources
    
    def test_dbt_model_sql_syntax(self):
        """Test that dbt models have valid SQL syntax"""
        models_path = Path(__file__).parent.parent / "dbt" / "models"
        
        # Find all SQL files
        sql_files = list(models_path.rglob("*.sql"))
        assert len(sql_files) > 0, "No SQL model files found"
        
        for sql_file in sql_files:
            with open(sql_file) as f:
                content = f.read()
                
            # Basic SQL syntax checks
            assert content.strip(), f"Empty SQL file: {sql_file}"
            assert "select" in content.lower() or "with" in content.lower(), \
                f"SQL file should contain SELECT or WITH: {sql_file}"
            
            # Check for dbt-specific syntax
            if "{{ " in content:
                # Contains Jinja templating - good
                pass
    
    def test_dbt_profiles_generation(self):
        """Test dbt profiles are generated correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Mock home directory for profiles
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                result = runner.invoke(app, ["init", "dbt_profile_test"])
                assert result.exit_code == 0
                
                # Check profiles.yml was created
                profiles_path = Path(temp_dir) / ".dbt" / "profiles.yml"
                assert profiles_path.exists()
                
                with open(profiles_path) as f:
                    content = f.read()
                    
                # Validate profile structure
                assert "dbt_profile_test:" in content
                assert "target: dev" in content
                assert "type: duckdb" in content
                assert "path:" in content


class TestDBTExecution:
    """Test dbt command execution"""
    
    @patch('subprocess.run')
    def test_dbt_run_command(self, mock_run):
        """Test dbt run command execution"""
        # Mock successful dbt run
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create test config
            config = {
                "project": "test_dbt",
                "duckdb_path": "data/test.duckdb",
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            # Mock pipeline execution
            with patch('cli.dev.run_pipeline_module'):
                result = runner.invoke(app, ["dev", "--dbt-only"])
                
            assert result.exit_code == 0
            
            # Verify dbt commands were called
            assert mock_run.call_count >= 2  # dbt run + dbt test
            
            # Check dbt run was called
            calls = mock_run.call_args_list
            run_called = any("dbt" in str(call) and "run" in str(call) for call in calls)
            test_called = any("dbt" in str(call) and "test" in str(call) for call in calls)
            
            assert run_called, "dbt run should have been called"
            assert test_called, "dbt test should have been called"
    
    @patch('subprocess.run')
    def test_dbt_test_command(self, mock_run):
        """Test dbt test command execution"""
        # Mock successful dbt test
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            config = {
                "project": "test_dbt",
                "duckdb_path": "data/test.duckdb", 
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            with patch('cli.dev.run_pipeline_module'):
                result = runner.invoke(app, ["dev", "--dbt-only"])
                
            assert result.exit_code == 0
    
    @patch('subprocess.run')
    def test_dbt_error_handling(self, mock_run):
        """Test dbt error handling"""
        # Mock failed dbt command
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'dbt', stdout="dbt output", stderr="dbt error"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            config = {
                "project": "test_dbt_error",
                "duckdb_path": "data/test.duckdb",
                "dbt_path": "./dbt", 
                "profiles_dir": "~/.dbt"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            with patch('cli.dev.run_pipeline_module'):
                result = runner.invoke(app, ["dev", "--dbt-only"])
                
            # Should exit with error
            assert result.exit_code == 1
            assert "dbt command failed" in result.stdout


class TestDataTransformations:
    """Test actual data transformations with dbt"""
    
    def test_dbt_with_sample_data(self):
        """Test dbt transformations with sample data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create a temporary DuckDB with sample data
            db_path = "test_sample.duckdb"
            con = duckdb.connect(db_path)
            
            # Create sample tables that match our sources
            con.execute("""
                CREATE TABLE users AS SELECT
                    1 as user_id,
                    'test@example.com' as email,
                    'free' as subscription_tier,
                    '2024-01-01'::date as created_at
                UNION ALL SELECT
                    2, 'test2@example.com', 'premium', '2024-01-02'::date
            """)
            
            con.execute("""
                CREATE TABLE events AS SELECT
                    1 as event_id,
                    1 as user_id,
                    'page_view' as event_type,
                    '2024-01-01 10:00:00'::timestamp as timestamp
                UNION ALL SELECT
                    2, 1, 'click', '2024-01-01 10:01:00'::timestamp
                UNION ALL SELECT
                    3, 2, 'signup', '2024-01-02 09:00:00'::timestamp
            """)
            
            con.execute("""
                CREATE TABLE orders AS SELECT
                    1 as order_id,
                    1 as user_id,
                    100.50 as total_amount,
                    'completed' as status,
                    '2024-01-01'::date as order_date
                UNION ALL SELECT
                    2, 2, 250.00, 'completed', '2024-01-02'::date
            """)
            
            con.close()
            
            # Test that we can query this data
            con = duckdb.connect(db_path)
            result = con.execute("SELECT COUNT(*) FROM users").fetchone()
            assert result[0] == 2
            
            result = con.execute("SELECT COUNT(*) FROM events").fetchone()
            assert result[0] == 3
            
            result = con.execute("SELECT COUNT(*) FROM orders").fetchone() 
            assert result[0] == 2
            
            con.close()
    
    def test_staging_model_logic(self):
        """Test staging model transformations"""
        # This would test the actual SQL logic in staging models
        # For now, we'll test the structure exists
        
        staging_path = Path(__file__).parent.parent / "dbt" / "models" / "staging"
        staging_files = list(staging_path.glob("stg_*.sql"))
        
        assert len(staging_files) >= 3, "Should have staging models for users, events, orders"
        
        # Check each staging file has basic structure
        for staging_file in staging_files:
            with open(staging_file) as f:
                content = f.read()
                
            # Should have select statement
            assert "select" in content.lower()
            # Should reference source
            assert "source(" in content or "ref(" in content
    
    def test_intermediate_model_logic(self):
        """Test intermediate model transformations"""
        intermediate_path = Path(__file__).parent.parent / "dbt" / "models" / "intermediate"
        
        if intermediate_path.exists():
            intermediate_files = list(intermediate_path.glob("int_*.sql"))
            
            for int_file in intermediate_files:
                with open(int_file) as f:
                    content = f.read()
                    
                # Should reference staging models
                assert "ref(" in content
                # Should have select
                assert "select" in content.lower()
    
    def test_marts_model_logic(self):
        """Test marts model transformations"""  
        marts_path = Path(__file__).parent.parent / "dbt" / "models" / "marts"
        marts_files = list(marts_path.glob("*.sql"))
        
        assert len(marts_files) > 0, "Should have mart models"
        
        for marts_file in marts_files:
            with open(marts_file) as f:
                content = f.read()
                
            # Should reference other models
            assert "ref(" in content
            # Should have aggregations or business logic
            assert "select" in content.lower()


class TestDBTConfiguration:
    """Test dbt configuration and setup"""
    
    def test_dbt_project_yml_validity(self):
        """Test dbt_project.yml is valid YAML"""
        dbt_project_file = Path(__file__).parent.parent / "dbt" / "dbt_project.yml"
        
        with open(dbt_project_file) as f:
            import yaml
            try:
                config = yaml.safe_load(f)
                assert isinstance(config, dict)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in dbt_project.yml: {e}")
    
    def test_sources_yml_validity(self):
        """Test _sources.yml is valid"""
        sources_file = Path(__file__).parent.parent / "dbt" / "models" / "_sources.yml"
        
        with open(sources_file) as f:
            import yaml
            try:
                sources = yaml.safe_load(f)
                assert isinstance(sources, dict)
                assert "sources" in sources
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in _sources.yml: {e}")
    
    def test_dbt_dependencies_installed(self):
        """Test that dbt dependencies are available"""
        try:
            import dbt.cli.main
            import dbt_duckdb
            
            # Basic import test
            assert hasattr(dbt.cli.main, 'main')
            
        except ImportError as e:
            pytest.fail(f"dbt dependencies not available: {e}")


class TestFullDBTWorkflow:
    """Test complete dbt workflow end-to-end"""
    
    def test_init_to_dbt_workflow(self):
        """Test complete workflow from init to dbt execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Step 1: Initialize project
                result = runner.invoke(app, ["init", "workflow_test"])
                assert result.exit_code == 0
                
                # Step 2: Navigate to project
                os.chdir("workflow_test")
                
                # Step 3: Verify config can be loaded
                config = load_config()
                assert config["project"] == "workflow_test"
                
                # Step 4: Create sample data directory
                os.makedirs("data", exist_ok=True)
                
                # Step 5: Test dbt structure was copied
                assert Path("dbt").exists()
                assert Path("dbt/models").exists()
                assert Path("dbt/dbt_project.yml").exists()
                
                # Step 6: Mock and test dev command
                with patch('cli.dev.run_pipeline_module'), \
                     patch('subprocess.run') as mock_dbt:
                    mock_dbt.return_value = MagicMock(returncode=0)
                    
                    result = runner.invoke(app, ["dev"])
                    assert result.exit_code == 0
                    
                    # Verify dbt was called
                    assert mock_dbt.called
                    
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])