# 🚀 SBDK Demo Project

## 🌟 Experience the Intelligent Interactive Interface

This demo project showcases SBDK.dev's capabilities, including the **intelligent interactive interface** that provides guided flows, smart first-run detection, and out-of-the-box data pipeline experience.

## 🎯 Quick Start with Intelligent Interface

### Try the Interactive Demo
```bash
# Experience the intelligent guided interface
uv run sbdk run --visual

# Features demonstrated:
# ✓ Smart first-run detection with welcome flow
# ✓ Guided setup for demo vs custom projects
# ✓ Real-time progress tracking
# ✓ Context-aware suggestions
```

### Launch the Interactive Interface
```bash
# Start the intelligent interactive interface
uv run sbdk interactive

# Run with guided visual interface
uv run sbdk run --visual

# Development mode with file watching
uv run sbdk run --watch

# System diagnostics and health check
uv run sbdk debug
```

## 📁 Project Structure

```
demo_project/
├── 📊 data/                    # Local DuckDB database (self-contained)
│   └── demo_project.duckdb    # Complete analytics database
├── 🔄 pipelines/               # DLT data pipelines
│   ├── users.py               # 10K+ users with unique emails
│   ├── events.py              # 50K+ realistic behavioral events
│   └── orders.py              # 20K+ e-commerce orders
├── 📈 dbt/                     # dbt transformations
│   └── models/
│       ├── staging/           # Clean and standardize raw data
│       ├── intermediate/      # Business logic and joins
│       └── marts/            # Final analytics tables
├── 🌐 fastapi_server/          # Optional webhook server
├── ⚙️  sbdk_config.json        # Local-first configuration
├── 📋 USAGE_GUIDE.md          # Detailed usage instructions
└── 📋 OPTIMIZE_DATABASES.md   # Database optimization guide
```

## 🎯 What's Different: Intelligent Interface vs Traditional

### Traditional CLI Experience
```bash
# Traditional text-based output
uv run sbdk run
# Starting pipelines...
# Running users pipeline...
# Running events pipeline...
# Running orders pipeline...
# Starting dbt...
# ... (scrolling text output)
```

### Intelligent Interactive Experience
```bash
# Guided interface with smart detection
uv run sbdk run --visual
```

**First-Run Welcome Flow:**
```
🎉 Welcome to SBDK.dev!

This appears to be your first time running this project.
Let me help you get started!

What would you like to do?
[1] Run demo with sample data (Recommended for first-time users)
    • Generates 10K users, 50K events, 20K orders
    • Creates analytics dashboard with dbt
    • Perfect for learning and exploration

[2] Set up custom project (For experienced users)
    • Guide you through creating your own pipelines
    • Help configure your data sources
    • Customize dbt models for your use case

[3] Learn more about SBDK
    • View project information and capabilities
    • Understand the architecture
    • See what files are included

Choose an option (1-3):
```

## 🚀 Getting Started Options

### Option 1: Intelligent Interactive Experience (Recommended)
```bash
# Guided interface with smart first-run detection
uv run sbdk run --visual

# Full interactive CLI mode
uv run sbdk interactive

# Execute complete pipeline
uv run sbdk run
```

### Option 2: Development Mode
```bash
# Development mode with file watching
uv run sbdk run --watch

# Individual components
uv run sbdk run --pipelines-only
uv run sbdk run --dbt-only
```

## 🎮 Interactive Interface Features

### 🎯 **Smart Detection**
- **First-Run Detection**: Automatically detects new projects
- **Welcome Flow**: Guided setup for different user levels
- **Context Awareness**: Provides relevant suggestions
- **Progress Tracking**: Real-time pipeline execution feedback

### ⚡ **Out-of-Box Benefits**
- **Zero Configuration**: Works immediately after init
- **Local-First**: Everything contained within project
- **Self-Contained**: No external dependencies or path mismatches
- **TDD-Hardened**: Comprehensive test coverage ensures reliability

