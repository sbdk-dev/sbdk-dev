"""
Interactive CLI Flow Tests for SBDK.dev
Tests user interaction flows, prompts, and real-world usage scenarios
"""
import pytest
import tempfile
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading
import signal

# Import CLI modules
from sbdk.cli.main import app
from sbdk.cli.commands.run import cli_run, PipelineFileHandler
from sbdk.cli.commands.webhooks import cli_webhooks
from typer.testing import CliRunner

runner = CliRunner()


class TestInteractiveWorkflows:
    """Test interactive user workflows"""
    
    def test_new_user_complete_workflow(self):
        """Test complete workflow for a new user"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Step 1: User runs init
            result = runner.invoke(app, ["init", "my_first_project"])
            assert result.exit_code == 0
            assert "Successfully initialized" in result.stdout
            
            # Step 2: User navigates to project
            project_path = Path("my_first_project")
            assert project_path.exists()
            os.chdir(project_path)
            
            # Step 3: User checks what's available
            result = runner.invoke(app, ["--help"])
            assert result.exit_code == 0
            assert "dev" in result.stdout
            assert "start" in result.stdout
            assert "webhooks" in result.stdout
            
            # Step 4: User tries dev command
            with patch('sbdk.cli.commands.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                assert result.exit_code == 0
    
    def test_help_discovery_workflow(self):
        """Test user discovering functionality through help"""
        # Main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "dev" in result.stdout
        assert "start" in result.stdout
        assert "webhooks" in result.stdout
        
        # Command-specific help
        commands = ["init", "dev", "start", "webhooks", "version"]
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert len(result.stdout) > 50  # Should have substantial help text
    
    def test_error_recovery_workflow(self):
        """Test user error recovery scenarios"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # User tries dev without init
            result = runner.invoke(app, ["dev"])
            assert result.exit_code == 1
            assert "Config file not found" in result.stdout
            assert "sbdk init" in result.stdout  # Helpful suggestion
            
            # User follows suggestion and runs init
            result = runner.invoke(app, ["init", "recovery_test"])
            assert result.exit_code == 0
            
            # Now dev should work (with mocking)
            os.chdir("recovery_test")
            with patch('sbdk.cli.commands.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                assert result.exit_code == 0


class TestRealTimeInteraction:
    """Test real-time interactive features"""
    
    def test_file_watcher_simulation(self):
        """Test file watching functionality"""
        handler = PipelineFileHandler({"project": "test", "duckdb_path": "test.db"}, visual=False)  # Updated for new class
        
        # Simulate file change events
        class MockEvent:
            def __init__(self, path, is_directory=False):
                self.src_path = path
                self.is_directory = is_directory
        
        # Test Python file triggers rebuild
        with patch('sbdk.cli.commands.run.execute_pipeline') as mock_run:
            event = MockEvent("pipelines/users.py")
            handler.on_modified(event)
            mock_dev.assert_called_once()
        
        # Test non-relevant file doesn't trigger
        handler.last_triggered = 0  # Reset debounce
        with patch('sbdk.cli.commands.run.execute_pipeline') as mock_run:
            event = MockEvent("README.txt")
            handler.on_modified(event)
            mock_dev.assert_not_called()
    
    def test_development_server_lifecycle(self):
        """Test development server start/stop lifecycle"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Initialize project first
            result = runner.invoke(app, ["init", "server_test"])
            assert result.exit_code == 0
            
            os.chdir("server_test")
            
            # Test server startup checks
            # Note: We can't easily test the full server due to infinite loop
            # But we can test the setup validation
            
            # Mock the observer and test setup
            with patch('watchdog.observers.Observer') as mock_observer, \
                 patch('sbdk.cli.commands.run.execute_pipeline'):
                
                mock_observer_instance = MagicMock()
                mock_observer.return_value = mock_observer_instance
                
                # This would normally run forever, so we'll patch time.sleep
                with patch('time.sleep', side_effect=KeyboardInterrupt):
                    try:
                        result = runner.invoke(app, ["start", "--no-initial-run"])
                    except SystemExit:
                        pass  # Expected due to KeyboardInterrupt
                
                # Verify observer was set up correctly
                mock_observer_instance.schedule.assert_called()
                mock_observer_instance.start.assert_called()


class TestUserExperienceFlows:
    """Test user experience and usability"""
    
    def test_progress_indicators_visible(self):
        """Test that progress indicators are shown to users"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["init", "progress_test"])
            
            # Should show progress or completion messages
            output = result.stdout
            progress_indicators = [
                "Creating", "Copying", "Setting up", "Configuring", 
                "✅", "Successfully", "complete"
            ]
            
            has_progress = any(indicator in output for indicator in progress_indicators)
            assert has_progress, f"No progress indicators found in: {output}"
    
    def test_colorful_rich_output(self):
        """Test that output uses Rich formatting"""
        result = runner.invoke(app, ["version"])
        
        # Rich console should produce more output than plain text
        assert result.exit_code == 0
        assert len(result.stdout) > 15  # More than just "v1.0.0"
        
        # Test help output is formatted
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "SBDK.dev" in result.stdout
        # Rich help should be substantial
        assert len(result.stdout) > 200
    
    def test_helpful_next_steps(self):
        """Test that commands provide helpful next steps"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["init", "nextsteps_test"])
            assert result.exit_code == 0
            
            output = result.stdout
            next_step_indicators = [
                "Next steps", "cd ", "python", "pip install", "dev"
            ]
            
            has_next_steps = any(step in output for step in next_step_indicators)
            assert has_next_steps, f"No next steps found in: {output}"
    
    def test_error_message_quality(self):
        """Test that error messages are helpful and actionable"""
        # Test missing config error
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(app, ["dev"])
            assert result.exit_code == 1
            
            error_output = result.stdout
            helpful_elements = [
                "not found", "init", "first", "sbdk"
            ]
            
            has_helpful_error = any(element in error_output for element in helpful_elements)
            assert has_helpful_error, f"Error not helpful: {error_output}"
        
        # Test directory exists error
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create directory first
            os.mkdir("existing_project")
            
            result = runner.invoke(app, ["init", "existing_project"])
            assert result.exit_code == 1
            assert "already exists" in result.stdout
            assert "--force" in result.stdout  # Suggests solution


class TestLongRunningOperations:
    """Test long-running operations and user feedback"""
    
    def test_pipeline_execution_feedback(self):
        """Test feedback during pipeline execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create config
            import json
            config = {
                "project": "feedback_test",
                "duckdb_path": "data/test.duckdb",
                "dbt_path": "./dbt",
                "profiles_dir": "~/.dbt"
            }
            
            with open("sbdk_config.json", "w") as f:
                json.dump(config, f)
            
            # Mock pipeline with delay to simulate long operation
            def slow_pipeline(*args, **kwargs):
                time.sleep(0.1)  # Small delay
                return MagicMock(stdout="Pipeline completed", stderr="")
            
            with patch('subprocess.run', side_effect=slow_pipeline):
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                
            assert result.exit_code == 0
            # Should show progress or status updates
            assert "Running" in result.stdout or "Pipeline" in result.stdout
    
    def test_cancellation_handling(self):
        """Test graceful handling of user cancellation"""
        # This is difficult to test directly with CliRunner
        # But we can test that KeyboardInterrupt is handled
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Initialize project
            result = runner.invoke(app, ["init", "cancel_test"])
            assert result.exit_code == 0
            
            os.chdir("cancel_test")
            
            # Test that start command handles interruption
            with patch('time.sleep', side_effect=KeyboardInterrupt), \
                 patch('watchdog.observers.Observer'), \
                 patch('sbdk.cli.commands.run.execute_pipeline'):
                
                try:
                    result = runner.invoke(app, ["start", "--no-initial-run"])
                    # Should exit gracefully
                    assert "Stopping" in result.stdout or result.exit_code != 0
                except SystemExit:
                    pass  # Expected


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_data_scientist_workflow(self):
        """Test typical data scientist workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Data scientist creates new project
            result = runner.invoke(app, ["init", "data_analysis"])
            assert result.exit_code == 0
            
            os.chdir("data_analysis")
            
            # Checks project structure
            assert Path("pipelines").exists()
            assert Path("dbt").exists()
            assert Path("dbt/models").exists()
            
            # Runs initial data pipeline
            with patch('sbdk.cli.commands.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev"])
                assert result.exit_code == 0
            
            # Starts development server for iterative work
            with patch('watchdog.observers.Observer'), \
                 patch('time.sleep', side_effect=KeyboardInterrupt):
                try:
                    result = runner.invoke(app, ["start"])
                except SystemExit:
                    pass  # Expected due to interrupt
    
    def test_team_collaboration_workflow(self):
        """Test team collaboration scenario"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Team member clones/receives project
            result = runner.invoke(app, ["init", "team_project"])
            assert result.exit_code == 0
            
            os.chdir("team_project")
            
            # Checks configuration
            with open("sbdk_config.json") as f:
                import json
                config = json.load(f)
                assert config["project"] == "team_project"
            
            # Runs existing pipelines
            with patch('sbdk.cli.commands.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev", "--pipelines-only"])
                assert result.exit_code == 0
            
            # Sets up webhook server for integration
            with patch('subprocess.run') as mock_run:
                # Create webhook server file
                os.makedirs("fastapi_server", exist_ok=True)
                Path("fastapi_server/webhook_listener.py").touch()
                
                mock_run.return_value = None
                result = runner.invoke(app, ["webhooks", "--port", "8080"])
                
                # Should attempt to start server
                mock_run.assert_called()
    
    def test_production_deployment_prep(self):
        """Test preparing for production deployment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Create production-ready project
            result = runner.invoke(app, ["init", "prod_ready"])
            assert result.exit_code == 0
            
            os.chdir("prod_ready")
            
            # Verify all components exist
            required_components = [
                "pipelines", "dbt", "fastapi_server", 
                "sbdk_config.json", "data"
            ]
            
            for component in required_components:
                assert Path(component).exists(), f"Missing component: {component}"
            
            # Test configuration is valid
            with open("sbdk_config.json") as f:
                import json
                config = json.load(f)
                assert all(key in config for key in [
                    "project", "duckdb_path", "dbt_path", "profiles_dir"
                ])
            
            # Test that pipeline can run
            with patch('sbdk.cli.commands.dev.run_pipeline_module'), \
                 patch('subprocess.run'):
                result = runner.invoke(app, ["dev"])
                assert result.exit_code == 0


class TestAccessibilityAndUsability:
    """Test accessibility and usability features"""
    
    def test_command_discoverability(self):
        """Test that users can discover commands easily"""
        # Main help should list all commands
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        
        commands = ["init", "dev", "start", "webhooks", "version"]
        for cmd in commands:
            assert cmd in result.stdout
        
        # Should have emojis or icons for visual appeal
        visual_elements = ["🚀", "🔧", "🏗️", "🔗"]
        has_visual = any(element in result.stdout for element in visual_elements)
        assert has_visual, "Help should have visual elements"
    
    def test_command_consistency(self):
        """Test that commands follow consistent patterns"""
        commands_with_help = ["init", "dev", "start", "webhooks"]
        
        for cmd in commands_with_help:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert len(result.stdout) > 50  # Substantial help
            
            # Should have consistent help format
            help_patterns = ["Usage:", "Options:", "help"]
            has_patterns = any(pattern in result.stdout for pattern in help_patterns)
            assert has_patterns, f"Inconsistent help format for {cmd}"
    
    def test_feedback_timing(self):
        """Test that feedback is provided at appropriate times"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Immediate feedback for quick operations
            start_time = time.time()
            result = runner.invoke(app, ["--help"])
            end_time = time.time()
            
            assert result.exit_code == 0
            assert (end_time - start_time) < 2.0  # Should be fast
            
            # Progress feedback for longer operations
            start_time = time.time()
            result = runner.invoke(app, ["init", "timing_test"])
            end_time = time.time()
            
            assert result.exit_code == 0
            if (end_time - start_time) > 1.0:  # If operation took time
                # Should have shown progress
                progress_words = ["Creating", "Copying", "Setting", "complete"]
                has_progress = any(word in result.stdout for word in progress_words)
                assert has_progress, "Long operation should show progress"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])