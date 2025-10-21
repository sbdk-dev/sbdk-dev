"""
SBDK Configuration Validators

Pydantic schemas for validating configuration files and command inputs.
Provides type safety, validation, and clear error messages.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TargetEnvironment(str, Enum):
    """Supported target environments."""
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class FeatureFlags(BaseModel):
    """Feature flags configuration."""
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing of pipelines"
    )
    memory_optimization: bool = Field(
        default=True,
        description="Enable memory optimization strategies"
    )
    quality_monitoring: bool = Field(
        default=True,
        description="Enable data quality monitoring"
    )
    visual_interface: bool = Field(
        default=True,
        description="Enable visual CLI interface"
    )


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""
    batch_size: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Batch size for data processing"
    )
    worker_threads: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker threads for parallel operations"
    )
    cache_strategy: str = Field(
        default="intelligent",
        pattern="^(intelligent|aggressive|conservative|none)$",
        description="Caching strategy for pipeline execution"
    )
    memory_limit_mb: Optional[int] = Field(
        default=None,
        ge=512,
        description="Memory limit in MB (None = unlimited)"
    )


class PipelineConfig(BaseModel):
    """Individual pipeline configuration."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Pipeline name (alphanumeric, underscore, hyphen)"
    )
    enabled: bool = Field(
        default=True,
        description="Whether pipeline is enabled"
    )
    module_path: str = Field(
        ...,
        description="Python module path for pipeline (e.g., pipelines.users)"
    )
    batch_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Override global batch size for this pipeline"
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of pipeline names this pipeline depends on"
    )


class DBTConfig(BaseModel):
    """dbt-specific configuration."""
    project_dir: Path = Field(
        default=Path("./dbt"),
        description="Path to dbt project directory"
    )
    profiles_dir: Path = Field(
        default=Path("~/.dbt"),
        description="Path to dbt profiles directory"
    )
    target: str = Field(
        default="dev",
        description="dbt target environment"
    )
    threads: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of threads for dbt execution"
    )
    vars: dict[str, Any] = Field(
        default_factory=dict,
        description="dbt variables to pass to models"
    )

    @field_validator('project_dir', 'profiles_dir', mode='after')
    @classmethod
    def expand_path(cls, v: Path) -> Path:
        """Expand user home directory in paths."""
        return v.expanduser()

    @model_validator(mode='after')
    def expand_default_paths(self) -> 'DBTConfig':
        """Ensure default paths are expanded."""
        self.project_dir = self.project_dir.expanduser()
        self.profiles_dir = self.profiles_dir.expanduser()
        return self


class DuckDBConfig(BaseModel):
    """DuckDB database configuration."""
    path: Path = Field(
        ...,
        description="Path to DuckDB database file"
    )
    memory_limit: Optional[str] = Field(
        default=None,
        pattern="^\\d+[MGT]B$",
        description="Memory limit (e.g., '4GB', '512MB')"
    )
    threads: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of threads for DuckDB operations"
    )
    read_only: bool = Field(
        default=False,
        description="Open database in read-only mode"
    )


