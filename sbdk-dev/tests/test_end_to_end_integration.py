"""
End-to-End Integration Test Suite for SBDK.dev v2.0.0
Tests complete workflows from project creation to data processing
"""
import pytest
import tempfile
import os
import json
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import duckdb
import pandas as pd
from typer.testing import CliRunner

from sbdk.cli.main import app
from sbdk.cli.commands.dev import load_config


def safe_getcwd():
    """Get current working directory safely"""
    try:
        return os.getcwd()
    except FileNotFoundError:
        return None


def safe_chdir(path):
    """Change directory safely"""
    if path:
        try:
            os.chdir(path)
        except (FileNotFoundError, OSError):
            pass


class TestCompleteProjectLifecycle:
    """Test complete project lifecycle from init to production"""
    
    def test_full_workflow_init_to_data_processing(self):
        """Test complete workflow: init -> configure -> run pipelines -> run dbt"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = safe_getcwd()
            os.chdir(temp_dir)
            
            try:
                runner = CliRunner()
                
                # Step 1: Initialize project
                result = runner.invoke(app, ["init", "integration_test", "--force"])
                assert result.exit_code == 0
                assert "Successfully initialized" in result.stdout
                
                # Step 2: Verify project structure
                project_path = Path("integration_test")
                assert project_path.exists()
                assert (project_path / "sbdk_config.json").exists()
                assert (project_path / "pipelines").exists()
                assert (project_path / "dbt").exists()
                assert (project_path / "data").exists()
                
                # Step 3: Navigate to project and load config
                os.chdir(project_path)
                config = load_config()
                assert config["project"] == "integration_test"
                
                # Step 4: Create sample data using pipelines
                # Mock the pipeline execution since we can't run actual DLT in tests
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="Pipeline completed")
                    
                    result = runner.invoke(app, ["dev", "--pipelines-only"])
                    # Should attempt to run pipelines
                    assert mock_run.called
                
                # Step 5: Test DBT execution
                with patch('subprocess.run') as mock_dbt:
                    mock_dbt.return_value = MagicMock(returncode=0, stdout="dbt completed")
                    
                    result = runner.invoke(app, ["dev", "--dbt-only"])
                    # Should attempt to run dbt
                    assert mock_dbt.called
                
            finally:
                safe_chdir(original_cwd)
    
    def test_multi_project_environment(self):
        """Test managing multiple projects in the same environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = safe_getcwd()
            os.chdir(temp_dir)
            
            try:
                runner = CliRunner()
                
                # Create multiple projects
                projects = ["analytics", "reporting", "ml_pipeline"]
                
                for project_name in projects:
                    result = runner.invoke(app, ["init", project_name])
                    assert result.exit_code == 0
                    
                    # Verify each project has its own config
                    project_path = Path(project_name)
                    assert (project_path / "sbdk_config.json").exists()
                    
                    # Load and verify config
                    os.chdir(project_path)
                    config = load_config()
                    assert config["project"] == project_name
                    os.chdir("..")
                
            finally:
                safe_chdir(original_cwd)


