# SBDK.dev Configuration Guide

## Overview
SBDK.dev is designed to work **out-of-the-box** with zero configuration required. This guide covers advanced configuration options for customization and scaling.

## Zero-Configuration Approach

### Default Behavior
When you run `sbdk init my_project`, SBDK automatically creates:
- **Local database**: `data/my_project.duckdb` (self-contained)
- **Pipeline templates**: Production-ready DLT pipelines
- **dbt configuration**: Properly aligned with local database
- **Intelligent CLI**: Smart first-run detection and guidance

### Guided Setup Flow
On first run, SBDK provides intelligent guidance:
1. **Demo Setup**: Run with sample data (recommended for new users)
2. **Custom Setup**: Configuration guidance for experienced users
3. **Learn More**: Project information and architecture overview

## Configuration Files

### sbdk_config.json (Auto-Generated)
```json
{
  "project": "my_project",
  "target": "dev",
  "duckdb_path": "data/my_project.duckdb",
  "pipelines_path": "./pipelines",
  "dbt_path": "./dbt",
  "profiles_dir": "~/.dbt"
}
```

**Key Features:**
- **Local-first**: Database path is always within project directory
- **Self-contained**: No external dependencies or parent directory references
- **dbt Alignment**: Perfect integration between pipelines and transformations

### dbt profiles.yml (Auto-Configured)
```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: data/my_project.duckdb  # Local path, no ../data/ mismatches
      schema: main
```

**Benefits:**
- **Path Consistency**: Same database used by pipelines and dbt
- **Zero Setup**: Automatically configured during project initialization
- **Local Development**: Everything contained within project directory

## Advanced Configuration Options

### Data Volume Customization
```json
{
  "project": "analytics_pipeline",
  "data_volume": {
    "users": 50000,
    "events": 250000,
    "orders": 100000
  }
}
```

### Performance Optimization
```json
{
  "performance": {
    "batch_size": 10000,
    "parallel_processing": true,
    "memory_optimization": true
  }
}
```

### Quality Monitoring
```json
{
  "features": {
    "quality_monitoring": true,
    "unique_validation": true,
    "business_rules": true
  }
}
```

## Command Line Options

### Core Commands
```bash
# Initialize with guided setup
sbdk init my_project

# Execute complete pipeline
sbdk run

# Interactive mode with intelligent guidance
sbdk run --visual
sbdk interactive

# Development mode
sbdk run --watch

# Partial execution
sbdk run --pipelines-only
sbdk run --dbt-only

# System diagnostics
sbdk debug
```

### Advanced Options
```bash
# Custom configuration file
sbdk run --config custom_config.json

# Quiet mode
sbdk run --quiet

# Development server with webhooks
sbdk webhooks
```

## Local-First Architecture

### Database Paths
SBDK ensures all database paths are local and consistent:

```
✅ Correct (SBDK approach):
Pipeline creates: data/project.duckdb
dbt uses:        data/project.duckdb

❌ Wrong (traditional approach):
Pipeline creates: data/project.duckdb
dbt uses:        ../data/project.duckdb  # Path mismatch!
```

### Project Structure
```
my_project/
├── data/                    # Local database storage
│   └── my_project.duckdb   # Self-contained database
├── pipelines/              # DLT pipeline definitions
├── dbt/                    # dbt transformations
└── sbdk_config.json       # Local configuration
```

## Environment Variables

### Optional Settings
```bash
# Override default paths
export SBDK_DATA_PATH="custom/data/path"
export SBDK_DBT_PROFILES_DIR="~/.dbt"

# Development options
export SBDK_LOG_LEVEL="DEBUG"
export SBDK_DEV_MODE="true"
```

## First-Run Experience

### Intelligent Detection
SBDK automatically detects first-run scenarios:
- No database file exists
- Fresh project initialization
- Clean development environment

### Guided Flow Options
1. **Demo Setup** (Recommended):
   - Generates realistic synthetic data
   - Runs complete pipeline automatically
   - Creates working analytics environment
   - Perfect for learning and exploration

2. **Custom Setup** (Advanced):
   - Guides through pipeline customization
   - Helps configure data sources
   - Provides architectural guidance
   - Best for experienced developers

3. **Learn More**:
   - Project information and capabilities
   - Architecture overview
   - File structure explanation

## Quality Assurance

### TDD-Hardened Configuration
- **100% Test Coverage**: All configuration paths tested
- **Out-of-Box Validation**: Everything works immediately
- **Error Prevention**: Intelligent path validation
- **Self-Healing**: Automatic configuration repair

### Data Quality Features
- **Unique Email Generation**: Guaranteed unique emails in synthetic data
- **Referential Integrity**: Proper foreign key relationships
- **Business Rule Validation**: Realistic data constraints
- **Type Safety**: Consistent data types across pipeline

## Troubleshooting

### Common Issues
```bash
# Check system health
sbdk debug

# Verify configuration
cat sbdk_config.json

# Test database connection
duckdb data/project.duckdb ".tables"
```

### Configuration Reset
```bash
# Reinitialize project configuration
sbdk init --force my_project

# Clean and rebuild
rm -rf data/ && sbdk run
```

## Best Practices

### Development Workflow
1. **Start with Demo**: Run demo first to understand structure
2. **Gradual Customization**: Modify templates incrementally
3. **Use Watch Mode**: `sbdk run --watch` for rapid iteration
4. **Regular Testing**: Leverage comprehensive test suite

### Production Preparation
1. **Scale Data Volume**: Adjust data_volume settings
2. **Performance Tuning**: Enable optimization features
3. **Quality Monitoring**: Enable all validation features
4. **Documentation**: Maintain clear project documentation

## Integration Points

### dbt Integration
- **Automatic Profiles**: No manual dbt configuration required
- **Path Alignment**: Perfect database path consistency
- **Local Development**: Complete local testing capability

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Test SBDK Pipeline
  run: |
    sbdk init test_project
    cd test_project
    sbdk run
    sbdk debug
```

This configuration approach ensures SBDK works reliably out-of-the-box while providing powerful customization options for advanced users.