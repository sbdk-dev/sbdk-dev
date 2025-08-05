# Video 1: 30-Second Setup Magic - Automated Script

## 🎯 Video Overview
- **Duration**: 30 seconds
- **Focus**: Lightning-fast installation and setup
- **Key Message**: "Data pipelines in seconds, not hours"

## 📋 Pre-Recording Setup Commands
```bash
# Clean environment for recording
cd ~/Desktop
rm -rf demo-recording
mkdir demo-recording && cd demo-recording
clear
```

## 🎬 Recording Commands (Automated)

```bash
# [0-4s] Problem introduction (voiceover plays during this)
echo "🚀 Traditional data pipeline setup takes hours..."
sleep 1
echo "⚡ With SBDK.dev, it takes 30 seconds. Watch:"

# [4-8s] Lightning-fast installation
echo ""
echo "💨 Installing SBDK.dev with uv (11x faster)..."
uv pip install sbdk-dev

# [8-12s] Instant project creation
echo ""
echo "📦 Creating new data pipeline project..."
sbdk init demo-pipeline

# [12-15s] Enter and explore
cd demo-pipeline
echo "📁 Generated project structure:"
ls -la

# [15-22s] Complete pipeline execution
echo ""
echo "⚡ Running complete data pipeline..."
sbdk run

# [22-27s] Show real results
echo ""
echo "📊 Real data generated:"
echo "SELECT COUNT(*) as users FROM users;" | duckdb data/demo.duckdb
echo "SELECT COUNT(*) as events FROM events;" | duckdb data/demo.duckdb

# [27-30s] Final impact message
echo ""
echo "✅ Complete modern data stack in 30 seconds!"
echo "🏠 100% local • $0 cost • Production ready"
```

## 🎙️ Voiceover Script (Record separately)
```
[0-3s] "Building data pipelines used to take hours of setup..."
[4-8s] "With SBDK.dev, it takes just 30 seconds."
[9-15s] "Watch: uv install, sbdk init, and you're running."
[16-25s] "Real data, real database, real dbt transformations."
[26-30s] "SBDK.dev - Modern data pipelines, zero complexity."
```

## 🎨 Visual Highlights
- **[4-8s]**: Emphasize speed of uv installation (11x faster)
- **[12-15s]**: Quick glimpse of generated project structure  
- **[15-22s]**: Beautiful progress bars and rich terminal output
- **[22-27s]**: Actual data counts proving it works
- **[27-30s]**: Strong value proposition display

## ⚙️ Technical Notes
- **Terminal**: Dark theme (#1a1a1a) with teal accents (#00D4AA)
- **Font**: JetBrains Mono, 16pt minimum
- **Resolution**: 1920x1080 for crisp text
- **Timing**: Each command block includes precise timing
- **Error Handling**: Commands tested to run reliably

## 🎯 Key Metrics to Highlight
- **11x faster** installation with uv
- **30 seconds** total setup time
- **480x faster** than traditional data stacks
- **100% local** - no cloud dependencies
- **$0 monthly cost** vs $200-2000+ alternatives