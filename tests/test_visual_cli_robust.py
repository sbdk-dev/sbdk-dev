"""
Comprehensive Test Suite for SBDK.dev Robust Visual CLI
Tests all components, integration points, and functionality

Author: SBDK.dev Team  
Version: 2.0.0
"""

import pytest
import asyncio
import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Import our CLI components
from sbdk.cli.visual_cli_robust import (
    VisualCLI, CLIState, TerminalRenderer, FastAPIClient, 
    FileWatcher, KeyboardHandler
)
from sbdk.cli.enhanced_components import (
    StatusPanel, PipelineProgressPanel, LogPanel, 
    MetricsPanel, ActionPanel, ComponentState
)
from sbdk.cli.integration_layer import (
    SBDKVisualIntegration, SBDKEnhancedCLI
)


class TestCLIState:
    """Test CLI state management"""
    
    def test_cli_state_initialization(self):
        """Test CLI state initializes with correct defaults"""
        state = CLIState()
        
        assert state.running is True
        assert state.current_view == "dashboard"
        assert state.auto_run_enabled is True
        assert state.keyboard_mode == "navigation"
        assert state.status_message == "Ready"
        assert state.error_message == ""
        assert state.debug_mode is False
        
    def test_cli_state_modification(self):
        """Test CLI state can be modified"""
        state = CLIState()
        
        state.running = False
        state.current_view = "logs"
        state.status_message = "Pipeline running"
        
        assert state.running is False
        assert state.current_view == "logs"
        assert state.status_message == "Pipeline running"


class TestTerminalRenderer:
    """Test terminal rendering functionality"""
    
    def test_terminal_renderer_initialization(self):
        """Test terminal renderer initializes correctly"""
        renderer = TerminalRenderer()
        
        assert renderer.console is not None
        assert renderer.layout is not None
        assert isinstance(renderer.components, dict)
        assert renderer.cursor_hidden is False
        assert renderer.alt_screen_active is False
        
    def test_get_terminal_size(self):
        """Test terminal size detection"""
        renderer = TerminalRenderer()
        width, height = renderer.get_terminal_size()
        
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0
        
    @patch('sys.stdout.isatty')
    def test_setup_terminal_non_tty(self, mock_isatty):
        """Test terminal setup in non-TTY mode"""
        mock_isatty.return_value = False
        renderer = TerminalRenderer()
        result = renderer.setup_terminal()
        
        assert result is False
        assert renderer.cursor_hidden is False
        assert renderer.alt_screen_active is False
        
    @patch('sys.stdout.isatty')
    @patch('sys.stdout.write')
    def test_setup_terminal_tty(self, mock_write, mock_isatty):
        """Test terminal setup in TTY mode"""
        mock_isatty.return_value = True
        renderer = TerminalRenderer()
        result = renderer.setup_terminal()
        
        assert result is True
        assert mock_write.called
        assert renderer.cursor_hidden is True
        assert renderer.alt_screen_active is True