### 🎯 **Interactive Features**
- **Menu Navigation**: Clean, intuitive interface
- **Project Monitoring**: Real-time status and metrics
- **Database Access**: Direct DuckDB shell integration
- **System Diagnostics**: Built-in health checks

## 📋 Available Commands

### Interactive Commands
```bash
uv run sbdk interactive         # Full interactive CLI mode
uv run sbdk run --visual       # Guided visual interface
uv run sbdk run                # Execute complete pipeline
uv run sbdk run --watch        # Development mode with hot reload
uv run sbdk debug              # System diagnostics
```

### Pipeline Commands
```bash
uv run sbdk run --pipelines-only  # Data generation only
uv run sbdk run --dbt-only        # Transformations only
uv run sbdk run --quiet           # Suppress non-essential output
```

### Utility Commands
```bash
uv run sbdk version            # Version and system info
uv run sbdk webhooks           # Start webhook server
```

## 🎨 Interactive Menu Options

When running `sbdk interactive`, you get:

1. **Run full pipeline (DLT + dbt)** - Complete data processing
2. **Run pipelines only** - Generate synthetic data
3. **Run dbt only** - Execute transformations
4. **Watch mode** - Auto-reload on file changes
5. **View database** - Direct DuckDB shell access
6. **Project information** - Detailed project status
7. **Quit** - Exit interface

## 🎯 Use Cases

### 🔍 **Learning and Exploration**
```bash
# Start with intelligent guidance
uv run sbdk run --visual

# Choose option 1: Run demo with sample data
# System automatically generates realistic data and runs analytics
```

### 🛠️ **Development Workflow**
```bash
# Interactive development mode
uv run sbdk interactive

# Use menu option 4: Watch mode for rapid iteration
# Files automatically reload when changed
```

### 📊 **Data Analysis**
```bash
# Generate data and run transformations
uv run sbdk run

# Access database directly
uv run sbdk interactive
# Then choose option 5: View database
```

## 🆘 Help and Documentation

### Quick Help
- **In Interactive Mode**: Built-in help and guidance
- **System Status**: `uv run sbdk debug`
- **Configuration**: Check `sbdk_config.json`

### Documentation
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)**: Detailed usage instructions
- **[OPTIMIZE_DATABASES.md](OPTIMIZE_DATABASES.md)**: Database optimization
- **[Configuration Guide](../../docs/CONFIGURATION.md)**: Complete configuration reference
- **[API Reference](../../docs/API_REFERENCE.md)**: Full API documentation

### Troubleshooting
```bash
# Test system compatibility
uv run sbdk debug

# Check project health
uv run sbdk interactive
# Then check project information (option 6)

# Validate configuration
cat sbdk_config.json
```

## 🎉 Next Steps

1. **Try the intelligent interface**: `uv run sbdk run --visual`
2. **Explore interactive mode**: `uv run sbdk interactive`
3. **Access the database**: Use DuckDB shell option in interactive mode
4. **Read the detailed guides**: Check out the documentation files
5. **Customize your experience**: Edit pipelines and dbt models

## 📊 What You Get

### Generated Data
- **10,000+ Users**: Unique emails, realistic demographics
- **50,000+ Events**: Behavioral tracking data
- **20,000+ Orders**: E-commerce transaction data

### Analytics Tables
- **Staging Models**: Clean, standardized data
- **Intermediate Models**: Business logic and joins
- **Mart Models**: Final analytics-ready tables

### Database Features
- **Local DuckDB**: Lightning-fast local analytics
- **Self-Contained**: Everything within project directory
- **Query Ready**: Immediate access for analysis

---

**🚀 Welcome to the future of data pipeline development with SBDK's intelligent interface!**

The intelligent interactive interface transforms data pipeline development into a guided, intuitive experience that works perfectly out-of-the-box for users of all skill levels.