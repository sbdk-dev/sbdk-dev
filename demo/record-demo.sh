#!/bin/bash
# SBDK Demo Recording Script
# This script demonstrates SBDK's core features for documentation

set -e

echo "🎬 SBDK.dev Demo - Local-First Data Pipeline Sandbox"
echo ""
sleep 2

echo "📦 Step 1: Install SBDK"
echo "$ pip install sbdk-dev"
sleep 3

echo ""
echo "🏗️ Step 2: Initialize a new project"
echo "$ sbdk init demo_analytics"
sleep 2

# Actually run the command if you want real output
# sbdk init demo_analytics

echo ""
echo "📁 Step 3: Navigate to project"
echo "$ cd demo_analytics"
sleep 2

echo ""
echo "✅ Step 4: Check version"
echo "$ sbdk version"
sleep 2

# sbdk version

echo ""
echo "🚀 Step 5: Run the pipeline"
echo "$ sbdk run"
sleep 3

# This would actually run the pipeline
# cd demo_analytics && sbdk run

echo ""
echo "🔍 Step 6: Query the data"
echo "$ sbdk query"
sleep 2

# sbdk query

echo ""
echo "📊 Step 7: Run a SQL query"
echo '$ sbdk query "SELECT COUNT(*) as total, status FROM stg_users GROUP BY status"'
sleep 3

# sbdk query "SELECT COUNT(*) as total, status FROM stg_users GROUP BY status"

echo ""
echo "✨ Demo complete! Your local data pipeline is ready."
echo ""
echo "📖 Learn more: https://github.com/sbdk-dev/sbdk-dev"
sleep 2