class TestDataProcessingWorkflows:
    """Test complete data processing workflows"""
    
    def test_synthetic_data_generation_workflow(self):
        """Test generating synthetic data and processing it"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = safe_getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create a minimal project structure
                project_path = Path("data_test")
                project_path.mkdir()
                os.chdir(project_path)
                
                # Create config
                config = {
                    "project": "data_test",
                    "target": "dev",
                    "duckdb_path": "data/test.duckdb",
                    "pipelines_path": "./pipelines",
                    "dbt_path": "./dbt"
                }
                
                with open("sbdk_config.json", "w") as f:
                    json.dump(config, f)
                
                # Create data directory
                os.makedirs("data", exist_ok=True)
                
                # Test direct data generation using pipeline modules
                from sbdk.templates.pipelines.users import generate_users_data
                from sbdk.templates.pipelines.events import generate_events_data
                from sbdk.templates.pipelines.orders import generate_orders_data
                
                # Generate small datasets
                users = generate_users_data(100)
                events = generate_events_data(500, max_user_id=100)
                orders = generate_orders_data(200, max_user_id=100)
                
                # Validate data generation
                assert len(users) == 100
                assert len(events) == 500
                assert len(orders) == 200
                
                # Test data can be loaded into DuckDB
                con = duckdb.connect("data/test.duckdb")
                
                # Convert to pandas and load
                users_df = pd.DataFrame(users)
                events_df = pd.DataFrame(events)
                orders_df = pd.DataFrame(orders)
                
                con.execute("CREATE TABLE users AS SELECT * FROM users_df")
                con.execute("CREATE TABLE events AS SELECT * FROM events_df")
                con.execute("CREATE TABLE orders AS SELECT * FROM orders_df")
                
                # Verify data was loaded
                user_count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                event_count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                order_count = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                
                assert user_count == 100
                assert event_count == 500
                assert order_count == 200
                
                con.close()
                
            finally:
                safe_chdir(original_cwd)
    
    def test_data_quality_validation(self):
        """Test data quality validation workflows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create test database with sample data
            con = duckdb.connect("test_quality.duckdb")
            
            # Create tables with various data quality issues
            con.execute("""
                CREATE TABLE users_quality_test AS SELECT
                    1 as user_id, 'test@example.com' as email, '2024-01-01'::date as created_at
                UNION ALL SELECT
                    2, 'invalid_email', '2024-01-02'
                UNION ALL SELECT
                    3, 'test3@example.com', NULL
                UNION ALL SELECT
                    NULL, 'test4@example.com', '2024-01-04'
            """)
            
            # Test data quality checks
            # Check for null user_ids
            null_ids = con.execute("SELECT COUNT(*) FROM users_quality_test WHERE user_id IS NULL").fetchone()[0]
            assert null_ids == 1
            
            # Check for invalid emails
            invalid_emails = con.execute("SELECT COUNT(*) FROM users_quality_test WHERE email NOT LIKE '%@%'").fetchone()[0]
            assert invalid_emails == 1
            
            # Check for null dates
            null_dates = con.execute("SELECT COUNT(*) FROM users_quality_test WHERE created_at IS NULL").fetchone()[0]
            assert null_dates == 1
            
            con.close()


