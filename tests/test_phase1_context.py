"""
Unit tests for Phase 1: Context Manager
Tests context lifecycle, state management, and resource cleanup
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sbdk.context import SBDKContext, create_context, get_context
from sbdk.exceptions import ConfigurationError


class MockResource:
    """Mock resource for testing cleanup"""
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class TestSBDKContextCreation:
    """Test context creation and initialization"""

    def test_create_default_context(self):
        """Test creating context with defaults"""
        ctx = SBDKContext()

        assert isinstance(ctx.project_dir, Path)
        assert ctx.project_dir.exists()
        assert ctx.config_file == "sbdk_config.json"
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.dry_run is False
        assert ctx.console is not None
        assert ctx.logger is not None

    def test_create_context_with_options(self):
        """Test creating context with custom options"""
        project_dir = Path("/tmp/test_project")
        ctx = SBDKContext(
            project_dir=project_dir,
            config_file="custom_config.json",
            verbose=True,
            quiet=False,
            dry_run=True
        )

        assert ctx.project_dir == project_dir
        assert ctx.config_file == "custom_config.json"
        assert ctx.verbose is True
        assert ctx.quiet is False
        assert ctx.dry_run is True

    def test_singleton_pattern(self):
        """Test singleton pattern for get_instance"""
        # Clear singleton
        SBDKContext._instance = None

        ctx1 = SBDKContext.get_instance()
        ctx2 = SBDKContext.get_instance()

        assert ctx1 is ctx2

    def test_create_replaces_singleton(self):
        """Test that create() replaces singleton instance"""
        ctx1 = SBDKContext.create(verbose=False)
        ctx2 = SBDKContext.create(verbose=True)

        assert ctx1 is not ctx2
        assert ctx2.verbose is True


class TestContextConfiguration:
    """Test configuration loading and management"""

    def test_load_config_success(self, tmp_path):
        """Test successful config loading"""
        config_file = tmp_path / "sbdk_config.json"
        config_data = {
            "project": "test_project",
            "duckdb_path": "data/test.duckdb",
            "pipelines_path": "./pipelines",
            "dbt_path": "./dbt",
            "profiles_dir": "~/.dbt"
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        ctx = SBDKContext(project_dir=tmp_path)
        config = ctx.load_config()

        assert config["project"] == "test_project"
        assert config["duckdb_path"] == "data/test.duckdb"

    def test_load_config_not_found(self, tmp_path):
        """Test config loading when file doesn't exist"""
        ctx = SBDKContext(project_dir=tmp_path)

        with pytest.raises(ConfigurationError) as exc_info:
            ctx.load_config()

        assert "not found" in str(exc_info.value)
        assert "sbdk init" in exc_info.value.suggestion

    def test_load_config_invalid_json(self, tmp_path):
        """Test config loading with invalid JSON"""
        config_file = tmp_path / "sbdk_config.json"

        with open(config_file, 'w') as f:
            f.write("{ invalid json }")

        ctx = SBDKContext(project_dir=tmp_path)

        with pytest.raises(ConfigurationError) as exc_info:
            ctx.load_config()

        assert "Invalid JSON" in str(exc_info.value)

    def test_config_lazy_loading(self, tmp_path):
        """Test config is lazy loaded"""
        config_file = tmp_path / "sbdk_config.json"
        config_data = {"project": "test", "duckdb_path": "data/test.duckdb"}

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        ctx = SBDKContext(project_dir=tmp_path)

        # Config should not be loaded yet
        assert ctx._config is None

        # Access config property
        config = ctx.config

        # Now it should be loaded
        assert ctx._config is not None
        assert config["project"] == "test"

    def test_save_config(self, tmp_path):
        """Test saving configuration"""
        config_file = tmp_path / "sbdk_config.json"
        config_data = {"project": "test", "duckdb_path": "data/test.duckdb"}

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        ctx = SBDKContext(project_dir=tmp_path)
        ctx.load_config()

        # Modify config
        ctx._config["project"] = "modified"
        ctx.save_config()

        # Read back
        with open(config_file) as f:
            saved_config = json.load(f)

        assert saved_config["project"] == "modified"


class TestContextState:
    """Test state management"""

    def test_get_state_default(self):
        """Test getting state with default value"""
        ctx = SBDKContext()

        value = ctx.get_state("nonexistent", default="default_value")
        assert value == "default_value"

    def test_set_and_get_state(self):
        """Test setting and getting state"""
        ctx = SBDKContext()

        ctx.set_state("key1", "value1")
        ctx.set_state("key2", 42)

        assert ctx.get_state("key1") == "value1"
        assert ctx.get_state("key2") == 42

    def test_state_isolation(self):
        """Test state is isolated per context instance"""
        ctx1 = SBDKContext()
        ctx2 = SBDKContext()

        ctx1.set_state("key", "value1")
        ctx2.set_state("key", "value2")

        assert ctx1.get_state("key") == "value1"
        assert ctx2.get_state("key") == "value2"


