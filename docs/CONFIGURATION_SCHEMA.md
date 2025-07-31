# SBDK Configuration Schema Design

## Overview
This document defines the complete configuration architecture for SBDK.dev, including the main configuration file schema, environment variables, and validation rules.

## 1. Main Configuration File (sbdk_config.json)

### Full Schema Definition
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SBDK Configuration",
  "description": "Configuration schema for SBDK.dev local-first data pipeline framework",
  "type": "object",
  "required": ["project", "target", "duckdb_path"],
  "properties": {
    "project": {
      "type": "string",
      "description": "Project name identifier",
      "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$",
      "minLength": 1,
      "maxLength": 50,
      "examples": ["my_analytics_project", "ecommerce-pipeline"]
    },
    "target": {
      "type": "string",
      "description": "Environment target for execution",
      "enum": ["dev", "staging", "prod"],
      "default": "dev"
    },
    "version": {
      "type": "string",
      "description": "Configuration schema version",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "default": "1.0.0"
    },
    "duckdb_path": {
      "type": "string",
      "description": "Path to DuckDB database file",
      "default": "data/dev.duckdb",
      "examples": ["data/dev.duckdb", "/tmp/analytics.duckdb"]
    },
    "pipelines_path": {
      "type": "string",
      "description": "Directory containing DLT pipeline definitions",
      "default": "./pipelines"
    },
    "dbt_path": {
      "type": "string", 
      "description": "Path to dbt project directory",
      "default": "./dbt"
    },
    "profiles_dir": {
      "type": "string",
      "description": "dbt profiles directory path",
      "default": "~/.dbt"
    },
    "data_volume": {
      "type": "object",
      "description": "Configuration for synthetic data generation volumes",
      "properties": {
        "users": {
          "type": "integer",
          "description": "Number of synthetic users to generate",
          "minimum": 100,
          "maximum": 1000000,
          "default": 10000
        },
        "events_per_user": {
          "type": "number",
          "description": "Average events per user (multiplier)",
          "minimum": 1,
          "maximum": 100,
          "default": 5
        },
        "orders_per_user": {
          "type": "number",
          "description": "Average orders per user (multiplier)",
          "minimum": 0.1,
          "maximum": 10,
          "default": 2
        },
        "time_range_days": {
          "type": "integer", 
          "description": "Historical data range in days",
          "minimum": 1,
          "maximum": 3650,
          "default": 365
        }
      },
      "additionalProperties": false
    },
    "tracking": {
      "type": "object",
      "description": "Analytics and tracking configuration",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Enable usage tracking and analytics",
          "default": false
        },
        "uuid": {
          "type": "string",
          "description": "Unique project identifier for tracking",
          "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        },
        "endpoint": {
          "type": "string",
          "description": "Tracking server endpoint URL",
          "format": "uri",
          "default": "https://api.sbdk.dev"
        },
        "anonymous": {
          "type": "boolean",
          "description": "Use anonymous tracking (no personal data)",
          "default": true
        }
      },
      "additionalProperties": false
    },
    "database": {
      "type": "object",
      "description": "Database connection and performance settings",
      "properties": {
        "memory_limit": {
          "type": "string",
          "description": "DuckDB memory limit (e.g., '1GB', '512MB')",
          "pattern": "^\\d+(\\.\\d+)?(KB|MB|GB|TB)$",
          "default": "1GB"
        },
        "threads": {
          "type": "integer",
          "description": "Number of threads for query execution",
          "minimum": 1,
          "maximum": 32,
          "default": 4
        },
        "temp_directory": {
          "type": "string",
          "description": "Temporary directory for DuckDB operations",
          "default": "/tmp"
        },
        "enable_progress_bar": {
          "type": "boolean",
          "description": "Show progress bars for long-running queries",
          "default": true
        }
      },
      "additionalProperties": false
    },
    "dlt": {
      "type": "object",
      "description": "DLT pipeline configuration",
      "properties": {
        "pipeline_name": {
          "type": "string",
          "description": "Default DLT pipeline name",
          "default": "sbdk_pipeline"
        },
        "dataset_name": {
          "type": "string", 
          "description": "Default dataset name for raw data",
          "default": "raw_data"
        },
        "write_disposition": {
          "type": "string",
          "description": "Default write behavior for DLT loads",
          "enum": ["replace", "append", "merge"],
          "default": "replace"
        },
        "loader_file_format": {
          "type": "string",
          "description": "File format for DLT staging",
          "enum": ["parquet", "jsonl", "csv"],
          "default": "parquet"
        }
      },
      "additionalProperties": false
    },
    "dbt": {
      "type": "object",
      "description": "dbt execution configuration",
      "properties": {
        "profile_name": {
          "type": "string",
          "description": "dbt profile name to use",
          "default": "sbdk"
        },
        "threads": {
          "type": "integer",
          "description": "Number of threads for dbt execution",
          "minimum": 1,
          "maximum": 16,
          "default": 4
        },
        "target_schema": {
          "type": "string",
          "description": "Target schema for dbt models",
          "default": "analytics"
        },
        "full_refresh": {
          "type": "boolean",
          "description": "Default full refresh mode for incremental models",
          "default": false
        },
        "test_failure_severity": {
          "type": "string",
          "description": "Severity level for test failures",
          "enum": ["warn", "error"],
          "default": "warn"
        }
      },
      "additionalProperties": false
    },
    "cli": {
      "type": "object",
      "description": "CLI behavior and display settings",
      "properties": {
        "verbose": {
          "type": "boolean",
          "description": "Enable verbose logging output",
          "default": false
        },
        "color": {
          "type": "boolean",
          "description": "Enable colored terminal output",
          "default": true
        },
        "progress_bars": {
          "type": "boolean",
          "description": "Show progress bars for operations",
          "default": true
        },
        "auto_confirm": {
          "type": "boolean",
          "description": "Auto-confirm destructive operations",
          "default": false
        }
      },
      "additionalProperties": false
    },
    "webhooks": {
      "type": "object",
      "description": "Webhook server configuration",
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "Enable webhook server",
          "default": false
        },
        "host": {
          "type": "string",
          "description": "Webhook server host",
          "default": "0.0.0.0"
        },
        "port": {
          "type": "integer",
          "description": "Webhook server port",
          "minimum": 1024,
          "maximum": 65535,
          "default": 8000
        },
        "github_secret": {
          "type": "string",
          "description": "GitHub webhook secret for verification",
          "minLength": 8
        },
        "auto_run_on_push": {
          "type": "boolean",
          "description": "Automatically run pipeline on GitHub push",
          "default": true
        }
      },
      "additionalProperties": false
    },
    "logging": {
      "type": "object",
      "description": "Logging configuration",
      "properties": {
        "level": {
          "type": "string",
          "description": "Logging level",
          "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
          "default": "INFO"
        },
        "file": {
          "type": "string",
          "description": "Log file path (empty for stdout only)",
          "default": ""
        },
        "format": {
          "type": "string",
          "description": "Log message format",
          "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "rotation": {
          "type": "object",
          "description": "Log file rotation settings",
          "properties": {
            "max_size": {
              "type": "string",
              "description": "Maximum log file size before rotation",
              "pattern": "^\\d+(\\.\\d+)?(KB|MB|GB)$",
              "default": "10MB"
            },
            "backup_count": {
              "type": "integer",
              "description": "Number of backup log files to keep",
              "minimum": 0,
              "maximum": 50,
              "default": 5
            }
          }
        }
      },
      "additionalProperties": false
    },
    "performance": {
      "type": "object",
      "description": "Performance optimization settings",
      "properties": {
        "cache_enabled": {
          "type": "boolean",
          "description": "Enable query result caching",
          "default": true
        },
        "cache_ttl_seconds": {
          "type": "integer",
          "description": "Cache time-to-live in seconds",
          "minimum": 60,
          "maximum": 86400,
          "default": 3600
        },
        "parallel_pipelines": {
          "type": "boolean",
          "description": "Run DLT pipelines in parallel",
          "default": true
        },
        "batch_size": {
          "type": "integer",
          "description": "Default batch size for data processing",
          "minimum": 1000,
          "maximum": 1000000,
          "default": 50000
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

## 2. Environment Variables Schema

### .env File Template
```bash
# SBDK Environment Configuration
# Copy this file to .env and customize for your environment

# Database Configuration
SBDK_DUCKDB_PATH=data/dev.duckdb
SBDK_DUCKDB_MEMORY_LIMIT=1GB
SBDK_DUCKDB_THREADS=4

# DLT Configuration  
SBDK_DLT_PIPELINE_NAME=sbdk_pipeline
SBDK_DLT_DATASET_NAME=raw_data

# dbt Configuration
SBDK_DBT_PROFILE_NAME=sbdk
SBDK_DBT_THREADS=4
SBDK_DBT_TARGET_SCHEMA=analytics

# Tracking Configuration (Optional)
SBDK_TRACKING_ENABLED=false
SBDK_TRACKING_UUID=
SBDK_TRACKING_ENDPOINT=https://api.sbdk.dev
SBDK_TRACKING_ANONYMOUS=true

# Webhook Configuration
SBDK_WEBHOOKS_ENABLED=false
SBDK_WEBHOOKS_HOST=0.0.0.0
SBDK_WEBHOOKS_PORT=8000
SBDK_GITHUB_WEBHOOK_SECRET=

# Logging Configuration
SBDK_LOG_LEVEL=INFO
SBDK_LOG_FILE=
SBDK_LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance Configuration
SBDK_CACHE_ENABLED=true
SBDK_CACHE_TTL_SECONDS=3600
SBDK_PARALLEL_PIPELINES=true
SBDK_BATCH_SIZE=50000

# Development Configuration
SBDK_VERBOSE=false
SBDK_COLOR=true
SBDK_PROGRESS_BARS=true
SBDK_AUTO_CONFIRM=false
```

## 3. Configuration Validation and Loading

### Python Configuration Loader (config.py)
```python
"""
Configuration management for SBDK.dev
Uses Pydantic for validation and Dynaconf for environment loading
"""

from typing import Optional, Dict, Any
from pathlib import Path
import os
import json
from pydantic import BaseModel, Field, validator, AnyUrl
from dynaconf import Dynaconf


class DataVolumeConfig(BaseModel):
    """Synthetic data volume configuration"""
    users: int = Field(default=10000, ge=100, le=1000000)
    events_per_user: float = Field(default=5.0, ge=1.0, le=100.0)
    orders_per_user: float = Field(default=2.0, ge=0.1, le=10.0)
    time_range_days: int = Field(default=365, ge=1, le=3650)


class TrackingConfig(BaseModel):
    """Analytics tracking configuration"""
    enabled: bool = False
    uuid: Optional[str] = Field(None, regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
    endpoint: AnyUrl = Field(default="https://api.sbdk.dev")
    anonymous: bool = True


class DatabaseConfig(BaseModel):
    """DuckDB database configuration"""
    memory_limit: str = Field(default="1GB", regex=r'^\d+(\.\d+)?(KB|MB|GB|TB)$')
    threads: int = Field(default=4, ge=1, le=32)
    temp_directory: str = "/tmp"
    enable_progress_bar: bool = True


class DLTConfig(BaseModel):
    """DLT pipeline configuration"""
    pipeline_name: str = "sbdk_pipeline"
    dataset_name: str = "raw_data"
    write_disposition: str = Field(default="replace", regex=r'^(replace|append|merge)$')
    loader_file_format: str = Field(default="parquet", regex=r'^(parquet|jsonl|csv)$')


class DBTConfig(BaseModel):
    """dbt execution configuration"""
    profile_name: str = "sbdk"
    threads: int = Field(default=4, ge=1, le=16)
    target_schema: str = "analytics"
    full_refresh: bool = False
    test_failure_severity: str = Field(default="warn", regex=r'^(warn|error)$')


class CLIConfig(BaseModel):
    """CLI behavior configuration"""
    verbose: bool = False
    color: bool = True
    progress_bars: bool = True
    auto_confirm: bool = False


class WebhookConfig(BaseModel):
    """Webhook server configuration"""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1024, le=65535)
    github_secret: Optional[str] = Field(None, min_length=8)
    auto_run_on_push: bool = True


class LogRotationConfig(BaseModel):
    """Log rotation settings"""
    max_size: str = Field(default="10MB", regex=r'^\d+(\.\d+)?(KB|MB|GB)$')
    backup_count: int = Field(default=5, ge=0, le=50)


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", regex=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    file: str = ""
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotation: LogRotationConfig = LogRotationConfig()


class PerformanceConfig(BaseModel):
    """Performance optimization settings"""
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    parallel_pipelines: bool = True
    batch_size: int = Field(default=50000, ge=1000, le=1000000)


class SBDKConfig(BaseModel):
    """Main SBDK configuration model"""
    project: str = Field(..., regex=r'^[a-zA-Z][a-zA-Z0-9_-]*$', min_length=1, max_length=50)
    target: str = Field(default="dev", regex=r'^(dev|staging|prod)$')
    version: str = Field(default="1.0.0", regex=r'^\d+\.\d+\.\d+$')
    
    # Path configurations
    duckdb_path: str = "data/dev.duckdb"
    pipelines_path: str = "./pipelines"
    dbt_path: str = "./dbt"
    profiles_dir: str = "~/.dbt"
    
    # Component configurations
    data_volume: DataVolumeConfig = DataVolumeConfig()
    tracking: TrackingConfig = TrackingConfig()
    database: DatabaseConfig = DatabaseConfig()
    dlt: DLTConfig = DLTConfig()
    dbt: DBTConfig = DBTConfig()
    cli: CLIConfig = CLIConfig()
    webhooks: WebhookConfig = WebhookConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    @validator('duckdb_path')
    def validate_duckdb_path(cls, v):
        """Ensure DuckDB path directory exists or can be created"""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())
    
    @validator('pipelines_path', 'dbt_path')
    def validate_directory_paths(cls, v):
        """Ensure directory paths exist"""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {v}")
        return str(path.resolve())
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"  # Don't allow extra fields
        validate_assignment = True  # Validate on assignment


class ConfigLoader:
    """Configuration loader with environment override support"""
    
    def __init__(self, config_file: str = "sbdk_config.json"):
        self.config_file = config_file
        self.dynaconf = Dynaconf(
            environments=True,
            env_prefix="SBDK",
            settings_files=[config_file],
            load_dotenv=True,
        )
    
    def load(self) -> SBDKConfig:
        """Load and validate configuration"""
        # Start with file-based config
        config_data = {}
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
        
        # Override with environment variables
        config_data.update(self._get_env_overrides())
        
        # Validate and return
        return SBDKConfig(**config_data)
    
    def _get_env_overrides(self) -> Dict[str, Any]:
        """Extract configuration from environment variables"""
        overrides = {}
        
        # Map environment variables to config structure
        env_mapping = {
            'SBDK_PROJECT': 'project',
            'SBDK_TARGET': 'target',
            'SBDK_DUCKDB_PATH': 'duckdb_path',
            'SBDK_PIPELINES_PATH': 'pipelines_path',
            'SBDK_DBT_PATH': 'dbt_path',
            'SBDK_PROFILES_DIR': 'profiles_dir',
            
            # Database config
            'SBDK_DUCKDB_MEMORY_LIMIT': 'database.memory_limit',
            'SBDK_DUCKDB_THREADS': 'database.threads',
            
            # DLT config
            'SBDK_DLT_PIPELINE_NAME': 'dlt.pipeline_name',
            'SBDK_DLT_DATASET_NAME': 'dlt.dataset_name',
            
            # dbt config
            'SBDK_DBT_PROFILE_NAME': 'dbt.profile_name',
            'SBDK_DBT_THREADS': 'dbt.threads',
            'SBDK_DBT_TARGET_SCHEMA': 'dbt.target_schema',
            
            # Tracking config
            'SBDK_TRACKING_ENABLED': 'tracking.enabled',
            'SBDK_TRACKING_UUID': 'tracking.uuid',
            'SBDK_TRACKING_ENDPOINT': 'tracking.endpoint',
            'SBDK_TRACKING_ANONYMOUS': 'tracking.anonymous',
            
            # CLI config
            'SBDK_VERBOSE': 'cli.verbose',
            'SBDK_COLOR': 'cli.color',
            'SBDK_PROGRESS_BARS': 'cli.progress_bars',
            'SBDK_AUTO_CONFIRM': 'cli.auto_confirm',
            
            # Webhook config
            'SBDK_WEBHOOKS_ENABLED': 'webhooks.enabled',
            'SBDK_WEBHOOKS_HOST': 'webhooks.host',
            'SBDK_WEBHOOKS_PORT': 'webhooks.port',
            'SBDK_GITHUB_WEBHOOK_SECRET': 'webhooks.github_secret',
            
            # Logging config
            'SBDK_LOG_LEVEL': 'logging.level',
            'SBDK_LOG_FILE': 'logging.file',
            'SBDK_LOG_FORMAT': 'logging.format',
            
            # Performance config
            'SBDK_CACHE_ENABLED': 'performance.cache_enabled',
            'SBDK_CACHE_TTL_SECONDS': 'performance.cache_ttl_seconds',
            'SBDK_PARALLEL_PIPELINES': 'performance.parallel_pipelines',
            'SBDK_BATCH_SIZE': 'performance.batch_size',
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                value = self._convert_env_value(value)
                self._set_nested_value(overrides, config_path, value)
        
        return overrides
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


# Global configuration instance
_config_loader = ConfigLoader()
config = _config_loader.load()


def reload_config(config_file: str = "sbdk_config.json") -> SBDKConfig:
    """Reload configuration from file"""
    global config, _config_loader
    _config_loader = ConfigLoader(config_file)
    config = _config_loader.load()
    return config


def get_config() -> SBDKConfig:
    """Get current configuration instance"""
    return config
```

## 4. Configuration Templates

### Development Template (sbdk_config.dev.json)
```json
{
  "project": "my_analytics_project",
  "target": "dev",
  "version": "1.0.0",
  "duckdb_path": "data/dev.duckdb",
  "pipelines_path": "./pipelines",
  "dbt_path": "./dbt",
  "profiles_dir": "~/.dbt",
  "data_volume": {
    "users": 1000,
    "events_per_user": 10,
    "orders_per_user": 2,
    "time_range_days": 90
  },
  "tracking": {
    "enabled": false,
    "anonymous": true
  },
  "database": {
    "memory_limit": "512MB",
    "threads": 2,
    "enable_progress_bar": true
  },
  "cli": {
    "verbose": true,
    "color": true,
    "progress_bars": true,
    "auto_confirm": false
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/sbdk_dev.log"
  }
}
```

### Production Template (sbdk_config.prod.json)
```json
{
  "project": "production_analytics",
  "target": "prod",
  "version": "1.0.0",
  "duckdb_path": "data/prod.duckdb",
  "pipelines_path": "./pipelines",
  "dbt_path": "./dbt",
  "profiles_dir": "/opt/dbt/profiles",
  "data_volume": {
    "users": 100000,
    "events_per_user": 25,
    "orders_per_user": 3,
    "time_range_days": 730
  },
  "tracking": {
    "enabled": true,
    "anonymous": true,
    "endpoint": "https://api.sbdk.dev"
  },
  "database": {
    "memory_limit": "4GB",
    "threads": 8,
    "enable_progress_bar": false
  },
  "dbt": {
    "threads": 8,
    "test_failure_severity": "error"
  },
  "cli": {
    "verbose": false,
    "color": false,
    "progress_bars": false,
    "auto_confirm": true
  },
  "webhooks": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000,
    "auto_run_on_push": true
  },
  "logging": {
    "level": "INFO",
    "file": "logs/sbdk_prod.log",
    "rotation": {
      "max_size": "100MB",
      "backup_count": 10
    }
  },
  "performance": {
    "cache_enabled": true,
    "cache_ttl_seconds": 7200,
    "parallel_pipelines": true,
    "batch_size": 100000
  }
}
```

## 5. Configuration CLI Commands

### CLI Integration Commands
```bash
# Show current configuration
sbdk config show

# Validate configuration file
sbdk config validate

# Initialize configuration from template
sbdk config init --template dev
sbdk config init --template prod

# Set configuration values
sbdk config set data_volume.users 50000
sbdk config set tracking.enabled true

# Get configuration values
sbdk config get database.memory_limit
sbdk config get dbt.threads

# Export configuration to different formats
sbdk config export --format yaml
sbdk config export --format toml
sbdk config export --format env > .env

# Check configuration differences
sbdk config diff sbdk_config.dev.json sbdk_config.prod.json
```

## 6. Configuration Migration and Versioning

### Version Migration Support
```python
"""Configuration migration utilities"""

from typing import Dict, Any
import semver


class ConfigMigrator:
    """Handle configuration migrations between versions"""
    
    def __init__(self):
        self.migrations = {
            "1.0.0": self._migrate_to_1_0_0,
            "1.1.0": self._migrate_to_1_1_0,
        }
    
    def migrate(self, config_data: Dict[str, Any], target_version: str = "1.0.0") -> Dict[str, Any]:
        """Migrate configuration to target version"""
        current_version = config_data.get("version", "0.1.0")
        
        if semver.compare(current_version, target_version) < 0:
            # Need to migrate up
            for version in sorted(self.migrations.keys()):
                if semver.compare(current_version, version) < 0:
                    config_data = self.migrations[version](config_data)
                    config_data["version"] = version
                    current_version = version
                    
                if version == target_version:
                    break
        
        return config_data
    
    def _migrate_to_1_0_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate to version 1.0.0"""
        # Add default performance settings if missing
        if "performance" not in config:
            config["performance"] = {
                "cache_enabled": True,
                "cache_ttl_seconds": 3600,
                "parallel_pipelines": True,
                "batch_size": 50000
            }
        
        return config
    
    def _migrate_to_1_1_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate to version 1.1.0 (example future migration)"""
        # Add new webhook authentication settings
        if "webhooks" in config and "auth" not in config["webhooks"]:
            config["webhooks"]["auth"] = {
                "enabled": False,
                "type": "basic"
            }
        
        return config
```

This comprehensive configuration schema provides a robust, validated, and extensible foundation for SBDK.dev with clear environment variable overrides, templates for different deployment scenarios, and migration support for future versions.