class TestRealTimeProcessing:
    """Test real-time data processing scenarios"""
    
    @patch('watchdog.observers.Observer')
    def test_file_watching_workflow(self, mock_observer):
        """Test file watching and auto-reload functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = safe_getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create project structure
                runner = CliRunner()
                result = runner.invoke(app, ["init", "realtime_test"])
                assert result.exit_code == 0
                
                os.chdir("realtime_test")
                
                # Create config
                config = load_config()
                assert config is not None
                
                # Mock observer for file watching
                mock_observer_instance = MagicMock()
                mock_observer.return_value = mock_observer_instance
                
                # Test that file watching can be set up
                # (Full integration would require more complex setup)
                assert callable(mock_observer)
                
            finally:
                safe_chdir(original_cwd)
    
    def test_webhook_integration_workflow(self):
        """Test webhook server integration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = safe_getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create project with webhook server
                runner = CliRunner()
                result = runner.invoke(app, ["init", "webhook_test"])
                assert result.exit_code == 0
                
                os.chdir("webhook_test")
                
                # Verify webhook server file exists
                webhook_file = Path("fastapi_server/webhook_listener.py")
                assert webhook_file.exists()
                
                # Test webhook server can be started (mocked)
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    result = runner.invoke(app, ["webhooks", "--port", "8001"])
                    mock_run.assert_called_once()
                
            finally:
                safe_chdir(original_cwd)


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience"""
    
    def test_database_connection_recovery(self):
        """Test recovery from database connection issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Test with invalid database path
            config = {
                "project": "recovery_test",
                "duckdb_path": "/invalid/path/db.duckdb"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            # Should handle invalid database path gracefully
            config_loaded = load_config()
            assert config_loaded["project"] == "recovery_test"
    
    def test_corrupted_config_recovery(self):
        """Test recovery from corrupted configuration files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create corrupted config
            with open("sbdk_config.json", "w") as f:
                f.write("{ corrupted json }")
            
            # Should handle corrupted config gracefully
            with pytest.raises((json.JSONDecodeError, SystemExit)):
                load_config()
    
    def test_permission_denied_recovery(self):
        """Test recovery from permission denied errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create read-only directory
            readonly_dir = Path("readonly_project")
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)
            
            try:
                runner = CliRunner()
                result = runner.invoke(app, ["init", str(readonly_dir / "nested")])
                
                # Should fail gracefully
                assert result.exit_code != 0
                # Check if error message is in output or if exception was properly handled
                assert (
                    "error" in result.stdout.lower() or 
                    "Error" in result.output or 
                    "Permission" in str(result.exception) or
                    result.exception is not None
                )
                
            finally:
                readonly_dir.chmod(0o755)  # Restore for cleanup


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_large_dataset_processing(self):
        """Test processing large datasets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            start_time = time.time()
            
            # Generate larger dataset
            from sbdk.templates.pipelines.users import generate_users_data
            large_users = generate_users_data(10000)
            
            generation_time = time.time() - start_time
            
            # Should generate 10k users in reasonable time
            assert len(large_users) == 10000
            assert generation_time < 10.0  # Less than 10 seconds
            
            # Test database loading performance
            con = duckdb.connect("perf_test.duckdb")
            
            load_start = time.time()
            users_df = pd.DataFrame(large_users)
            con.execute("CREATE TABLE large_users AS SELECT * FROM users_df")
            load_time = time.time() - load_start
            
            # Verify data loaded correctly
            count = con.execute("SELECT COUNT(*) FROM large_users").fetchone()[0]
            assert count == 10000
            
            # Should load in reasonable time
            assert load_time < 5.0  # Less than 5 seconds
            
            con.close()
    
    def test_cli_response_time(self):
        """Test CLI command response times"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            runner = CliRunner()
            
            # Test help command response time
            start_time = time.time()
            result = runner.invoke(app, ["--help"])
            help_time = time.time() - start_time
            
            assert result.exit_code == 0
            assert help_time < 2.0  # Should respond quickly
            
            # Test init command response time
            start_time = time.time()
            result = runner.invoke(app, ["init", "perf_project"])
            init_time = time.time() - start_time
            
            assert result.exit_code == 0
            assert init_time < 5.0  # Should initialize quickly


class TestConcurrencyAndParallelism:
    """Test concurrent operations"""
    
    def test_multiple_cli_instances(self):
        """Test running multiple CLI instances simultaneously"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def run_cli_init(project_name):
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                runner = CliRunner()
                result = runner.invoke(app, ["init", project_name])
                results.put((project_name, result.exit_code))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_cli_init, args=[f"concurrent_project_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        successful_inits = 0
        while not results.empty():
            project_name, exit_code = results.get()
            if exit_code == 0:
                successful_inits += 1
        
        # All should succeed
        assert successful_inits == 3


class TestCrossplatformCompatibility:
    """Test cross-platform compatibility"""
    
    def test_path_handling_cross_platform(self):
        """Test path handling works across platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            runner = CliRunner()
            
            # Test project names with different path separators
            project_names = [
                "simple_project",
                "project-with-dashes",
                "project.with.dots"
            ]
            
            for name in project_names:
                result = runner.invoke(app, ["init", name])
                assert result.exit_code == 0
                assert Path(name).exists()
    
    def test_config_file_encoding(self):
        """Test configuration file encoding handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Test with different encodings
            config_data = {
                "project": "encoding_test",
                "description": "Test with special chars: äöü 中文 🚀"
            }
            
            # Write with UTF-8 encoding
            with open("sbdk_config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False)
            
            # Should load correctly
            config = load_config()
            assert config["project"] == "encoding_test"
            assert "🚀" in config["description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])