class TestResourceManagement:
    """Test resource registration and cleanup"""

    def test_register_resource(self):
        """Test resource registration"""
        ctx = SBDKContext()
        resource = MockResource()

        ctx.register_resource(resource)

        assert len(ctx._resources) == 1
        assert ctx._resources[0] is resource

    def test_cleanup_resources(self):
        """Test resource cleanup"""
        ctx = SBDKContext()
        resource1 = MockResource()
        resource2 = MockResource()

        ctx.register_resource(resource1)
        ctx.register_resource(resource2)

        ctx.cleanup()

        assert resource1.closed is True
        assert resource2.closed is True
        assert len(ctx._resources) == 0

    def test_cleanup_with_context_manager(self):
        """Test cleanup happens with context manager"""
        resource = MockResource()

        with SBDKContext() as ctx:
            ctx.register_resource(resource)
            assert resource.closed is False

        # After exiting context, resource should be closed
        assert resource.closed is True

    def test_cleanup_handles_errors(self):
        """Test cleanup handles resource errors gracefully"""
        ctx = SBDKContext()

        # Resource that raises on close
        bad_resource = MagicMock()
        bad_resource.close.side_effect = Exception("Close failed")

        good_resource = MockResource()

        ctx.register_resource(bad_resource)
        ctx.register_resource(good_resource)

        # Should not raise, just log warning
        ctx.cleanup()

        # Good resource should still be cleaned up
        assert good_resource.closed is True


class TestProjectVerification:
    """Test project structure verification"""

    def test_verify_project_structure_valid(self, tmp_path):
        """Test verification with valid project"""
        # Create project structure
        (tmp_path / "sbdk_config.json").write_text('{"project": "test", "duckdb_path": "data/test.duckdb"}')
        (tmp_path / "pipelines").mkdir()
        (tmp_path / "dbt").mkdir()
        (tmp_path / "data").mkdir()

        ctx = SBDKContext(project_dir=tmp_path)

        assert ctx.verify_project_structure() is True

    def test_verify_project_structure_no_config(self, tmp_path):
        """Test verification without config file"""
        ctx = SBDKContext(project_dir=tmp_path)

        from sbdk.exceptions import ProjectNotFoundError
        with pytest.raises(ProjectNotFoundError):
            ctx.verify_project_structure()

    def test_verify_project_structure_missing_dirs(self, tmp_path):
        """Test verification with missing directories (should warn but pass)"""
        (tmp_path / "sbdk_config.json").write_text('{"project": "test", "duckdb_path": "data/test.duckdb"}')

        ctx = SBDKContext(project_dir=tmp_path)

        # Should return True but log warnings
        result = ctx.verify_project_structure()
        assert result is True


class TestLoggingSetup:
    """Test logging configuration"""

    def test_logging_level_verbose(self):
        """Test logging level in verbose mode"""
        import logging

        ctx = SBDKContext(verbose=True)

        assert ctx.logger.level == logging.DEBUG

    def test_logging_level_quiet(self):
        """Test logging level in quiet mode"""
        import logging

        ctx = SBDKContext(quiet=True)

        assert ctx.logger.level == logging.ERROR

    def test_logging_level_normal(self):
        """Test logging level in normal mode"""
        import logging

        ctx = SBDKContext(verbose=False, quiet=False)

        assert ctx.logger.level == logging.INFO

    def test_logging_to_file(self, tmp_path):
        """Test logging to file is set up when project exists"""
        (tmp_path / "sbdk_config.json").write_text('{"project": "test", "duckdb_path": "data/test.duckdb"}')

        ctx = SBDKContext(project_dir=tmp_path)

        log_file = tmp_path / ".sbdk" / "logs" / "sbdk.log"

        # Log something
        ctx.logger.info("Test message")

        # Check log file was created
        assert log_file.exists()


class TestGlobalContextFunctions:
    """Test global context accessor functions"""

    def test_get_context(self):
        """Test get_context function"""
        # Clear singleton
        SBDKContext._instance = None

        ctx1 = get_context()
        ctx2 = get_context()

        assert ctx1 is ctx2
        assert isinstance(ctx1, SBDKContext)

    def test_create_context_function(self):
        """Test create_context function"""
        ctx = create_context(verbose=True, dry_run=True)

        assert isinstance(ctx, SBDKContext)
        assert ctx.verbose is True
        assert ctx.dry_run is True

    def test_create_context_replaces_global(self):
        """Test create_context replaces global instance"""
        ctx1 = create_context(verbose=False)
        ctx2 = create_context(verbose=True)

        assert get_context() is ctx2
        assert ctx2.verbose is True


class TestConsoleSetup:
    """Test Rich console configuration"""

    def test_console_quiet_mode(self):
        """Test console in quiet mode"""
        ctx = SBDKContext(quiet=True)

        assert ctx.console.quiet is True

    def test_console_normal_mode(self):
        """Test console in normal mode"""
        ctx = SBDKContext(quiet=False)

        assert ctx.console.quiet is False
