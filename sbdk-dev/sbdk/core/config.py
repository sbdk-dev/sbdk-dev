"""
SBDK configuration management
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field


class SBDKConfig(BaseModel):
    """SBDK project configuration"""

    project: str = Field(..., description="Project name")
    target: str = Field(default="dev", description="Target environment")
    duckdb_path: str = Field(..., description="Path to DuckDB database file")
    pipelines_path: str = Field(
        default="./pipelines", description="Path to DLT pipelines"
    )
    dbt_path: str = Field(default="./dbt", description="Path to dbt project")
    profiles_dir: str = Field(default="~/.dbt", description="dbt profiles directory")

    # Additional configuration options
    webhook_port: int = Field(default=8000, description="Webhook server port")
    webhook_host: str = Field(default="0.0.0.0", description="Webhook server host")
    auto_reload: bool = Field(
        default=True, description="Enable auto-reload for development"
    )
    watch_paths: list[str] = Field(
        default_factory=lambda: ["pipelines/", "dbt/models/"],
        description="Paths to watch for file changes",
    )

    @classmethod
    def load_from_file(cls, config_path: str = "sbdk_config.json") -> "SBDKConfig":
        """Load configuration from JSON file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file) as f:
            config_data = json.load(f)

        return cls(**config_data)

    def save_to_file(self, config_path: str = "sbdk_config.json") -> None:
        """Save configuration to JSON file"""
        config_file = Path(config_path)

        with open(config_file, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    def get_duckdb_path(self) -> Path:
        """Get resolved DuckDB path"""
        return Path(self.duckdb_path).resolve()

    def get_pipelines_path(self) -> Path:
        """Get resolved pipelines path"""
        return Path(self.pipelines_path).resolve()

    def get_dbt_path(self) -> Path:
        """Get resolved dbt path"""
        return Path(self.dbt_path).resolve()

    def get_profiles_dir(self) -> Path:
        """Get resolved dbt profiles directory"""
        return Path(self.profiles_dir).expanduser().resolve()

    def validate_paths(self) -> dict[str, bool]:
        """Validate that required paths exist"""
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


def load_config(config_path: str = "sbdk_config.json") -> SBDKConfig:
    """Load SBDK configuration from file"""
    return SBDKConfig.load_from_file(config_path)
