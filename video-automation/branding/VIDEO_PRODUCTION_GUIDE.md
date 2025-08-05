# 🎬 SBDK.dev Video Production Guide

## 📋 Complete Recording Setup

### Required Software
- **Screen Recording**: OBS Studio or Screenflow
- **Terminal**: iTerm2 or Terminal with clean theme
- **Code Editor**: VS Code with dark theme
- **Voice Recording**: Audacity or built-in recording
- **Video Editing**: DaVinci Resolve (free) or Final Cut Pro

### Terminal Setup for Recording
```bash
# Clean, professional terminal setup
export PS1="\[\033[32m\]\u@\h:\[\033[34m\]\w\[\033[0m\]$ "

# Set terminal to 120x30 for readability
resize -s 30 120

# Use clear, large font (14pt minimum)
# Dark background, high contrast text
```

### Environment Preparation
```bash
# Clean slate for each recording
cd ~/Desktop && rm -rf demo-*
mkdir sbdk-recording && cd sbdk-recording

# Ensure uv is installed and working
uv --version

# Clear terminal history
history -c && clear
```

---

## 🎯 Video 1: "30-Second Setup Magic"

### Pre-Recording Setup
```bash
# Terminal window: 1920x1080, centered
# Font: JetBrains Mono, 16pt
# Theme: Dark background, teal accents matching brand

# Start with empty directory
cd ~/Desktop/demo-recording
```

### Recording Script (30 seconds)
```bash
# [0-3s] Show problem - traditional setup (quick montage)
# Screen shows: Docker compose files, cloud dashboards, complex configs

# [4-8s] "With SBDK.dev, it takes 30 seconds"
uv pip install sbdk-dev                    # [4-6s] - Show fast installation
echo "✅ Installation complete"            # [6s]

# [9-15s] "Watch: uv pip install, sbdk init, and you're running"  
sbdk init demo-pipeline                    # [7-9s] - Show project creation
cd demo-pipeline                           # [9s]
ls -la                                     # [10s] - Show generated structure

# [16-25s] "Real data, real database, real dbt transformations"
sbdk run                                   # [11-20s] - Show full pipeline
# Display should show:
# - Progress bars for data generation
# - DLT pipeline execution
# - DuckDB database creation
# - dbt model runs

# [21-25s] Quick glimpse of results
echo "SELECT COUNT(*) FROM users;" | duckdb data/demo.duckdb    # [21-23s]
echo "SELECT COUNT(*) FROM events;" | duckdb data/demo.duckdb   # [23-25s]

# [26-30s] End screen with logo and CTA
echo "🚀 SBDK.dev - Modern data pipelines, zero complexity"     # [26-30s]
```

### Voiceover Script
```
[0-3s] "Building data pipelines used to take hours of setup..."
[4-8s] "With SBDK.dev, it takes just 30 seconds."
[9-15s] "Watch: uv install, sbdk init, and you're running."
[16-25s] "Real data, real database, real dbt transformations."
[26-30s] "SBDK.dev - Modern data pipelines, zero complexity."
```

### Visual Cues
- [4-6s]: Highlight speed of uv installation
- [10s]: Zoom in on generated project structure  
- [15-20s]: Show beautiful progress bars and terminal output
- [21-25s]: Display actual data counts proving it works
- [26-30s]: Clean end screen with logo and install command

---

## 🎯 Video 2: "Visual Mode Magic"

### Recording Script
```bash
# [0-4s] Show traditional chaos - multiple terminal windows
# Quick montage: logs, errors, switching windows

# [5-7s] "SBDK's visual mode puts everything in one place"
sbdk visual                               # Launch visual interface

# [8-18s] Navigate through TUI
# Show different screens:
# - Dashboard with pipeline status
# - Real-time logs panel  
# - Configuration view
# - Help system

# [19-25s] "See your data pipeline come alive visually"
# Trigger pipeline run from within visual mode
# Show real-time progress updates
```

### Voiceover Script
```
[0-4s] "Tired of switching between terminals and docs?"
[5-10s] "SBDK's visual mode puts everything in one place."
[11-18s] "Real-time monitoring, interactive controls, beautiful UI."
[19-25s] "See your data pipeline come alive visually."
[26-30s] "Visual development mode - it's like magic."
```

---

## 🎯 Video 3: "Dev Mode Power"

### Recording Script  
```bash
# [0-4s] Show traditional slow cycle
# Edit file → save → restart → wait → check result

# [5-7s] Launch dev mode
sbdk dev --watch

# [8-12s] Edit pipeline file in VS Code (split screen)
# Make visible change to user count: 1000 → 5000

# [13-18s] Show automatic detection and re-execution
# Terminal shows: "File changed: pipelines/users.py"
# "Re-running pipeline..."
# Progress bars appear

# [19-25s] Show changed results instantly
echo "SELECT COUNT(*) FROM users;" | duckdb data/demo.duckdb
# Shows 5000 instead of 1000
```

