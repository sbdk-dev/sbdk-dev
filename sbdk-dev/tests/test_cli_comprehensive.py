"""
Comprehensive CLI Test Suite for SBDK.dev
Tests all CLI commands, workflows, and user experience scenarios
"""
import pytest
import tempfile
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import typer
from typer.testing import CliRunner

# Import CLI modules
from sbdk.cli.main import app
from sbdk.cli.commands.init import cli_init
from sbdk.cli.commands.dev import cli_dev
from cli.start import cli_start, PipelineHandler
from cli.webhooks import cli_webhooks

runner = CliRunner()


class TestCLIInit:
    """Test CLI initialization functionality"""
    
    def test_init_basic_project(self):
        """Test basic project initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["init", "test_project"])
            
            assert result.exit_code == 0
            assert "Successfully initialized SBDK project: test_project" in result.stdout
            
            # Verify project structure
            project_path = Path("test_project")
            assert project_path.exists()
            assert (project_path / "pipelines").exists()
            assert (project_path / "dbt").exists()
            assert (project_path / "fastapi_server").exists()
            assert (project_path / "data").exists()
            assert (project_path / "sbdk_config.json").exists()
    
    def test_init_with_force_flag(self):
        """Test project initialization with force flag"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create existing directory
            project_path = Path("test_project")
            project_path.mkdir()
            
            # Should fail without force
            result = runner.invoke(app, ["init", "test_project"])
            assert result.exit_code == 1
            assert "already exists" in result.stdout
            
            # Should succeed with force
            result = runner.invoke(app, ["init", "test_project", "--force"])
            assert result.exit_code == 0
    
    def test_init_config_generation(self):
        """Test configuration file generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            runner.invoke(app, ["init", "config_test"])
            
            config_path = Path("config_test/sbdk_config.json")
            assert config_path.exists()
            
            with open(config_path) as f:
                config = json.load(f)
                
            assert config["project"] == "config_test"
            assert config["target"] == "dev"
            assert config["duckdb_path"] == "data/config_test.duckdb"
            assert config["pipelines_path"] == "./pipelines"
            assert config["dbt_path"] == "./dbt"
    
    def test_init_dbt_profiles_creation(self):
        """Test dbt profiles.yml creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Mock home directory
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                runner.invoke(app, ["init", "profiles_test"])
                
                profiles_path = Path(temp_dir) / ".dbt" / "profiles.yml"
                assert profiles_path.exists()
                
                with open(profiles_path) as f:
                    content = f.read()
                    
                assert "profiles_test:" in content
                assert "type: duckdb" in content


