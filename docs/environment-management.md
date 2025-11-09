# Environment Management

SBDK Environment Management enables you to create, switch between, and manage multiple isolated environments (dev, staging, prod) with different configurations and templates.

## Quick Start

### Create an Environment

```bash
# Create basic environment
sbdk env create dev

# Create with template
sbdk env create analytics --template analytics

# Create by copying existing
sbdk env create staging --copy-from dev
```

### Switch Environments

```bash
# Switch to dev environment
sbdk env switch dev

# Switch with performance timing
sbdk env switch prod --verbose
```

### List Environments

```bash
# List all environments
sbdk env list

# List with details
sbdk env list --verbose
```

### Check Status

```bash
# Show current environment status
sbdk env status

# Show detailed status
sbdk env status --verbose
```

### Delete Environment

```bash
# Delete environment (with confirmation)
sbdk env delete old-env

# Force delete without confirmation
sbdk env delete old-env --force
```

## Templates

SBDK provides three built-in templates:

### Analytics Template
- Full-featured with dbt, DLT, and quality monitoring
- Optimized for data analytics pipelines
- Includes parallel processing and intelligent caching
- Memory limit: 2GB

```bash
sbdk env create analytics --template analytics
```

### ML Template
- Optimized for machine learning workflows
- Higher memory limits (4GB)
- More worker threads for parallel training
- Aggressive caching strategy

```bash
sbdk env create ml-dev --template ml
```

### Basic Template
- Minimal configuration
- Low resource usage
- Perfect for learning and simple experiments

```bash
sbdk env create simple --template basic
```

## Environment Configuration

Each environment has its own isolated configuration stored in `~/.sbdk/environments/<name>/config.json`:

```json
{
  "name": "dev",
  "template": "analytics",
  "target": "duckdb",
  "description": "Development environment",
  "features": {
    "parallel_processing": true,
    "memory_optimization": true,
    "quality_monitoring": true,
    "incremental_builds": true
  },
  "performance": {
    "batch_size": 10000,
    "worker_threads": 4,
    "cache_strategy": "intelligent",
    "memory_limit_mb": 2048
  }
}
```

## Performance

Environment switching is optimized for speed:
- **Target**: <2 seconds for environment switch
- Caching for frequently accessed configurations
- Minimal validation in fast mode

```bash
# Fast switch (skip validation)
sbdk env switch dev --fast

# Switch with performance metrics
sbdk env switch dev --verbose
```

## Use Cases

### Development Workflow

```bash
# Create development environment
sbdk env create dev --template analytics

# Work on features
sbdk env switch dev
sbdk run

# Create staging for testing
sbdk env create staging --copy-from dev
sbdk env switch staging
sbdk run --test

# Create production environment
sbdk env create prod --template analytics --description "Production"
sbdk env switch prod
```

### Multi-Project Setup

```bash
# Project A - Analytics
sbdk env create project-a-dev --template analytics
sbdk env create project-a-prod --template analytics

# Project B - ML
sbdk env create project-b-dev --template ml
sbdk env create project-b-prod --template ml

# Switch between projects
sbdk env switch project-a-dev
sbdk env switch project-b-dev
```

## Troubleshooting

### Environment Not Found

```bash
# List available environments
sbdk env list

# Create if missing
sbdk env create <name>
```

### Cannot Delete Active Environment

```bash
# Switch to different environment first
sbdk env switch <other-env>
sbdk env delete <name>

# Or force delete
sbdk env delete <name> --force
```

### Slow Switching

```bash
# Use fast mode
sbdk env switch <name> --fast

# Check performance
sbdk env switch <name> --verbose
```

## Advanced Usage

### View Available Templates

```bash
sbdk env templates
```

### Custom Configuration

Environments can be customized by editing `~/.sbdk/environments/<name>/config.json` directly.

### Environment Directory Structure

```
~/.sbdk/environments/<name>/
├── config.json          # Environment configuration
├── data/                # DuckDB databases
├── pipelines/           # DLT pipelines
├── dbt/                 # dbt models
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
└── logs/                # Pipeline logs
```

## API Usage

```python
from sbdk.environment import EnvironmentManager, EnvironmentTemplate

# Create manager
manager = EnvironmentManager()

# Create environment
env_path = manager.create("dev", template=EnvironmentTemplate.ANALYTICS)

# Switch environment
manager.switch("dev")

# List environments
environments = manager.list_environments()

# Get status
status = manager.get_status()
```

## See Also

- [SBDK Platform Vision](../SBDK_PLATFORM_VISION.md)
- [CLI Reference](./cli-reference.md)
- [Configuration Guide](./configuration.md)