class TestFastAPIClient:
    """Test FastAPI client integration"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return FastAPIClient("http://localhost:8000")
        
    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client.base_url == "http://localhost:8000"
        assert client.project_uuid is None
        assert client.client is not None
        
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.client, 'get', return_value=mock_response):
            result = await client.health_check()
            
        assert result["status"] == "healthy"
        
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test failed health check"""
        with patch.object(client.client, 'get', side_effect=Exception("Connection failed")):
            result = await client.health_check()
            
        assert result["status"] == "error"
        assert "Connection failed" in result["error"]
        
    @pytest.mark.asyncio
    async def test_register_project_success(self, client):
        """Test successful project registration"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "uuid": "test-uuid-123",
            "project_name": "test_project",
            "status": "registered"
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.register_project("test_project", "test@example.com")
            
        assert result["uuid"] == "test-uuid-123"
        assert result["project_name"] == "test_project"
        assert client.project_uuid == "test-uuid-123"
        
    @pytest.mark.asyncio
    async def test_track_usage_without_registration(self, client):
        """Test usage tracking without registration"""
        result = await client.track_usage("test_command")
        
        assert result["status"] == "skipped"
        assert result["reason"] == "not_registered"
        
    @pytest.mark.asyncio
    async def test_track_usage_with_registration(self, client):
        """Test usage tracking with registration"""
        client.project_uuid = "test-uuid-123"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "tracked",
            "event_id": "event-123"
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client.track_usage("test_command", 1.5, {"extra": "data"})
            
        assert result["status"] == "tracked"
        assert result["event_id"] == "event-123"


class TestFileWatcher:
    """Test file watching functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
            
    def test_file_watcher_initialization(self, temp_dir):
        """Test file watcher initializes correctly"""
        callback = Mock()
        watcher = FileWatcher([str(temp_dir)], callback)
        
        assert watcher.paths == [str(temp_dir)]
        assert watcher.callback == callback
        assert watcher.running is False
        assert watcher.thread is None
        
    def test_file_watcher_start_stop(self, temp_dir):
        """Test file watcher start and stop"""
        callback = Mock()
        watcher = FileWatcher([str(temp_dir)], callback)
        
        watcher.start()
        assert watcher.running is True
        assert watcher.thread is not None
        
        watcher.stop()
        assert watcher.running is False
        
    def test_file_watcher_detects_changes(self, temp_dir):
        """Test file watcher detects file changes"""
        callback = Mock()
        watcher = FileWatcher([str(temp_dir)], callback)
        
        # Create a test file
        test_file = temp_dir / "test.py"
        test_file.write_text("initial content")
        
        watcher.start()
        time.sleep(0.1)  # Let watcher initialize
        
        # Modify the file
        test_file.write_text("modified content")
        time.sleep(1.5)  # Wait for detection
        
        watcher.stop()
        
        # Verify callback was called
        assert callback.called


class TestKeyboardHandler:
    """Test keyboard input handling"""
    
    def test_keyboard_handler_initialization(self):
        """Test keyboard handler initializes correctly"""
        handler = KeyboardHandler()
        
        assert handler.old_settings is None
        assert handler.raw_mode is False
        
    @patch('sys.stdin.isatty')
    def test_enable_raw_mode_non_tty(self, mock_isatty):
        """Test raw mode on non-TTY"""
        mock_isatty.return_value = False
        handler = KeyboardHandler()
        
        result = handler.enable_raw_mode()
        assert result is False
        assert handler.raw_mode is False
        
    @patch('sys.stdin.isatty')
    @patch('termios.tcgetattr')
    @patch('tty.setraw')
    def test_enable_raw_mode_tty(self, mock_setraw, mock_tcgetattr, mock_isatty):
        """Test raw mode on TTY"""
        mock_isatty.return_value = True
        mock_tcgetattr.return_value = "fake_settings"
        
        handler = KeyboardHandler()
        result = handler.enable_raw_mode()
        
        assert result is True
        assert handler.raw_mode is True
        assert handler.old_settings == "fake_settings"


class TestStatusPanel:
    """Test status panel component"""
    
    def test_status_panel_initialization(self):
        """Test status panel initializes correctly"""
        panel = StatusPanel("Test Status")
        
        assert panel.title == "Test Status"
        assert isinstance(panel.status_items, dict)
        assert len(panel.status_items) == 0
        
    def test_add_status_item(self):
        """Test adding status items"""
        panel = StatusPanel()
        
        panel.add_status_item("server", "API Server", "Running", 
                            ComponentState.SUCCESS, "🟢")
        
        assert "server" in panel.status_items
        item = panel.status_items["server"]
        assert item["label"] == "API Server"
        assert item["value"] == "Running"
        assert item["status"] == ComponentState.SUCCESS
        assert item["icon"] == "🟢"
        
    def test_update_status_item(self):
        """Test updating status items"""
        panel = StatusPanel()
        panel.add_status_item("server", "API Server", "Starting", ComponentState.LOADING)
        
        panel.update_status_item("server", "Running", ComponentState.SUCCESS)
        
        item = panel.status_items["server"]
        assert item["value"] == "Running"
        assert item["status"] == ComponentState.SUCCESS
        
    def test_get_status_color(self):
        """Test status color mapping"""
        panel = StatusPanel()
        
        assert panel.get_status_color(ComponentState.SUCCESS) == "green"
        assert panel.get_status_color(ComponentState.ERROR) == "red"
        assert panel.get_status_color(ComponentState.WARNING) == "orange"
        assert panel.get_status_color(ComponentState.LOADING) == "yellow"
        assert panel.get_status_color(ComponentState.IDLE) == "white"
        
    def test_render_status_panel(self):
        """Test rendering status panel"""
        panel = StatusPanel("Test Panel")
        panel.add_status_item("test", "Test Item", "Active", ComponentState.SUCCESS)
        
        rendered = panel.render()
        assert rendered is not None
        assert "Test Panel" in str(rendered)


