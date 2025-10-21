# 🎬 SBDK Demo Recording Guide

This directory contains scripts and instructions for creating demo GIFs and videos for the README.

## Quick Start - Create a Demo GIF

### Option 1: Using asciinema + agg (Recommended)

```bash
# Install tools
brew install asciinema agg

# Record the demo
asciinema rec demo.cast

# Run commands manually during recording:
pip install sbdk-dev
sbdk init demo_analytics
cd demo_analytics
sbdk run
sbdk query
sbdk query "SELECT * FROM stg_users LIMIT 5"
exit  # Stop recording

# Convert to GIF
agg demo.cast demo.gif

# Copy to README assets
mkdir -p ../docs/images
cp demo.gif ../docs/images/sbdk-demo.gif
```

### Option 2: Using VHS (Automated)

```bash
# Install VHS
brew install vhs

# Create automated recording script
cat > demo.tape <<'EOF'
Output demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Dracula"

Type "pip install sbdk-dev"
Sleep 1s
Enter
Sleep 3s

Type "sbdk init demo_analytics"
Sleep 1s
Enter
Sleep 2s

Type "cd demo_analytics"
Sleep 500ms
Enter

Type "sbdk run"
Sleep 1s
Enter
Sleep 5s

Type "sbdk query"
Sleep 1s
Enter
Sleep 2s

Type 'sbdk query "SELECT * FROM stg_users LIMIT 5"'
Sleep 1s
Enter
Sleep 2s

Sleep 3s
EOF

# Generate GIF
vhs demo.tape
```

### Option 3: Using Terminalizer

```bash
# Install
npm install -g terminalizer

# Record
terminalizer record demo

# Render to GIF
terminalizer render demo
```

## Demo Scripts

### `record-demo.sh`
Automated script that shows SBDK commands with delays. Run this while recording with asciinema or screen capture.

```bash
chmod +x record-demo.sh
./record-demo.sh
```

## Recommended GIF Specifications

- **Width**: 1000-1200px
- **FPS**: 10-15
- **Duration**: 30-60 seconds
- **Theme**: Dracula or Material (for visibility)
- **Show**: Installation → Init → Run → Query

## Adding GIF to README

Once you have `sbdk-demo.gif`:

1. Create images directory:
   ```bash
   mkdir -p docs/images
   ```

2. Copy GIF:
   ```bash
   cp demo.gif docs/images/sbdk-demo.gif
   ```

3. Add to README.md:
   ```markdown
   ## 🎥 See It In Action

   ![SBDK Demo](docs/images/sbdk-demo.gif)

   *From zero to data pipeline in 30 seconds*
   ```

## Tips for Great Demos

1. **Clear terminal**: `clear` before starting
2. **Proper sizing**: Use a readable font size (14-16pt)
3. **Pause between commands**: Let viewers read
4. **Show output**: Let commands complete before next step
5. **Keep it short**: 30-60 seconds max
6. **Highlight key features**: init → run → query

## Automated Demo (Full Pipeline)

For a realistic demo showing actual data:

```bash
#!/bin/bash
# Create temporary demo
cd /tmp
sbdk init demo_live
cd demo_live

# Run pipeline (generates real data)
sbdk run

# Show tables
echo "📊 Available tables:"
sbdk query

# Query users
echo "👥 Sample users:"
sbdk query "SELECT * FROM stg_users LIMIT 5"

# Show aggregation
echo "📈 User status summary:"
sbdk query "SELECT status, COUNT(*) as count FROM stg_users GROUP BY status"

# Cleanup
cd /tmp
rm -rf demo_live
```

## Example VHS Configuration

Create `sbdk-demo.tape`:

```tape
Output ../docs/images/sbdk-demo.gif

Set FontSize 16
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# Setup
Type "# SBDK.dev - Local-First Data Pipeline Sandbox"
Sleep 2s
Enter
Enter

Type "pip install sbdk-dev"
Enter
Sleep 3s

# Initialize
Type "sbdk init my_analytics"
Enter
Sleep 2s

Type "cd my_analytics"
Enter
Sleep 1s

# Show help
Type "sbdk --help"
Enter
Sleep 3s

# Run pipeline
Type "sbdk run"
Enter
Sleep 8s

# Query data
Type "sbdk query"
Enter
Sleep 3s

# SQL query
Type 'sbdk query "SELECT * FROM stg_users LIMIT 5"'
Enter
Sleep 3s

# Finish
Type "# ✨ Your local data pipeline is ready!"
Sleep 3s