class TestCLIDev:
    """Test development mode functionality"""
    
    def test_load_config_success(self):
        """Test successful config loading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "project": "test",
                "duckdb_path": "test.duckdb",
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt"
            }
            json.dump(test_config, f)
            f.flush()
            
            config = load_config(f.name)
            assert config == test_config
            
            os.unlink(f.name)
    
    def test_load_config_missing_file(self):
        """Test config loading with missing file"""
        with pytest.raises(typer.Exit):
            load_config("nonexistent_config.json")
    
    @patch('subprocess.run')
    def test_run_pipeline_module_success(self, mock_run):
        """Test successful pipeline module execution"""
        mock_run.return_value = MagicMock(stdout="Pipeline completed", stderr="")
        
        # Should not raise exception
        run_pipeline_module("users")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "pipelines.users" in args[2]
    
    @patch('subprocess.run')
    def test_run_pipeline_module_failure(self, mock_run):
        """Test pipeline module execution failure"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr="Error occurred")
        
        with pytest.raises(typer.Exit):
            run_pipeline_module("invalid_module")
    
    def test_dev_command_pipelines_only(self):
        """Test dev command with pipelines-only flag"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create minimal config
            config = {
                "project": "test",
                "duckdb_path": "data/test.duckdb",
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            # Mock pipeline modules
            with patch('cli.dev.run_pipeline_module') as mock_pipeline:
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                
                # Should call pipeline modules but not dbt
                assert mock_pipeline.call_count == 3  # users, events, orders
                assert result.exit_code == 0


class TestCLIStart:
    """Test development server functionality"""
    
    def test_pipeline_handler_debounce(self):
        """Test file change debouncing"""
        handler = PipelineHandler(debounce_seconds=1.0)
        
        # Mock event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "test.py"
        
        # First call should trigger
        with patch('cli.start.cli_dev') as mock_dev:
            handler.on_modified(mock_event)
            mock_dev.assert_called_once()
        
        # Immediate second call should be debounced
        with patch('cli.start.cli_dev') as mock_dev:
            handler.on_modified(mock_event)
            mock_dev.assert_not_called()
    
    def test_pipeline_handler_file_filtering(self):
        """Test file extension filtering"""
        handler = PipelineHandler()
        
        # Python file should trigger
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "test.py"
        
        with patch('cli.start.cli_dev') as mock_dev:
            handler.on_modified(mock_event)
            mock_dev.assert_called_once()
        
        # Non-relevant file should not trigger
        mock_event.src_path = "test.txt"
        handler.last_triggered = 0  # Reset debounce
        
        with patch('cli.start.cli_dev') as mock_dev:
            handler.on_modified(mock_event)
            mock_dev.assert_not_called()


class TestCLIWebhooks:
    """Test webhook server functionality"""
    
    @patch('subprocess.run')
    def test_webhooks_command_success(self, mock_run):
        """Test successful webhook server start"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create mock fastapi server file
            server_dir = Path("fastapi_server")
            server_dir.mkdir()
            (server_dir / "webhook_listener.py").touch()
            
            # Mock successful subprocess run
            mock_run.return_value = None
            
            result = runner.invoke(app, ["webhooks", "--port", "9000"])
            
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "uvicorn" in args
            assert "--port" in args
            assert "9000" in args
    
    def test_webhooks_missing_server(self):
        """Test webhook command with missing server file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["webhooks"])
            
            assert result.exit_code == 1
            assert "FastAPI server not found" in result.stdout


class TestCLIIntegration:
    """Test full CLI integration workflows"""
    
    def test_full_project_lifecycle(self):
        """Test complete project creation and development workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Step 1: Initialize project
            result = runner.invoke(app, ["init", "integration_test"])
            assert result.exit_code == 0
            
            # Step 2: Verify project structure
            project_path = Path("integration_test")
            assert (project_path / "sbdk_config.json").exists()
            assert (project_path / "pipelines").exists()
            assert (project_path / "dbt").exists()
            
            # Step 3: Change to project directory and test config loading
            os.chdir(project_path)
            config = load_config()
            assert config["project"] == "integration_test"
            
            # Step 4: Test development command (mock the actual execution)
            with patch('cli.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                assert result.exit_code == 0
    
    def test_version_command(self):
        """Test version command"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "SBDK.dev v1.0.0" in result.stdout
    
    def test_help_commands(self):
        """Test help functionality"""
        # Main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "SBDK.dev" in result.stdout
        
        # Command-specific help
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize a new SBDK project" in result.stdout


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_command(self):
        """Test handling of invalid commands"""
        result = runner.invoke(app, ["invalid_command"])
        assert result.exit_code != 0
    
    def test_dev_without_config(self):
        """Test dev command without config file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["dev"])
            assert result.exit_code == 1
            assert "Config file not found" in result.stdout
    
    def test_malformed_config(self):
        """Test handling of malformed config file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create malformed JSON config
            with open("sbdk_config.json", "w") as f:
                f.write("{ invalid json }")
            
            with pytest.raises(json.JSONDecodeError):
                load_config()


class TestUserExperience:
    """Test user experience aspects"""
    
    def test_colorful_output(self):
        """Test that CLI produces rich, colorful output"""
        result = runner.invoke(app, ["version"])
        
        # Check for rich markup or ANSI codes (basic test)
        assert result.exit_code == 0
        # The rich console should produce styled output
        assert len(result.stdout) > 20  # More than just plain text
    
    def test_progress_indicators(self):
        """Test that long-running operations show progress"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["init", "progress_test"])
            
            # Should complete successfully and show progress-related text
            assert result.exit_code == 0
            assert "Creating" in result.stdout or "Copying" in result.stdout
    
    def test_helpful_error_messages(self):
        """Test that error messages are helpful"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Try to run dev without config
            result = runner.invoke(app, ["dev"])
            
            assert result.exit_code == 1
            assert "Run 'sbdk init' first" in result.stdout


class TestPackaging:
    """Test CLI packaging and distribution"""
    
    def test_module_imports(self):
        """Test that all required modules can be imported"""
        try:
            import typer
            import rich
            import fastapi
            import duckdb
            import pandas
            import faker
        except ImportError as e:
            pytest.fail(f"Required dependency not available: {e}")
    
    def test_entry_point_callable(self):
        """Test that main entry point is callable"""
        from main import app
        assert callable(app)
    
    def test_cli_modules_structure(self):
        """Test CLI module structure is correct"""
        from cli import init, dev, start, webhooks
        
        # Check that modules have expected functions
        assert hasattr(init, 'cli_init')
        assert hasattr(dev, 'cli_dev')
        assert hasattr(start, 'cli_start')
        assert hasattr(webhooks, 'cli_webhooks')


# Performance and Load Testing
class TestPerformance:
    """Test CLI performance characteristics"""
    
    def test_startup_time(self):
        """Test CLI startup time is reasonable"""
        import time
        
        start_time = time.time()
        result = runner.invoke(app, ["--help"])
        end_time = time.time()
        
        startup_time = end_time - start_time
        assert startup_time < 2.0  # Should start in under 2 seconds
        assert result.exit_code == 0
    
    def test_config_loading_performance(self):
        """Test config loading performance with large configs"""
        import time
        
        # Create a reasonably large config file
        large_config = {
            "project": "perf_test",
            "target": "dev",
            "duckdb_path": "data/perf_test.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt",
            "large_data": ["item"] * 1000  # Add some bulk
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_config, f)
            f.flush()
            
            start_time = time.time()
            config = load_config(f.name)
            end_time = time.time()
            
            load_time = end_time - start_time
            assert load_time < 0.5  # Should load in under 500ms
            assert config["project"] == "perf_test"
            
            os.unlink(f.name)


# Security Testing
class TestSecurity:
    """Test security aspects of the CLI"""
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Try to create project with path traversal
            result = runner.invoke(app, ["init", "../../../malicious_project"])
            
            # Should create locally, not traverse paths
            assert result.exit_code == 0
            malicious_path = Path("../../../malicious_project")
            local_malicious = Path("../../../malicious_project")
            
            # Check that it doesn't write outside the intended area
            assert not (Path(temp_dir).parent.parent.parent / "malicious_project").exists()
    
    def test_config_injection_prevention(self):
        """Test prevention of config injection attacks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create config with potentially malicious content
            malicious_config = {
                "project": "test",
                "duckdb_path": "data/test.duckdb",
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt",
                "malicious_script": "$(rm -rf /)"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(malicious_config, f)
            
            # Config should load without executing the malicious content
            config = load_config()
            assert config["malicious_script"] == "$(rm -rf /)"  # Should be treated as string


if __name__ == "__main__":
    # Run all tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])