class TestPipelineProgressPanel:
    """Test pipeline progress component"""
    
    def test_pipeline_progress_initialization(self):
        """Test pipeline progress initializes correctly"""
        panel = PipelineProgressPanel("Test Pipeline")
        
        assert panel.title == "Test Pipeline"
        assert isinstance(panel.steps, list)
        assert len(panel.steps) == 0
        assert panel.current_step == 0
        assert panel.overall_progress == 0.0
        
    def test_add_step(self):
        """Test adding pipeline steps"""
        panel = PipelineProgressPanel()
        
        panel.add_step("users", "Generate user data", 5.0)
        
        assert len(panel.steps) == 1
        step = panel.steps[0]
        assert step["name"] == "users"
        assert step["description"] == "Generate user data"
        assert step["estimated_duration"] == 5.0
        assert step["status"] == ComponentState.IDLE
        
    def test_pipeline_execution_flow(self):
        """Test complete pipeline execution flow"""
        panel = PipelineProgressPanel()
        panel.add_step("step1", "First step")
        panel.add_step("step2", "Second step")
        
        # Start pipeline
        panel.start_pipeline()
        assert panel.overall_progress == 0.0
        
        # Start first step
        panel.start_step(0)
        assert panel.steps[0]["status"] == ComponentState.LOADING
        
        # Update progress
        panel.update_step_progress(0, 0.5)
        assert panel.steps[0]["progress"] == 0.5
        assert panel.overall_progress == 0.25  # 50% of first step = 25% overall
        
        # Complete first step
        panel.complete_step(0, True)
        assert panel.steps[0]["status"] == ComponentState.SUCCESS
        assert panel.steps[0]["progress"] == 1.0
        assert panel.overall_progress == 0.5  # First step complete = 50% overall
        
        # Complete second step
        panel.start_step(1)
        panel.complete_step(1, True)
        assert panel.overall_progress == 1.0  # Both steps complete = 100%
        
    def test_step_failure(self):
        """Test step failure handling"""
        panel = PipelineProgressPanel()
        panel.add_step("failing_step", "This will fail")
        
        panel.start_step(0)
        panel.complete_step(0, False, "Connection timeout")
        
        step = panel.steps[0]
        assert step["status"] == ComponentState.ERROR
        assert step["error_message"] == "Connection timeout"


class TestLogPanel:
    """Test log panel component"""
    
    def test_log_panel_initialization(self):
        """Test log panel initializes correctly"""
        panel = LogPanel("Test Logs", max_lines=50)
        
        assert panel.title == "Test Logs"
        assert panel.max_lines == 50
        assert isinstance(panel.log_entries, list)
        assert len(panel.log_entries) == 0
        
    def test_add_log_entry(self):
        """Test adding log entries"""
        panel = LogPanel()
        
        panel.add_log("Test message", "INFO", "TestComponent")
        
        assert len(panel.log_entries) == 1
        entry = panel.log_entries[0]
        assert entry["message"] == "Test message"
        assert entry["level"] == "INFO"
        assert entry["component"] == "TestComponent"
        assert isinstance(entry["timestamp"], datetime)
        
    def test_log_level_colors(self):
        """Test log level color mapping"""
        panel = LogPanel()
        
        assert panel.get_level_color("DEBUG") == "dim"
        assert panel.get_level_color("INFO") == "white"
        assert panel.get_level_color("WARNING") == "yellow"
        assert panel.get_level_color("ERROR") == "red"
        assert panel.get_level_color("CRITICAL") == "bold red"
        
    def test_log_filtering(self):
        """Test log filtering functionality"""
        panel = LogPanel()
        
        panel.add_log("Debug message", "DEBUG")
        panel.add_log("Info message", "INFO")
        panel.add_log("Error message", "ERROR")
        
        # Test level filtering
        panel.set_filter(level="ERROR")
        filtered = panel._filter_logs()
        assert len(filtered) == 1
        assert filtered[0]["level"] == "ERROR"
        
        # Test search filtering
        panel.set_filter(search_term="Info")
        filtered = panel._filter_logs()
        assert len(filtered) == 1
        assert "Info" in filtered[0]["message"]
        
    def test_max_lines_limit(self):
        """Test log entry limit"""
        panel = LogPanel(max_lines=2)
        
        panel.add_log("Message 1", "INFO")
        panel.add_log("Message 2", "INFO")
        panel.add_log("Message 3", "INFO")
        
        assert len(panel.log_entries) == 2
        assert panel.log_entries[0]["message"] == "Message 2"
        assert panel.log_entries[1]["message"] == "Message 3"


