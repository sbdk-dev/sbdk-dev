# 🔧 Database Optimization Instructions

## Current Database Files (Confusing Names)
- `data/demo_project.duckdb` - Main database file
- `data/dev.duckdb` - Development database  
- `sample.duckdb` - Sample data database (in project root)

## Optimized Database Names (Clear Purpose)
- `data/starter-database.duckdb` - Clean starting point for new users
- `data/development-database.duckdb` - Development and testing database
- `data/sample-data-database.duckdb` - Pre-populated with example data

## Quick Optimization Commands

Run these commands from the demo_project directory:

```bash
# Create backups first
mkdir -p data/backups
cp data/demo_project.duckdb data/backups/backup_demo_project.duckdb
cp data/dev.duckdb data/backups/backup_dev.duckdb
cp sample.duckdb data/backups/backup_sample.duckdb

# Create optimized copies with clear names
cp data/demo_project.duckdb data/starter-database.duckdb
cp data/dev.duckdb data/development-database.duckdb
cp sample.duckdb data/sample-data-database.duckdb

# Update configuration to use starter database
# Edit sbdk_config.json and change:
# "duckdb_path": "data/starter-database.duckdb"
```

## Usage After Optimization

### For New Users (Recommended)
```bash
# Use the clean starter database
cp data/starter-database.duckdb data/my-project.duckdb
# Edit sbdk_config.json: "duckdb_path": "data/my-project.duckdb"
```

### For Exploring Examples
```bash
# Use the pre-populated sample database
cp data/sample-data-database.duckdb data/my-project.duckdb
# Edit sbdk_config.json: "duckdb_path": "data/my-project.duckdb"
```

### For Development
```bash
# Use the development database (already configured)
# sbdk_config.json: "duckdb_path": "data/development-database.duckdb"
```

## Benefits of Optimization

✅ **Clear Purpose**: Each database file has a clear, descriptive name
✅ **Better UX**: Users immediately understand which file to use
✅ **Safer**: Original files are backed up before changes
✅ **Organized**: All databases are in the data/ directory
✅ **Documented**: README.md explains each file's purpose

After running these commands, users will have a much clearer understanding of which database to use for their specific needs!