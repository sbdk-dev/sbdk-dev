# 🚀 SBDK Demo Project

## 🌟 Experience the Modern Visual CLI

This demo project showcases SBDK.dev's capabilities, including the **new Visual CLI interface** that provides a modern, React-like terminal experience with in-place updates and smooth animations.

## 🎨 Quick Start with Visual CLI

### Try the Interactive Demo
```bash
# Experience the Visual CLI features first
uv run sbdk visual demo

# Features demonstrated:
# ✓ In-place text updates (no scrolling/appending)
# ✓ Professional headers with live timestamps
# ✓ Smooth progress bars and animations
# ✓ Interactive keyboard controls
```

### Launch the Main Interface
```bash
# Start the modern visual interface
uv run sbdk visual start

# Interactive dashboard with real-time metrics
uv run sbdk visual dashboard --watch

# Visual pipeline execution
uv run sbdk visual pipeline

# DBT operations with progress tracking
uv run sbdk visual dbt
```

## 📁 Project Structure

```
demo_project/
├── 📊 data/                    # Database files (optimized names)
│   ├── starter-database.duckdb         # Clean starting point
│   ├── development-database.duckdb     # Development work
│   ├── sample-data-database.duckdb     # Pre-populated examples
│   └── backups/                        # Backup copies
├── 🔄 pipelines/               # DLT data pipelines
│   ├── users.py               # User data generation
│   ├── events.py              # Event tracking data
│   └── orders.py              # E-commerce orders
├── 📈 dbt/                     # dbt transformations
│   └── models/
│       ├── staging/           # Clean and standardize
│       ├── intermediate/      # Business logic
│       └── marts/            # Final analytical models
├── 🌐 fastapi_server/          # Optional webhook server
├── ⚙️  sbdk_config.json        # Project configuration
├── 📋 USAGE_GUIDE.md          # Detailed usage instructions
└── 📋 OPTIMIZE_DATABASES.md   # Database optimization guide
```

## 🎯 What's Different: Visual CLI vs Traditional

### Traditional CLI Experience
```bash
# Traditional text-based output
uv run sbdk dev
# [2025-01-01 10:00:00] Starting pipelines...
# [2025-01-01 10:00:05] Running users pipeline...
# [2025-01-01 10:00:10] Running events pipeline...
# [2025-01-01 10:00:15] Running orders pipeline...
# [2025-01-01 10:00:20] Starting dbt...
# ... (scrolling text output)
```

### Visual CLI Experience
```bash
# Modern visual interface with components
uv run sbdk visual start
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🎨 SBDK Analytics Platform                    [Processing]        14:30:25   │
└──────────────────────────────────────────────────────────────────────────────┘

┌───────────────────[ Pipeline Progress ]─────────────────────┐
│ Users Pipeline:   [████████████████████████████████████] 100%│
│ Events Pipeline:  [██████████████████░░░░░░░░░░░░░░░░░░] 65% │
│ Orders Pipeline:  [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 30% │
└─────────────────────────────────────────────────────────────┘

⠋ Processing events data...

┌──────────────────────────────────────────────────────────────────────────────┐
│ Press 'q' to quit, 'r' to refresh                          Visual CLI Active │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started Options

### Option 1: Visual CLI Experience (Recommended)
```bash
# Modern interface with real-time monitoring
uv run sbdk visual start

# Interactive dashboard
uv run sbdk visual dashboard --watch

# Visual pipeline execution
uv run sbdk visual pipeline
```

### Option 2: Traditional CLI
```bash
# Classic command-line interface
uv run sbdk dev

# Individual components
uv run sbdk start
cd dbt && dbt run && dbt test
```

## 🎮 Visual CLI Features

### 🎨 **Modern Interface Components**
- **Headers**: Live status, timestamps, project context
- **Progress Bars**: Smooth animations, multiple styles
- **Spinners**: Loading indicators with various animations
- **Panels**: Information display with Unicode borders
- **Footers**: Help text and keyboard shortcuts

### ⚡ **Performance Benefits**
- **Double-Buffered Rendering**: Zero screen flicker
- **In-Place Updates**: Text updates in same position
- **30-60 FPS**: Smooth animations and transitions
- **Minimal CPU**: Optimized for terminal efficiency

### 🎯 **Interactive Features**
- **Keyboard Navigation**: Intuitive controls
- **Real-Time Metrics**: Live project monitoring
- **Error Visualization**: Clear error display
- **Progress Tracking**: Visual feedback for operations

## 📋 Available Commands

### Visual CLI Commands
```bash
uv run sbdk visual start       # Main interface
uv run sbdk visual demo        # Feature demonstration
uv run sbdk visual dashboard   # Project monitoring
uv run sbdk visual dbt         # DBT with progress
uv run sbdk visual pipeline    # Pipeline execution
```

### Traditional Commands
```bash
uv run sbdk dev               # Complete pipeline
uv run sbdk start             # Development server
uv run sbdk webhooks          # Webhook listener
uv run sbdk debug             # System diagnostics
```

## 🎨 Customization

### Visual CLI Configuration
Edit `sbdk_config.json` to customize the interface:

```json
{
  "visual_cli": {
    "enabled": true,
    "fps": 30,
    "theme": "default",
    "features": {
      "animations": true,
      "unicode": "auto",
      "colors": "auto"
    }
  }
}
```

### Performance Tuning
```bash
# High refresh rate for powerful systems
uv run sbdk visual start --fps 60

# Battery saving mode
uv run sbdk visual start --fps 15
```

## 🎯 Use Cases

### 🔍 **Learning and Exploration**
```bash
# Start with the demo to understand features
uv run sbdk visual demo

# Explore with the main interface
uv run sbdk visual start

# Monitor your project in real-time
uv run sbdk visual dashboard --watch
```

### 🛠️ **Development Workflow**
```bash
# Visual pipeline development
uv run sbdk visual pipeline

# DBT model development with progress
uv run sbdk visual dbt

# Real-time project monitoring
uv run sbdk visual dashboard --watch
```

### 📊 **Production Monitoring**
```bash
# Dashboard for production monitoring
uv run sbdk visual dashboard

# Visual validation of data pipelines
uv run sbdk visual pipeline --production

# DBT deployment with visual feedback
uv run sbdk visual dbt --target prod
```

## 🆘 Help and Documentation

### Quick Help
- **In Visual CLI**: Press `h` or `?` for help
- **Quit Interface**: Press `q` or `Ctrl+C`
- **Refresh Data**: Press `r`

### Documentation
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: Detailed usage instructions
- **[OPTIMIZE_DATABASES.md](OPTIMIZE_DATABASES.md)**: Database optimization
- **[Visual CLI Guide](../../docs/VISUAL_CLI_GUIDE.md)**: Complete Visual CLI documentation

### Troubleshooting
```bash
# Test Visual CLI compatibility
uv run sbdk visual demo

# Check system status
uv run sbdk debug

# Validate configuration
uv run sbdk debug --show-config
```

## 🎉 Next Steps

1. **Try the Visual CLI demo**: `uv run sbdk visual demo`
2. **Explore the main interface**: `uv run sbdk visual start`
3. **Monitor your project**: `uv run sbdk visual dashboard --watch`
4. **Read the detailed guides**: Check out the documentation files
5. **Customize your experience**: Edit `sbdk_config.json`

---

**🚀 Welcome to the future of data pipeline development with SBDK's Visual CLI!**

The Visual CLI transforms the traditional terminal experience into a modern, interactive interface that makes data pipeline development both powerful and enjoyable.