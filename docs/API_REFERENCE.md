# SBDK.dev API Reference

## Overview
SBDK.dev provides both CLI and Python API interfaces for data pipeline development. This reference covers all available commands, options, and programmatic interfaces.

## CLI API Reference

### Core Commands

#### `sbdk init`
Initialize a new SBDK project with guided setup.

```bash
sbdk init <project_name> [OPTIONS]
```

**Arguments:**
- `project_name`: Name of the project to create

**Options:**
- `--template TEXT`: Template to use (default: "default")  
- `--force, -f`: Overwrite existing directory
- `--help`: Show help message

**Examples:**
```bash
# Create new project with guided setup
sbdk init my_analytics_project

# Force overwrite existing project
sbdk init existing_project --force

# Use specific template
sbdk init custom_project --template advanced
```

**Output:**
- Creates complete project structure
- Configures local database paths
- Sets up dbt profiles automatically
- Provides next steps guidance

---

#### `sbdk run`
Execute data pipeline with comprehensive options.

```bash
sbdk run [OPTIONS]
```

**Options:**
- `--visual`: Run with interactive guided interface
- `--watch`: Development mode with file watching and auto-reload
- `--pipelines-only`: Run only DLT pipelines, skip dbt transformations
- `--dbt-only`: Run only dbt transformations, skip pipeline generation
- `--config TEXT`: Custom configuration file path (default: "sbdk_config.json")
- `--quiet, -q`: Suppress non-essential output
- `--help`: Show help message

**Examples:**
```bash
# Execute complete pipeline
sbdk run

# Interactive mode with guided flows
sbdk run --visual

# Development mode with hot reload
sbdk run --watch

# Run only data generation
sbdk run --pipelines-only

# Run only transformations
sbdk run --dbt-only

# Use custom configuration
sbdk run --config custom_config.json

# Quiet execution
sbdk run --quiet
```

**Interactive Mode Features:**
- Smart first-run detection
- Welcome flow with guided options
- Real-time progress tracking
- Context-aware suggestions
- Clean, intuitive interface

---

#### `sbdk interactive`
Launch full interactive CLI mode.

```bash
sbdk interactive [OPTIONS]
```

**Options:**
- `--help`: Show help message

**Features:**
- Menu-driven interface
- Project status monitoring
- Pipeline execution controls
- Database shell access
- System diagnostics

**Interactive Menu Options:**
1. Run full pipeline (DLT + dbt)
2. Run pipelines only
3. Run dbt only
4. Watch mode (auto-run on changes)
5. View database (DuckDB shell)
6. Project information
7. Quit

---

#### `sbdk debug`
System diagnostics and health checks.

```bash
sbdk debug [OPTIONS]
```

**Options:**
- `--help`: Show help message

**Diagnostics Include:**
- Configuration validation
- Database connectivity
- File system permissions
- Dependency verification
- Performance metrics
- Error analysis

**Example Output:**
```
🔍 SBDK System Diagnostics

✅ Configuration: Valid
✅ Database: Connected (data/project.duckdb)
✅ Pipelines: 3 files found
✅ dbt Models: 8 models configured
✅ System: All dependencies available

Performance Metrics:
- Database size: 18.2 MB
- Last run: 2 minutes ago
- Pipeline status: Healthy
```

---

#### `sbdk webhooks`
Start webhook listener server for integrations.

```bash
sbdk webhooks [OPTIONS]
```

**Options:**
- `--port INTEGER`: Server port (default: 8000)
- `--host TEXT`: Server host (default: "localhost")
- `--help`: Show help message

**Endpoints:**
- `POST /register`: Project registration
- `POST /track/usage`: Usage analytics (optional)
- `POST /webhook/github`: GitHub integration

---

#### `sbdk version`
Display version and system information.

```bash
sbdk version [OPTIONS]
```

**Options:**
- `--help`: Show help message

**Output:**
```
SBDK.dev v1.0.1
Python: 3.11.5
Platform: macOS-14.0-arm64
Database: DuckDB 0.9.0
Dependencies: All up-to-date
```

## Python API Reference

### Core Classes

#### `SBDKConfig`
Configuration management for SBDK projects.

```python
from sbdk.core.config import SBDKConfig

# Load configuration
config = SBDKConfig.from_file("sbdk_config.json")

# Create new configuration
config = SBDKConfig(
    project="my_project",
    duckdb_path="data/my_project.duckdb",
    target="dev"
)

# Get resolved paths
db_path = config.get_duckdb_path()
pipelines_path = config.get_pipelines_path()
```

**Attributes:**
- `project: str`: Project name
- `target: str`: Environment target (default: "dev")
- `duckdb_path: str`: Path to DuckDB database file
- `pipelines_path: str`: Path to DLT pipelines directory
- `dbt_path: str`: Path to dbt project directory

