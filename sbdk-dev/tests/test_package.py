"""
Basic package tests
"""
import pytest
from pathlib import Path


def test_package_imports():
    """Test that main package imports work"""
    import sbdk
    assert sbdk.__version__ == "1.0.0"
    assert sbdk.__author__ == "SBDK.dev Team"


def test_core_imports():
    """Test that core modules import correctly"""
    from sbdk.core.config import SBDKConfig
    from sbdk.core.project import SBDKProject
    
    # Test basic instantiation
    config_data = {
        "project": "test_project",
        "duckdb_path": "data/test.duckdb"
    }
    config = SBDKConfig(**config_data)
    assert config.project == "test_project"
    assert config.target == "dev"  # default value


def test_cli_imports():
    """Test that CLI modules import correctly"""
    from sbdk.cli.main import main
    from sbdk.cli.commands.init import cli_init
    from sbdk.cli.commands.run import cli_run
    # cli_start functionality moved to cli_run --watch
    from sbdk.cli.commands.webhooks import cli_webhooks
    
    # Just test that imports work
    assert callable(main)
    assert callable(cli_init)
    assert callable(cli_run)
    # cli_start functionality moved to cli_run --watch
    assert callable(cli_webhooks)


def test_config_validation():
    """Test configuration validation"""
    from sbdk.core.config import SBDKConfig
    
    config_data = {
        "project": "test_project",
        "duckdb_path": "data/test.duckdb"
    }
    config = SBDKConfig(**config_data)
    
    # Test path resolution
    duckdb_path = config.get_duckdb_path()
    assert isinstance(duckdb_path, Path)
    
    pipelines_path = config.get_pipelines_path()
    assert isinstance(pipelines_path, Path)


def test_package_structure():
    """Test that required package files exist"""
    import sbdk
    package_root = Path(sbdk.__file__).parent
    
    # Check for required directories
    assert (package_root / "cli").exists()
    assert (package_root / "core").exists()
    assert (package_root / "templates").exists()
    
    # Check for CLI command files
    cli_commands = package_root / "cli" / "commands"
    assert (cli_commands / "init.py").exists()
    assert (cli_commands / "dev.py").exists()
    assert (cli_commands / "start.py").exists()
    assert (cli_commands / "webhooks.py").exists()
    
    # Check for template directories
    templates = package_root / "templates"
    assert (templates / "pipelines").exists()
    assert (templates / "dbt").exists()
    assert (templates / "fastapi_server").exists()