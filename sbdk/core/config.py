"""
SBDK Configuration Management

Enhanced configuration system with Pydantic validation, backward compatibility,
and integration with the new validators module.

This module provides a bridge between the legacy SBDKConfig interface and
the new comprehensive validation system in sbdk.validators.
"""

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError as PydanticValidationError

from sbdk.exceptions import ConfigurationError, SchemaValidationError
from sbdk.validators import SBDKConfig as SBDKConfigSchema


class SBDKConfig:
    """
    SBDK project configuration manager.

    Provides backward-compatible interface while using the new
    Pydantic-based validation system internally.

    This class acts as a wrapper around the SBDKConfigSchema to maintain
    compatibility with existing code while leveraging enhanced validation.
    """

    def __init__(self, config_data: dict[str, Any]):
        """
        Initialize configuration from dictionary.

        Args:
            config_data: Configuration dictionary

        Raises:
            SchemaValidationError: If configuration is invalid
        """
        try:
            self._schema = SBDKConfigSchema(**config_data)
        except PydanticValidationError as e:
            raise SchemaValidationError(e.errors()) from e

    @classmethod
    def load_from_file(cls, config_path: str = "sbdk_config.json") -> "SBDKConfig":
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            SBDKConfig instance

        Raises:
            ConfigurationError: If file not found or invalid JSON
            SchemaValidationError: If validation fails
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                suggestion="Run 'sbdk init <project-name>' to create a new project"
            )

        try:
            with open(config_file) as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}",
                suggestion="Check your sbdk_config.json for syntax errors"
            ) from e

        return cls(config_data)

    def save_to_file(self, config_path: str = "sbdk_config.json") -> None:
        """
        Save configuration to JSON file.

        Args:
            config_path: Path to save configuration

        Raises:
            ConfigurationError: If save operation fails
        """
        config_file = Path(config_path)

        try:
            with open(config_file, "w") as f:
                f.write(self._schema.to_json())
        except (IOError, OSError) as e:
            raise ConfigurationError(
                f"Failed to save configuration: {e}",
                suggestion="Check file permissions and disk space"
            ) from e

    def model_dump(self) -> dict[str, Any]:
        """
        Export configuration as dictionary (Pydantic compatibility).

        Returns:
            Configuration dictionary
        """
        return self._schema.to_dict()

    # Property accessors for backward compatibility

    @property
    def project(self) -> str:
        """Project name."""
        return self._schema.project

    @property
    def target(self) -> str:
        """Target environment."""
        return self._schema.target.value

    @property
    def duckdb_path(self) -> str:
        """DuckDB database file path."""
        return self._schema.duckdb_path

    @property
    def pipelines_path(self) -> str:
        """Pipelines directory path."""
        return str(self._schema.pipelines_path)

    @property
    def dbt_path(self) -> str:
        """dbt project directory path."""
        return str(self._schema.dbt_path)

    @property
    def profiles_dir(self) -> str:
        """dbt profiles directory path."""
        return str(self._schema.profiles_dir)

    @property
    def webhook_port(self) -> int:
        """Webhook server port."""
        return self._schema.webhooks.port if self._schema.webhooks else 8000

    @property
    def webhook_host(self) -> str:
        """Webhook server host."""
        return self._schema.webhooks.host if self._schema.webhooks else "0.0.0.0"

    @property
    def auto_reload(self) -> bool:
        """Auto-reload enabled."""
        return True  # Always enabled, controlled by command options

    @property
    def watch_paths(self) -> list[str]:
        """Paths to watch for file changes."""
        return [str(self._schema.pipelines_path), str(self._schema.dbt_path / "models")]

    # Path resolution methods

    def get_duckdb_path(self) -> Path:
        """
        Get resolved DuckDB path.

        Returns:
            Absolute path to DuckDB file
        """
        return Path(self.duckdb_path).resolve()

    def get_pipelines_path(self) -> Path:
        """
        Get resolved pipelines path.

        Returns:
            Absolute path to pipelines directory
        """
        return self._schema.pipelines_path.resolve()

    def get_dbt_path(self) -> Path:
        """
        Get resolved dbt path.

        Returns:
            Absolute path to dbt directory
        """
        return self._schema.dbt_path.resolve()

    def get_profiles_dir(self) -> Path:
        """
        Get resolved dbt profiles directory.

        Returns:
            Absolute path to dbt profiles directory
        """
        return self._schema.profiles_dir.expanduser().resolve()

    def validate_paths(self) -> dict[str, bool]:
        """
        Validate that required paths exist.

        Returns:
            Dictionary mapping path names to existence status
        """
        validation_results = {}

        paths_to_check = {
            "pipelines": self.get_pipelines_path(),
            "dbt": self.get_dbt_path(),
            "profiles_dir": self.get_profiles_dir(),
        }

        for name, path in paths_to_check.items():
            validation_results[name] = path.exists()

        # Special check for duckdb file (parent directory should exist)
        duckdb_path = self.get_duckdb_path()
        validation_results["duckdb_parent"] = duckdb_path.parent.exists()

        return validation_results

    # Access to underlying schema for advanced usage

    def get_schema(self) -> SBDKConfigSchema:
        """
        Get underlying Pydantic schema.

        Returns:
            SBDKConfigSchema instance
        """
        return self._schema

    # New enhanced methods

    def get_feature_flags(self) -> dict[str, bool]:
        """
        Get feature flags configuration.

        Returns:
            Dictionary of feature flags
        """
        return self._schema.features.model_dump()

    def get_performance_config(self) -> dict[str, Any]:
        """
        Get performance configuration.

        Returns:
            Dictionary of performance settings
        """
        return self._schema.performance.model_dump()

    def get_pipelines_config(self) -> list[dict[str, Any]]:
        """
        Get pipelines configuration.

        Returns:
            List of pipeline configurations
        """
        return [p.model_dump() for p in self._schema.pipelines]

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name

        Returns:
            True if feature is enabled
        """
        return getattr(self._schema.features, feature, False)


def load_config(config_path: str = "sbdk_config.json") -> SBDKConfig:
    """
    Load SBDK configuration from file.

    This is the main entry point for loading configuration throughout
    the application.

    Args:
        config_path: Path to configuration file

    Returns:
        Loaded and validated SBDKConfig instance

    Raises:
        ConfigurationError: If file not found or invalid
        SchemaValidationError: If validation fails
    """
    return SBDKConfig.load_from_file(config_path)


# Utility functions for configuration management

def create_default_config(
    project_name: str,
    duckdb_path: Optional[str] = None
) -> SBDKConfig:
    """
    Create default configuration for a new project.

    Args:
        project_name: Name of the project
        duckdb_path: Custom DuckDB path (default: data/{project}.duckdb)

    Returns:
        SBDKConfig instance with default settings
    """
    if duckdb_path is None:
        duckdb_path = f"data/{project_name}.duckdb"

    config_data = {
        "project": project_name,
        "duckdb_path": duckdb_path,
        "pipelines_path": "./pipelines",
        "dbt_path": "./dbt",
        "profiles_dir": "~/.dbt"
    }

    return SBDKConfig(config_data)


def merge_configs(
    base: SBDKConfig,
    override: dict[str, Any]
) -> SBDKConfig:
    """
    Merge configuration override into base configuration.

    Args:
        base: Base configuration
        override: Override values

    Returns:
        New SBDKConfig with merged values
    """
    merged_data = base.model_dump()
    merged_data.update(override)

    return SBDKConfig(merged_data)
