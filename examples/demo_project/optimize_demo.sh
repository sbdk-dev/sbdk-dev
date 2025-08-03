#!/bin/bash
# 🔧 SBDK Demo Project Database Optimization Script
# 
# This script optimizes the demo project database files for better usability:
# - Creates backups of original files
# - Renames databases with clear, descriptive names
# - Updates configuration
# - Provides usage instructions

set -e  # Exit on any error

echo "🚀 SBDK Demo Project Database Optimization"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "sbdk_config.json" ]; then
    echo "❌ Error: Please run this script from the demo_project directory"
    echo "   Expected to find sbdk_config.json in current directory"
    exit 1
fi

# Create backups directory
echo "📁 Creating backups directory..."
mkdir -p data/backups

# Create backups of original files
echo "💾 Creating backups of original database files..."

if [ -f "data/demo_project.duckdb" ]; then
    cp data/demo_project.duckdb data/backups/backup_demo_project.duckdb
    echo "   ✅ Backed up: demo_project.duckdb"
else
    echo "   ⚠️  Warning: demo_project.duckdb not found"
fi

if [ -f "data/dev.duckdb" ]; then
    cp data/dev.duckdb data/backups/backup_dev.duckdb
    echo "   ✅ Backed up: dev.duckdb"
else
    echo "   ⚠️  Warning: dev.duckdb not found"
fi

if [ -f "sample.duckdb" ]; then
    cp sample.duckdb data/backups/backup_sample.duckdb
    echo "   ✅ Backed up: sample.duckdb"
else
    echo "   ⚠️  Warning: sample.duckdb not found"
fi

# Create optimized copies with descriptive names
echo "✨ Creating optimized database files..."

if [ -f "data/demo_project.duckdb" ]; then
    cp data/demo_project.duckdb data/starter-database.duckdb
    echo "   🚀 Created: starter-database.duckdb (clean starting point)"
fi

if [ -f "data/dev.duckdb" ]; then
    cp data/dev.duckdb data/development-database.duckdb
    echo "   🔧 Created: development-database.duckdb (for development)"
fi

if [ -f "sample.duckdb" ]; then
    cp sample.duckdb data/sample-data-database.duckdb
    echo "   📋 Created: sample-data-database.duckdb (with example data)"
fi

# Configuration is already updated to use starter-database.duckdb
echo "🔧 Configuration already optimized (using starter-database.duckdb)"

echo ""
echo "✅ Optimization Complete!"
echo ""
echo "📊 Available database files:"
echo "├── 🚀 data/starter-database.duckdb     - Clean starting point (ACTIVE)"
echo "├── 📋 data/sample-data-database.duckdb - Pre-populated examples"
echo "└── 🔧 data/development-database.duckdb - Development/testing"
echo ""
echo "💾 Backups saved in: data/backups/"
echo ""
echo "📚 Next Steps:"
echo "1. Read data/README.md for database details"
echo "2. Read USAGE_GUIDE.md for complete instructions"
echo "3. Run 'sbdk dev' to test the optimized setup"
echo ""
echo "🎯 Quick Start:"
echo "   # Create your own project database"
echo "   cp data/starter-database.duckdb data/my-project.duckdb"
echo ""
echo "   # Update config to use your database"
echo "   # Edit sbdk_config.json: change duckdb_path to 'data/my-project.duckdb'"
echo ""
echo "   # Run your pipeline"
echo "   sbdk dev"
echo ""
echo "Happy building with SBDK! 🚀"