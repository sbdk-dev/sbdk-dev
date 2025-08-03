# SBDK Development Server Guide

## Overview

The SBDK development server provides a clean, interactive CLI for monitoring and rebuilding your data pipelines as you develop.

## Starting the Server

```bash
cd your_project
sbdk start
```

Or with options:
```bash
sbdk start --no-initial-run  # Skip initial pipeline run
sbdk start --watch src/ --watch scripts/  # Custom watch paths
```

## Interactive Commands

Once the server is running, you have full control:

| Command | Description |
|---------|-------------|
| `s` | Show server status and recent file changes |
| `r` | Run pipeline manually |
| `a` | Toggle auto-run mode (ON/OFF) |
| `l` | Show recent pipeline logs |
| `c` | Clear file change history |
| `h` | Show help menu |
| `q` | Quit the server gracefully |

## Features

### Auto-run Mode
- **ON**: Pipeline runs automatically when files change
- **OFF**: Changes are detected but you control when to run

### Smart File Detection
- Monitors `.py`, `.sql`, `.yml`, `.yaml`, `.json` files
- 3-second debounce prevents excessive runs
- Shows what type of file changed (Pipeline, dbt, Config, Code)

### Clean Output
- Pipeline output is captured and viewable with `l`
- No overlapping or garbled text
- Clear status indicators (🟢 Success, 🟡 Running, 🔴 Failed)

### Error Handling
- Shows last error in status display
- Full error details in logs
- Graceful recovery options

## Example Session

```
🚀 Starting SBDK Development Server
Database: data/my_project.duckdb

Running initial pipeline...
✅ Initial pipeline completed successfully
👀 Watching: pipelines
👀 Watching: dbt/models

✅ Server started!
Type 'h' for help, 'q' to quit

SBDK> s

============================================================
🚀 SBDK Development Server Status
============================================================
Time: 14:30:45
Auto-run: ON
Watching: pipelines, dbt/models
Pipeline: 🟢 Success
Last run: 14:28:32
Success rate: 5/6 (83.3%)

Recent changes:
  [14:30:15] Pipeline: events.py
============================================================

SBDK> 
📁 1 file(s) changed
🔄 Auto-running pipeline...
✅ Pipeline completed successfully

SBDK> l

Recent Pipeline Output (last 10 entries):
------------------------------------------------------------
[14:31:02] 🏃‍♂️ Running users pipeline...
[14:31:02] 📊 Generated 10000 user records
[14:31:03] ✅ Users pipeline completed successfully!
[14:31:03] 🏃‍♂️ Running events pipeline...
[14:31:04] 📊 Generated 50000 event records
[14:31:04] ✅ Events pipeline completed successfully!
------------------------------------------------------------

SBDK> q

🛑 Shutting down server...
✅ Server stopped
```

## Tips

- Use `s` frequently to check server health
- Toggle auto-run with `a` based on your workflow
- View logs with `l` to debug pipeline issues
- The server captures all output - nothing is lost