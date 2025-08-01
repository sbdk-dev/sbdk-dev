# 🚀 SBDK Demo Project - Usage Guide

## 📋 Quick Start Options

### Option 1: Complete Beginner (Recommended) 
**Goal**: Learn SBDK with clear, empty database

1. **Optimize database names first** (run once):
   ```bash
   # Create backups and optimized copies
   mkdir -p data/backups
   cp data/demo_project.duckdb data/backups/backup_demo_project.duckdb
   cp data/dev.duckdb data/backups/backup_dev.duckdb
   cp sample.duckdb data/backups/backup_sample.duckdb
   
   # Create clear, descriptive names
   cp data/demo_project.duckdb data/starter-database.duckdb
   cp data/dev.duckdb data/development-database.duckdb
   cp sample.duckdb data/sample-data-database.duckdb
   ```

2. **Start with clean database**:
   ```bash
   # Create your own project database
   cp data/starter-database.duckdb data/my-first-project.duckdb
   
   # Update config to use your database
   # Edit sbdk_config.json: change "duckdb_path" to "data/my-first-project.duckdb"
   ```

3. **Run your first pipeline**:
   ```bash
   sbdk dev
   ```

### Option 2: Explore with Sample Data
**Goal**: See SBDK in action with realistic example data

1. **Use sample database**:
   ```bash
   # After running optimization commands above
   cp data/sample-data-database.duckdb data/my-exploration.duckdb
   
   # Update config
   # Edit sbdk_config.json: change "duckdb_path" to "data/my-exploration.duckdb"
   ```

2. **Explore the data**:
   ```bash
   # Run DBT transformations
   cd dbt
   dbt run
   dbt test
   
   # Check results
   dbt docs generate
   dbt docs serve
   ```

### Option 3: Advanced Development
**Goal**: Modify and extend the demo project

1. **Use development database**:
   ```bash
   # After optimization, config is already set to:
   # "duckdb_path": "data/starter-database.duckdb"
   
   # Or switch to development database:
   # Edit sbdk_config.json: change to "data/development-database.duckdb"
   ```

2. **Develop and test**:
   ```bash
   # Make changes to pipelines/
   # Edit models in dbt/models/
   
   # Test your changes
   sbdk dev
   cd dbt && dbt test
   ```

## 📊 Understanding the Databases

After optimization, you'll have:

| Database File | Purpose | When to Use |
|---------------|---------|-------------|
| `starter-database.duckdb` | Clean, minimal schema | Starting fresh, learning basics |
| `sample-data-database.duckdb` | Pre-populated examples | Exploring features, seeing results |
| `development-database.duckdb` | Work-in-progress | Active development, testing |

## 🔧 Configuration Files

### `sbdk_config.json` - Main Configuration
```json
{
  "project": "demo_project",
  "target": "dev", 
  "duckdb_path": "data/starter-database.duckdb",  // Change this!
  "pipelines_path": "./pipelines",
  "dbt_path": "./dbt",
  "profiles_dir": "~/.dbt"
}
```

**Key Setting**: Change `duckdb_path` to switch between databases:
- `"data/starter-database.duckdb"` - Clean start
- `"data/sample-data-database.duckdb"` - With examples  
- `"data/development-database.duckdb"` - Development work
- `"data/my-custom-name.duckdb"` - Your own project

## 🎯 Common Workflows

### Learning Workflow
```bash
1. cp data/starter-database.duckdb data/learning.duckdb
2. Edit sbdk_config.json -> "duckdb_path": "data/learning.duckdb"
3. sbdk dev  # Run pipelines
4. cd dbt && dbt run && dbt test  # Run transformations
5. Examine data, make changes, repeat
```

### Development Workflow  
```bash
1. cp data/sample-data-database.duckdb data/feature-branch.duckdb
2. Edit sbdk_config.json -> "duckdb_path": "data/feature-branch.duckdb"
3. Modify pipelines/ and dbt/models/
4. sbdk dev  # Test changes
5. dbt test  # Validate transformations
6. Commit when satisfied
```

### Production Workflow
```bash
1. Use starter-database.duckdb as base
2. Add production data via pipelines
3. Run full DBT suite: dbt run && dbt test
4. Monitor data quality
5. Deploy with confidence
```

## 🆘 Troubleshooting

### Database File Issues
```bash
# Database locked?
lsof data/your-database.duckdb

# Corrupted database?
cp data/backups/backup_demo_project.duckdb data/recovery.duckdb

# Fresh start needed?
cp data/starter-database.duckdb data/fresh-start.duckdb
```

### Configuration Issues
```bash
# Wrong database path?
cat sbdk_config.json  # Check duckdb_path

# DBT can't find models?
cd dbt && dbt debug  # Check connections
```

### Pipeline Issues
```bash
# Pipeline failing?
sbdk dev --verbose  # See detailed logs

# DBT tests failing?
cd dbt && dbt test --select failing_model
```

## 📚 Next Steps

1. **Read the data README**: `data/README.md` - Detailed database info
2. **Explore models**: `dbt/models/` - See transformations
3. **Check pipelines**: `pipelines/` - Understand data flow  
4. **Run tests**: `dbt test` - Validate everything works
5. **Build your own**: Create custom databases and models

## 💡 Pro Tips

- **Always backup** before making changes: `cp database.duckdb database-backup.duckdb`
- **Use descriptive names** for your project databases
- **Run tests frequently**: `dbt test` catches issues early
- **Check logs** when things fail: `dbt/logs/dbt.log`
- **Start simple** then add complexity gradually

---

**Happy Building with SBDK!** 🚀

For more help, check the main project documentation or create an issue on GitHub.