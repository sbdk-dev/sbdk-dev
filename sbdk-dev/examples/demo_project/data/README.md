# 📊 Demo Project Database Files

This directory contains the database files for the SBDK demo project, optimized for clarity and ease of use.

## 📁 Database Files

### 🚀 `starter-database.duckdb` 
**Purpose**: Clean, empty database for new users to start with
- Contains only the schema/tables structure
- No sample data
- Perfect for testing your own data pipelines
- **Use when**: You want to start fresh with your own data

### 📋 `sample-data-database.duckdb`
**Purpose**: Pre-populated database with realistic sample data
- Contains example users, orders, and events data
- Demonstrates working DBT transformations
- Shows expected data patterns and relationships
- **Use when**: You want to explore the system with example data

### 🔧 `development-database.duckdb`
**Purpose**: Development and testing database
- Used during active development
- May contain work-in-progress data
- Updated by DBT runs and pipeline tests
- **Use when**: You're actively developing/testing

## 🎯 Quick Start Guide

### Option 1: Start Fresh (Recommended for New Users)
```bash
# Copy the starter database
cp data/starter-database.duckdb data/my-project.duckdb

# Update config to use your database
# Edit sbdk_config.json: change "duckdb_path" to "data/my-project.duckdb"

# Run your pipelines
sbdk dev
```

### Option 2: Explore with Sample Data
```bash
# Copy the sample database
cp data/sample-data-database.duckdb data/my-project.duckdb

# Run DBT to see transformations in action
cd dbt && dbt run && dbt test
```

### Option 3: Use Development Database
```bash
# The development database is already configured
# Just run the project as-is
sbdk dev
```

## 📊 Database Schema

All databases contain these tables:

### Raw Data Tables (Sources)
- `users` - User information and profiles
- `orders` - Purchase orders and transactions  
- `events` - User activity events and interactions

### Transformed Tables (DBT Models)
- `stg_users` - Cleaned and standardized user data
- `stg_orders` - Processed order information
- `stg_events` - Structured event data
- `int_user_activity` - Intermediate user activity metrics
- `user_metrics` - Final user analytics and KPIs

## 🔧 Configuration

The main database file is configured in `../sbdk_config.json`:

```json
{
  "duckdb_path": "data/starter-database.duckdb"
}
```

Change the `duckdb_path` to use a different database file.

## 💡 Tips

1. **Always backup** your database before major changes
2. **Use descriptive names** when creating your own database files
3. **Check file sizes** - databases grow with data, plan accordingly
4. **Run DBT tests** regularly to ensure data quality

## 🆘 Troubleshooting

### Database File Locked
```bash
# Make sure no other processes are using the database
# Check with: lsof data/your-database.duckdb
```

### Corrupted Database
```bash
# Start fresh with the starter database
cp data/starter-database.duckdb data/your-database.duckdb
```

### Missing Tables
```bash
# Re-run the pipelines to recreate tables
sbdk dev
```

---

**Need help?** Check the main project README.md or the comprehensive documentation in the docs/ folder.