class WebhookConfig(BaseModel):
    """Webhook server configuration."""
    enabled: bool = Field(
        default=False,
        description="Enable webhook server"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Webhook server host"
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Webhook server port"
    )
    secret: Optional[str] = Field(
        default=None,
        min_length=16,
        description="Webhook secret for request validation"
    )
    endpoints: dict[str, str] = Field(
        default_factory=lambda: {
            "github": "/webhook/github",
            "register": "/register",
            "track": "/track/usage"
        },
        description="Webhook endpoint paths"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    file: Optional[Path] = Field(
        default=None,
        description="Log file path (None = console only)"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    rotation: Optional[str] = Field(
        default="1 day",
        description="Log rotation interval (e.g., '1 day', '100 MB')"
    )


class SBDKConfig(BaseModel):
    """
    Main SBDK configuration schema.

    Validates the complete sbdk_config.json structure with type checking
    and business rule validation.
    """

    # Project metadata
    project: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Project name"
    )
    version: str = Field(
        default="1.0.0",
        pattern="^\\d+\\.\\d+\\.\\d+$",
        description="Project version (semantic versioning)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Project description"
    )

    # Environment
    target: TargetEnvironment = Field(
        default=TargetEnvironment.DEV,
        description="Target environment (dev, test, prod)"
    )

    # Paths
    duckdb_path: str = Field(
        ...,
        description="Path to DuckDB database file"
    )
    pipelines_path: Path = Field(
        default=Path("./pipelines"),
        description="Path to pipelines directory"
    )
    dbt_path: Path = Field(
        default=Path("./dbt"),
        description="Path to dbt project directory"
    )
    profiles_dir: Path = Field(
        default=Path("~/.dbt"),
        description="Path to dbt profiles directory"
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="Path to data directory"
    )

    # Nested configurations
    dbt: Optional[DBTConfig] = Field(
        default=None,
        description="dbt-specific configuration"
    )
    duckdb: Optional[DuckDBConfig] = Field(
        default=None,
        description="DuckDB-specific configuration"
    )
    features: FeatureFlags = Field(
        default_factory=FeatureFlags,
        description="Feature flags"
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig,
        description="Performance tuning configuration"
    )
    pipelines: list[PipelineConfig] = Field(
        default_factory=list,
        description="Pipeline configurations"
    )
    webhooks: Optional[WebhookConfig] = Field(
        default=None,
        description="Webhook server configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional project metadata"
    )

    @field_validator('pipelines_path', 'dbt_path', 'profiles_dir', 'data_dir')
    @classmethod
    def expand_path(cls, v: Path) -> Path:
        """Expand user home directory in paths."""
        return v.expanduser()

    @model_validator(mode='after')
    def validate_pipeline_dependencies(self) -> 'SBDKConfig':
        """Validate that pipeline dependencies exist."""
        if not self.pipelines:
            return self

        pipeline_names = {p.name for p in self.pipelines}

        for pipeline in self.pipelines:
            for dep in pipeline.dependencies:
                if dep not in pipeline_names:
                    raise ValueError(
                        f"Pipeline '{pipeline.name}' depends on non-existent pipeline '{dep}'"
                    )

        return self

    @model_validator(mode='after')
    def validate_paths_exist(self) -> 'SBDKConfig':
        """Validate that essential paths exist (in non-init contexts)."""
        # Skip validation during project initialization
        # This will be checked by the context manager at runtime
        return self

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation with Path objects converted to strings
        """
        data = self.model_dump(mode='json', exclude_none=True)
        return data

    def to_json(self) -> str:
        """
        Convert configuration to JSON string.

        Returns:
            JSON string representation
        """
        return self.model_dump_json(indent=2, exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SBDKConfig':
        """
        Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Validated SBDKConfig instance
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SBDKConfig':
        """
        Create configuration from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Validated SBDKConfig instance
        """
        return cls.model_validate_json(json_str)

    @classmethod
    def from_file(cls, file_path: Path) -> 'SBDKConfig':
        """
        Load and validate configuration from file.

        Args:
            file_path: Path to configuration file

        Returns:
            Validated SBDKConfig instance
        """
        with open(file_path) as f:
            import json
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, file_path: Path) -> None:
        """
        Save configuration to file.

        Args:
            file_path: Path to save configuration
        """
        with open(file_path, 'w') as f:
            f.write(self.to_json())


# Command input validators

class InitCommandInput(BaseModel):
    """Validation schema for sbdk init command."""
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Project name (alphanumeric, underscore, hyphen)"
    )
    template: str = Field(
        default="default",
        description="Template name to use"
    )
    force: bool = Field(
        default=False,
        description="Force overwrite existing directory"
    )


class RunCommandInput(BaseModel):
    """Validation schema for sbdk run command."""
    visual: bool = Field(
        default=False,
        description="Run with visual interface"
    )
    watch: bool = Field(
        default=False,
        description="Watch for file changes and auto-rerun"
    )
    pipelines_only: bool = Field(
        default=False,
        description="Run only pipelines, skip dbt"
    )
    dbt_only: bool = Field(
        default=False,
        description="Run only dbt, skip pipelines"
    )
    config_file: str = Field(
        default="sbdk_config.json",
        description="Config file path"
    )
    quiet: bool = Field(
        default=False,
        description="Suppress non-essential output"
    )
    dry_run: bool = Field(
        default=False,
        description="Preview actions without executing"
    )

    @model_validator(mode='after')
    def validate_mutually_exclusive(self) -> 'RunCommandInput':
        """Validate mutually exclusive options."""
        if self.pipelines_only and self.dbt_only:
            raise ValueError("--pipelines-only and --dbt-only are mutually exclusive")

        if self.quiet and self.visual:
            raise ValueError("--quiet and --visual are mutually exclusive")

        return self