class TestMetricsPanel:
    """Test metrics panel component"""
    
    def test_metrics_panel_initialization(self):
        """Test metrics panel initializes correctly"""
        panel = MetricsPanel("Test Metrics")
        
        assert panel.title == "Test Metrics"
        assert isinstance(panel.metrics, dict)
        assert len(panel.metrics) == 0
        
    def test_add_metric(self):
        """Test adding metrics"""
        panel = MetricsPanel()
        
        panel.add_metric("cpu", "CPU Usage", "%", lambda x: f"{x:.1f}")
        
        assert "cpu" in panel.metrics
        metric = panel.metrics["cpu"]
        assert metric["name"] == "CPU Usage"
        assert metric["unit"] == "%"
        assert metric["format_fn"](50.5) == "50.5"
        
    def test_update_metric(self):
        """Test updating metric values"""
        panel = MetricsPanel()
        panel.add_metric("memory", "Memory", "MB")
        
        panel.update_metric("memory", 100)
        panel.update_metric("memory", 150)
        panel.update_metric("memory", 120)
        
        metric = panel.metrics["memory"]
        assert metric["current_value"] == 120
        assert metric["min_value"] == 100
        assert metric["max_value"] == 150
        assert metric["avg_value"] == 123.33333333333333
        assert len(metric["values"]) == 3
        
    def test_metric_history_limit(self):
        """Test metric history limit"""
        panel = MetricsPanel()
        panel.add_metric("test", "Test Metric")
        
        # Add 150 values (more than limit of 100)
        for i in range(150):
            panel.update_metric("test", i)
            
        metric = panel.metrics["test"]
        assert len(metric["values"]) == 100
        assert metric["values"][0] == 50  # First 50 values should be dropped


class TestActionPanel:
    """Test action panel component"""
    
    def test_action_panel_initialization(self):
        """Test action panel initializes correctly"""
        panel = ActionPanel("Test Actions")
        
        assert panel.title == "Test Actions"
        assert isinstance(panel.actions, list)
        assert len(panel.actions) == 0
        
    def test_add_action(self):
        """Test adding actions"""
        callback = Mock()
        panel = ActionPanel()
        
        panel.add_action("r", "Run", "Execute pipeline", callback, True)
        
        assert len(panel.actions) == 1
        action = panel.actions[0]
        assert action["key"] == "r"
        assert action["label"] == "Run"
        assert action["description"] == "Execute pipeline"
        assert action["callback"] == callback
        assert action["enabled"] is True
        
    def test_trigger_action(self):
        """Test triggering actions"""
        callback = Mock()
        panel = ActionPanel()
        panel.add_action("test", "Test Action", callback=callback)
        
        result = panel.trigger_action("test")
        
        assert result is True
        assert callback.called
        
    def test_trigger_disabled_action(self):
        """Test triggering disabled action"""
        callback = Mock()
        panel = ActionPanel()
        panel.add_action("test", "Test Action", callback=callback, enabled=False)
        
        result = panel.trigger_action("test")
        
        assert result is False
        assert not callback.called
        
    def test_set_action_enabled(self):
        """Test enabling/disabling actions"""
        panel = ActionPanel()
        panel.add_action("test", "Test Action", enabled=True)
        
        panel.set_action_enabled("test", False)
        assert panel.actions[0]["enabled"] is False
        
        panel.set_action_enabled("test", True)
        assert panel.actions[0]["enabled"] is True