### Voiceover Script
```
[0-4s] "Hot reload for data pipelines? Yes, really."
[5-10s] "Edit your pipeline, save, and see instant results."
[11-18s] "No rebuilding, no restarting, just pure flow state."
[19-25s] "Development mode that actually understands data."
[26-30s] "SBDK dev mode - where data meets developer experience."
```

---

## 🎯 Video 4: "Data Generation Demo"

### Recording Script
```bash
# [0-4s] Show CSV files, manual data creation problems

# [5-7s] Start fresh pipeline
sbdk init data-demo && cd data-demo

# [8-12s] Run pipeline, focus on data generation
sbdk run --pipelines-only

# [13-18s] Show data relationships with SQL
echo "
SELECT 
  u.name,
  COUNT(e.id) as events,
  COUNT(o.id) as orders
FROM users u
LEFT JOIN events e ON u.id = e.user_id  
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name
LIMIT 5;
" | duckdb data/demo.duckdb

# [19-25s] Show scale and quality
echo "SELECT COUNT(DISTINCT email) FROM users;" | duckdb data/demo.duckdb
echo "SELECT COUNT(*) FROM events WHERE user_id IS NOT NULL;" | duckdb data/demo.duckdb
```

### Voiceover Script
```
[0-4s] "Need realistic test data for your pipeline?"
[5-10s] "SBDK generates it automatically with relationships."
[11-18s] "10,000 users, 50,000 events, all connected perfectly."
[19-25s] "From fake data to real insights in seconds."
[26-30s] "Smart data generation - no more CSV hunting."
```

---

## 🎬 Production Guidelines

### Visual Consistency
- **Resolution**: 1920x1080 (1080p)
- **Frame Rate**: 30fps  
- **Terminal Font**: JetBrains Mono, 16pt minimum
- **Color Scheme**: Dark background (#1a1a1a), teal highlights (#00D4AA)
- **Logo Placement**: Bottom right corner, 10% opacity during demo

### Audio Guidelines
- **Voice**: Clear, enthusiastic but professional
- **Pace**: 160-180 words per minute
- **Background Music**: Subtle tech/productivity track at 15% volume
- **Sound Effects**: Terminal clicks, success chimes for completions

### Recording Settings
```bash
# OBS Studio Settings
Resolution: 1920x1080
FPS: 30
Format: MP4
Encoder: x264
Bitrate: 8000 kbps
Audio: 192 kbps, 48kHz

# Terminal Settings
Font: JetBrains Mono 16pt
Background: #1a1a1a
Text: #ffffff
Accent: #00D4AA
Cursor: Block, blinking
```

### Editing Checklist
- [ ] Remove any hesitations or mistakes
- [ ] Add smooth transitions between sections
- [ ] Highlight key commands with zoom/highlight
- [ ] Add progress indicators for long operations
- [ ] Include captions for accessibility
- [ ] Add end screen with clear CTA
- [ ] Export in multiple formats (16:9, 1:1 for LinkedIn)

---

## 📱 Platform Optimization

### YouTube (16:9)
- Full resolution 1920x1080
- Add end cards linking to GitHub
- Include chapters in description
- Custom thumbnail with large text

### LinkedIn (1:1 Square)
- Crop to 1080x1080 square
- Ensure text remains readable
- Add native captions
- Shorter attention span - front-load value

### Website Embed
- Include video controls
- Auto-play muted for hero sections
- Provide play/pause for user control
- Ensure mobile responsive

---

## 🎯 Success Metrics

### Recording Quality Metrics
- [ ] Audio levels consistent (-12dB to -6dB)
- [ ] No background noise or echo
- [ ] Terminal text clearly readable on mobile
- [ ] Smooth screen recordings (no frame drops)
- [ ] Proper color contrast ratios

### Content Quality Metrics  
- [ ] Commands execute successfully every time
- [ ] Real data generated (not mocked)
- [ ] Timing matches voiceover precisely
- [ ] Clear value proposition in first 5 seconds
- [ ] Strong call-to-action at end

### Performance Targets
- **Retention Rate**: >70% completion
- **Click-Through**: >5% to GitHub
- **Engagement**: >10% like/comment rate
- **Conversion**: Measurable star/clone increases

---

## 🚀 Post-Production Workflow

### 1. Raw Recording Review
- Check audio sync
- Remove long pauses
- Verify all commands worked
- Note any re-recording needs

### 2. Editing Phase
- Cut to 30 seconds exactly
- Add intro/outro branding
- Include captions/subtitles
- Color correct if needed
- Add zoom highlights for key moments

### 3. Platform Exports
- YouTube: 1080p MP4, high bitrate
- LinkedIn: 1080x1080 MP4, mobile-optimized  
- Website: Multiple formats for compatibility
- GIF previews: For GitHub README

### 4. Upload Optimization
- Custom thumbnails for each platform
- SEO-optimized titles and descriptions
- Relevant tags and categories
- Proper video chapters/timestamps

### 5. Distribution
- Schedule releases across platforms
- Cross-promote on social media
- Share in relevant communities
- Monitor metrics and engagement

---

This production guide ensures consistent, professional video content that effectively demonstrates SBDK.dev's value proposition while maintaining high production standards across all platforms.