**Methods:**
- `get_duckdb_path() -> Path`: Get resolved database path
- `get_pipelines_path() -> Path`: Get resolved pipelines path
- `get_dbt_path() -> Path`: Get resolved dbt path
- `validate() -> bool`: Validate configuration

---

#### `SBDKProject`
Project management and operations.

```python
from sbdk.core.project import SBDKProject

# Initialize project
project = SBDKProject("my_project")

# Project operations
project.initialize()
project.run_pipelines()
project.run_dbt()
project.get_status()
```

**Methods:**
- `initialize()`: Set up project structure
- `run_pipelines()`: Execute DLT pipelines
- `run_dbt()`: Execute dbt transformations
- `get_status() -> dict`: Get project status
- `validate() -> bool`: Validate project health

---

#### `SBDKInteractive`
Interactive CLI interface management.

```python
from sbdk.cli.interactive import SBDKInteractive

# Start interactive session
cli = SBDKInteractive(project_path=".")
cli.run()

# Check project status
status = cli._get_project_status()
is_first_run = cli._is_first_run()
```

**Features:**
- Smart first-run detection
- Guided welcome flows
- Real-time project monitoring
- Context-aware suggestions

## Configuration Schema

### `sbdk_config.json`
```json
{
  "project": "string",              // Project name (required)
  "target": "dev|prod",             // Environment target
  "duckdb_path": "string",          // Database file path
  "pipelines_path": "string",       // Pipelines directory
  "dbt_path": "string",             // dbt project directory
  "profiles_dir": "string",         // dbt profiles directory
  "data_volume": {                  // Synthetic data configuration
    "users": "number",              // Number of users to generate
    "events": "number",             // Number of events to generate
    "orders": "number"              // Number of orders to generate
  },
  "performance": {                  // Performance settings
    "batch_size": "number",         // Processing batch size
    "parallel_processing": "boolean", // Enable parallel execution
    "memory_optimization": "boolean"  // Enable memory optimization
  },
  "features": {                     // Feature flags
    "quality_monitoring": "boolean", // Enable data quality monitoring
    "unique_validation": "boolean",  // Enable uniqueness validation
    "business_rules": "boolean"      // Enable business rule validation
  },
  "tracking": {                     // Analytics configuration
    "enabled": "boolean",           // Enable usage tracking
    "uuid": "string",               // Anonymous project UUID
    "endpoint": "string"            // Analytics endpoint
  }
}
```

## Error Handling

### Common Error Codes
- `CONFIG_NOT_FOUND`: Configuration file missing
- `DATABASE_CONNECTION_FAILED`: Cannot connect to DuckDB
- `PIPELINE_EXECUTION_FAILED`: Pipeline execution error
- `DBT_EXECUTION_FAILED`: dbt transformation error
- `VALIDATION_FAILED`: Data validation error

### Error Response Format
```json
{
  "error": "CONFIG_NOT_FOUND",
  "message": "Configuration file not found. Run 'sbdk init' first.",
  "suggestions": [
    "Run 'sbdk init my_project' to create a new project",
    "Check if you're in the correct directory",
    "Verify sbdk_config.json exists"
  ]
}
```

## Integration Examples

### GitHub Actions
```yaml
name: SBDK Pipeline Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install SBDK
        run: pip install sbdk-dev
      
      - name: Test Pipeline
        run: |
          sbdk init test_project
          cd test_project
          sbdk run --quiet
          sbdk debug
```

### Docker Integration
```dockerfile
FROM python:3.11-slim

RUN pip install sbdk-dev

WORKDIR /app
COPY . .

RUN sbdk init production_pipeline
WORKDIR /app/production_pipeline

CMD ["sbdk", "run"]
```

### Python Script Integration
```python
#!/usr/bin/env python

import subprocess
import sys
from pathlib import Path

def run_pipeline():
    """Execute SBDK pipeline programmatically"""
    
    # Initialize project if needed
    if not Path("sbdk_config.json").exists():
        subprocess.run(["sbdk", "init", "automated_pipeline"], check=True)
        
    # Run pipeline
    result = subprocess.run(["sbdk", "run", "--quiet"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Pipeline executed successfully")
        return True
    else:
        print(f"❌ Pipeline failed: {result.stderr}")
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
```

## Performance Optimization

### Recommended Settings
```json
{
  "performance": {
    "batch_size": 10000,
    "parallel_processing": true,
    "memory_optimization": true
  },
  "data_volume": {
    "users": 50000,
    "events": 250000,
    "orders": 100000
  }
}
```

### Monitoring Commands
```bash
# Check system performance
sbdk debug

# Monitor during execution
sbdk run --visual

# Batch processing optimization
sbdk run --config optimized_config.json
```

This API reference provides comprehensive coverage of all SBDK.dev interfaces for both CLI and programmatic usage.