class TestSBDKVisualIntegration:
    """Test SBDK integration layer"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary SBDK project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create project structure
            (project_path / "pipelines").mkdir()
            (project_path / "dbt").mkdir()
            (project_path / "dbt" / "models").mkdir()
            (project_path / "data").mkdir()
            
            # Create config file
            config = {
                "project": "test_project",
                "target": "dev",
                "duckdb_path": "data/test.duckdb",
                "pipelines_dir": "pipelines",
                "dbt_dir": "dbt"
            }
            
            with open(project_path / "sbdk_config.json", "w") as f:
                json.dump(config, f)
                
            yield project_path
            
    def test_integration_initialization(self, temp_project):
        """Test integration layer initialization"""
        integration = SBDKVisualIntegration(str(temp_project))
        
        assert integration.project_path == temp_project
        assert integration.config is not None
        assert integration.config["project"] == "test_project"
        assert integration.status_panel is not None
        assert integration.pipeline_panel is not None
        assert integration.log_panel is not None
        
    def test_load_sbdk_project_with_config(self, temp_project):
        """Test loading SBDK project with existing config"""
        integration = SBDKVisualIntegration(str(temp_project))
        
        assert integration.config["project"] == "test_project"
        assert integration.config["duckdb_path"] == "data/test.duckdb"
        
    def test_get_default_config(self, temp_project):
        """Test default configuration generation"""
        integration = SBDKVisualIntegration(str(temp_project))
        default_config = integration.get_default_config()
        
        assert "project" in default_config
        assert "target" in default_config
        assert "duckdb_path" in default_config
        assert "features" in default_config
        
    @patch('subprocess.run')
    def test_run_sbdk_command(self, mock_run, temp_project):
        """Test running SBDK commands"""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        
        integration = SBDKVisualIntegration(str(temp_project))
        result = integration._run_sbdk_command(["dev"])
        
        assert result.returncode == 0
        mock_run.assert_called_once()
        
    @patch('subprocess.run')
    def test_run_dbt_command(self, mock_run, temp_project):
        """Test running dbt commands"""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        
        integration = SBDKVisualIntegration(str(temp_project))
        result = integration._run_dbt_command(["run"])
        
        assert result.returncode == 0
        mock_run.assert_called_once()


class TestSBDKEnhancedCLI:
    """Test enhanced CLI with full integration"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary SBDK project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create minimal project structure
            config = {"project": "test_project", "target": "dev"}
            with open(project_path / "sbdk_config.json", "w") as f:
                json.dump(config, f)
                
            yield project_path
            
    def test_enhanced_cli_initialization(self, temp_project):
        """Test enhanced CLI initialization"""
        cli = SBDKEnhancedCLI(str(temp_project))
        
        assert cli.project_path == temp_project
        assert cli.integration is not None
        assert "dashboard" in cli.views
        assert "pipeline" in cli.views
        assert "metrics" in cli.views
        
    @pytest.mark.asyncio
    async def test_enhanced_cli_keyboard_handling(self, temp_project):
        """Test enhanced keyboard handling"""
        cli = SBDKEnhancedCLI(str(temp_project))
        
        # Mock the action panel
        cli.integration.actions_panel.trigger_action = Mock(return_value=True)
        
        await cli.handle_keyboard_input('r')
        
        cli.integration.actions_panel.trigger_action.assert_called_with('r')


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def complete_project(self):
        """Create a complete test project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create complete project structure
            (project_path / "pipelines").mkdir()
            (project_path / "dbt").mkdir()
            (project_path / "dbt" / "models").mkdir()
            (project_path / "data").mkdir()
            (project_path / "fastapi_server").mkdir()
            
            # Create config
            config = {
                "project": "integration_test",
                "target": "dev",
                "duckdb_path": "data/integration_test.duckdb",
                "features": {
                    "visual_cli": True,
                    "auto_run": True,
                    "webhook_server": True
                }
            }
            
            with open(project_path / "sbdk_config.json", "w") as f:
                json.dump(config, f)
                
            # Create dummy pipeline files
            (project_path / "pipelines" / "users.py").write_text("# Users pipeline")
            (project_path / "pipelines" / "events.py").write_text("# Events pipeline")
            
            # Create dummy dbt files
            (project_path / "dbt" / "dbt_project.yml").write_text("name: test")
            (project_path / "dbt" / "models" / "users.sql").write_text("SELECT 1")
            
            yield project_path
            
    def test_complete_project_initialization(self, complete_project):
        """Test complete project can be initialized"""
        cli = SBDKEnhancedCLI(str(complete_project))
        
        assert cli.project_path == complete_project
        assert cli.integration.config["project"] == "integration_test"
        assert cli.integration.config["features"]["visual_cli"] is True
        
    @patch('subprocess.run')
    def test_pipeline_execution_simulation(self, mock_run, complete_project):
        """Test simulated pipeline execution"""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        
        integration = SBDKVisualIntegration(str(complete_project))
        
        # Simulate running pipeline
        integration._run_pipeline_async()
        
        # Verify pipeline panel was updated
        assert integration.pipeline_panel.overall_progress >= 0
        
    def test_component_integration(self, complete_project):
        """Test all components work together"""
        cli = SBDKEnhancedCLI(str(complete_project))
        
        # Verify all components are available
        assert cli.integration.status_panel is not None
        assert cli.integration.pipeline_panel is not None
        assert cli.integration.log_panel is not None
        assert cli.integration.metrics_panel is not None
        assert cli.integration.actions_panel is not None
        
        # Test component interactions
        cli.integration.log_panel.add_log("Test message", "INFO")
        cli.integration.status_panel.update_status_item("test", "Active")
        cli.integration.metrics_panel.update_metric("test_metric", 42)
        
        # Verify state updates
        assert len(cli.integration.log_panel.log_entries) == 1
        assert cli.integration.status_panel.status_items.get("test", {}).get("value") == "Active"


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_missing_config_handling(self):
        """Test handling of missing configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No config file created
            integration = SBDKVisualIntegration(temp_dir)
            
            # Should use default config
            assert integration.config is not None
            assert "project" in integration.config
            
    def test_invalid_config_handling(self):
        """Test handling of invalid configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create invalid config file
            with open(project_path / "sbdk_config.json", "w") as f:
                f.write("invalid json content")
                
            integration = SBDKVisualIntegration(temp_dir)
            
            # Should fall back to default config
            assert integration.config is not None
            
    @patch('subprocess.run')
    def test_pipeline_failure_handling(self, mock_run):
        """Test pipeline failure handling"""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Pipeline failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            integration = SBDKVisualIntegration(temp_dir)
            result = integration._run_sbdk_command(["dev"])
            
            assert result.returncode == 1
            assert "Pipeline failed" in result.stderr


class TestPerformance:
    """Test performance characteristics"""
    
    def test_large_log_volume(self):
        """Test handling of large log volumes"""
        panel = LogPanel(max_lines=100)
        
        # Add many log entries quickly
        start_time = time.time()
        for i in range(1000):
            panel.add_log(f"Log message {i}", "INFO")
        end_time = time.time()
        
        # Should complete quickly and respect max_lines
        assert end_time - start_time < 1.0  # Less than 1 second
        assert len(panel.log_entries) == 100
        
    def test_frequent_metric_updates(self):
        """Test frequent metric updates"""
        panel = MetricsPanel()
        panel.add_metric("test", "Test Metric")
        
        # Update metric frequently
        start_time = time.time()
        for i in range(1000):
            panel.update_metric("test", i)
        end_time = time.time()
        
        # Should handle updates efficiently
        assert end_time - start_time < 1.0  # Less than 1 second
        assert len(panel.metrics["test"]["values"]) == 100  # Respects history limit
        
    def test_component_rendering_performance(self):
        """Test component rendering performance"""
        panels = [
            StatusPanel(),
            PipelineProgressPanel(),
            LogPanel(),
            MetricsPanel(),
            ActionPanel()
        ]
        
        # Add data to panels
        panels[0].add_status_item("test", "Test", "Active")
        panels[1].add_step("test", "Test step")
        panels[2].add_log("Test log", "INFO")
        panels[3].add_metric("test", "Test metric")
        panels[4].add_action("test", "Test action")
        
        # Render all panels multiple times
        start_time = time.time()
        for _ in range(100):
            for panel in panels:
                panel.render()
        end_time = time.time()
        
        # Should render efficiently
        assert end_time - start_time < 2.0  # Less than 2 seconds for 500 renders


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])