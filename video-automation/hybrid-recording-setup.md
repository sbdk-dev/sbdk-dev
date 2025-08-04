# 🎬 Hybrid Video Recording Setup for SBDK.dev

## 🎯 Overview

This hybrid approach combines:
- **MCP Terminal Server** for automated command execution
- **OBS Studio** for high-quality screen recording
- **Coordination Scripts** for perfect timing
- **Your existing video scripts** for content structure

## 📋 Prerequisites

### Required Software
```bash
# 1. OBS Studio (for screen recording)
# Download from: https://obsproject.com/
# Or install via Homebrew:
brew install --cask obs

# 2. Node.js and npm (for MCP servers)
node --version  # Should be 18+
npm --version

# 3. Terminal MCP Server
npm install -g @rinardnick/mcp-terminal
```

### System Requirements
- **macOS**: Screen Recording permissions for OBS
- **Memory**: 4GB+ available (OBS + terminal operations)
- **Storage**: 10GB+ for video files
- **Display**: 1920x1080 or higher for crisp recordings

---

## 🔧 Step 1: MCP Terminal Server Setup

### Installation
```bash
# Install the Terminal MCP server
npm install -g @rinardnick/mcp-terminal

# Verify installation
mcp-terminal --version
```

### Configuration
Create MCP configuration file:
```json
{
  "mcpServers": {
    "terminal": {
      "command": "mcp-terminal",
      "args": [],
      "env": {
        "TERMINAL_TIMEOUT": "30000",
        "ALLOWED_COMMANDS": "sbdk,uv,echo,ls,cd,mkdir,duckdb"
      }
    }
  }
}
```

### Security Settings
```bash
# Create secure command whitelist
echo "sbdk" >> ~/.mcp-terminal-allowed
echo "uv" >> ~/.mcp-terminal-allowed
echo "echo" >> ~/.mcp-terminal-allowed
echo "ls" >> ~/.mcp-terminal-allowed
echo "cd" >> ~/.mcp-terminal-allowed
echo "mkdir" >> ~/.mcp-terminal-allowed
echo "duckdb" >> ~/.mcp-terminal-allowed
```

---

## 🎥 Step 2: OBS Studio Configuration

### Recording Settings
```
Resolution: 1920x1080
Frame Rate: 30 FPS
Encoder: Software (x264)
Rate Control: CBR
Bitrate: 8000 Kbps
Keyframe Interval: 2
CPU Usage Preset: veryfast
Profile: high
```

### Scene Setup
1. **Source**: Display Capture (entire screen)
2. **Audio**: Desktop Audio + Microphone (if doing voiceover)
3. **Filters**: 
   - Color Correction (if needed)
   - Noise Suppression (for microphone)

### Hotkey Configuration
```
Start Recording: Cmd+Shift+R
Stop Recording: Cmd+Shift+S
Pause Recording: Cmd+Shift+P
```

### Recording Path
```bash
# Set output directory
mkdir -p ~/Videos/SBDK-Demos
# Configure OBS to save here: ~/Videos/SBDK-Demos/
```

---

## 🤖 Step 3: Automation Coordination Script

Create the main automation script:

```javascript
// video-automation/record-demo.js
const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class VideoRecorder {
  constructor(scriptPath, outputName) {
    this.scriptPath = scriptPath;
    this.outputName = outputName;
    this.commands = [];
    this.currentIndex = 0;
  }

  async loadScript() {
    const content = await fs.readFile(this.scriptPath, 'utf8');
    this.commands = this.parseCommands(content);
    console.log(`📋 Loaded ${this.commands.length} commands`);
  }

  parseCommands(content) {
    // Extract commands from video scripts
    const commandRegex = /```bash\n(.*?)\n```/gs;
    const matches = [...content.matchAll(commandRegex)];
    return matches.map(match => ({
      command: match[1].trim(),
      timing: this.extractTiming(match[0])
    }));
  }

  extractTiming(block) {
    // Extract timing from comments like # [4-6s]
    const timingMatch = block.match(/# \[(\d+)-(\d+)s\]/);
    return timingMatch ? {
      start: parseInt(timingMatch[1]),
      end: parseInt(timingMatch[2])
    } : { start: 0, end: 3 };
  }

  async startRecording() {
    console.log('🎬 Starting OBS recording...');
    // Send hotkey to OBS (requires AppleScript on macOS)
    await this.sendOBSCommand('start');
    
    // Wait 2 seconds for recording to start
    await this.sleep(2000);
    console.log('🔴 Recording started');
  }

  async stopRecording() {
    console.log('⏹️  Stopping OBS recording...');
    await this.sendOBSCommand('stop');
    console.log('✅ Recording stopped');
  }

  async sendOBSCommand(action) {
    const hotkeys = {
      start: 'command down, shift down, "r", shift up, command up',
      stop: 'command down, shift down, "s", shift up, command up'
    };
    
    const script = `
      tell application "System Events"
        key code ${hotkeys[action]}
      end tell
    `;
    
    return new Promise((resolve) => {
      const proc = spawn('osascript', ['-e', script]);
      proc.on('close', resolve);
    });
  }

  async executeCommand(cmd) {
    return new Promise((resolve, reject) => {
      console.log(`💻 Executing: ${cmd.command}`);
      
      const proc = spawn('bash', ['-c', cmd.command], {
        stdio: 'pipe',
        env: { ...process.env, PATH: process.env.PATH }
      });

      let output = '';
      proc.stdout.on('data', (data) => {
        output += data.toString();
        process.stdout.write(data);
      });

      proc.stderr.on('data', (data) => {
        output += data.toString();
        process.stderr.write(data);
      });

      proc.on('close', (code) => {
        console.log(`✅ Command completed (exit: ${code})`);
        resolve({ code, output });
      });

      proc.on('error', reject);
    });
  }

  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async recordVideo() {
    try {
      await this.loadScript();
      await this.startRecording();

      for (const cmd of this.commands) {
        const startTime = Date.now();
        await this.executeCommand(cmd);
        
        // Wait for timing if needed
        const elapsed = Date.now() - startTime;
        const targetDuration = (cmd.timing.end - cmd.timing.start) * 1000;
        if (elapsed < targetDuration) {
          await this.sleep(targetDuration - elapsed);
        }
      }

      await this.stopRecording();
      console.log(`🎉 Video recording complete: ${this.outputName}`);

    } catch (error) {
      console.error('❌ Recording failed:', error);
      await this.stopRecording(); // Ensure recording stops
    }
  }
}

// Export for use
module.exports = VideoRecorder;

// CLI usage
if (require.main === module) {
  const [,, scriptPath, outputName] = process.argv;
  if (!scriptPath || !outputName) {
    console.log('Usage: node record-demo.js <script-path> <output-name>');
    process.exit(1);
  }

  const recorder = new VideoRecorder(scriptPath, outputName);
  recorder.recordVideo().catch(console.error);
}
```

---

## 📝 Step 4: Adapted Video Scripts

Convert your existing scripts to MCP-compatible format:

```markdown
# Video 1: 30-Second Setup - MCP Compatible

## Pre-Recording Setup
```bash
# Clean environment
cd ~/Desktop
rm -rf demo-recording
mkdir demo-recording && cd demo-recording
clear
```

## Recording Commands
```bash
# [0-4s] Show installation speed
echo "🚀 Installing SBDK.dev with uv..."
uv pip install sbdk-dev

# [5-9s] Create project
echo "📦 Creating new project..."
sbdk init demo-pipeline

# [10-12s] Enter directory
cd demo-pipeline
ls -la

# [13-20s] Run pipeline
echo "⚡ Running complete pipeline..."
sbdk run

# [21-25s] Show results
echo "📊 Checking generated data..."
echo "SELECT COUNT(*) as total_users FROM users;" | duckdb data/demo.duckdb
echo "SELECT COUNT(*) as total_events FROM events;" | duckdb data/demo.duckdb

# [26-30s] Final message
echo "✅ Complete data pipeline in 30 seconds!"
```
```

---

## 🎬 Step 5: Recording Workflow

### Terminal Setup
```bash
# Terminal appearance for recording
export PS1="\[\033[32m\]sbdk-demo\[\033[0m\]:\[\033[34m\]\w\[\033[0m\]$ "
clear

# Font settings (iTerm2/Terminal)
# Font: JetBrains Mono, 16pt
# Background: #1a1a1a
# Text: #ffffff
# Accent: #00D4AA
```

### Recording Process
```bash
# 1. Prepare environment
cd ~/Desktop && mkdir -p sbdk-video-demos
cd sbdk-video-demos

# 2. Start automated recording
node ../video-automation/record-demo.js video1-setup-script.md "SBDK-30-Second-Setup"

# 3. Let automation handle the rest!
```

### Manual Coordination
1. **Pre-recording**: Set up clean terminal, check lighting
2. **Start**: Run automation script (it handles OBS start/stop)
3. **During**: Let script execute commands with proper timing
4. **Post**: Review recording, trim if needed

---

## ⚡ Step 6: Advanced Automation Features

### Smart Waiting
```javascript
// Add to VideoRecorder class
async waitForProcess(processName, maxWait = 30000) {
  const start = Date.now();
  while (Date.now() - start < maxWait) {
    const { output } = await this.executeCommand(`pgrep ${processName}`);
    if (!output.trim()) break;
    await this.sleep(1000);
  }
}
```

### Progress Indicators
```javascript
async showProgress(message, duration) {
  console.log(`🔄 ${message}`);
  const interval = setInterval(() => {
    process.stdout.write('.');
  }, 500);
  
  await this.sleep(duration);
  clearInterval(interval);
  console.log(' ✅');
}
```

### Error Recovery
```javascript
async safeExecute(cmd, retries = 2) {
  for (let i = 0; i < retries; i++) {
    try {
      return await this.executeCommand(cmd);
    } catch (error) {
      if (i === retries - 1) throw error;
      console.log(`⚠️  Retry ${i + 1}/${retries}`);
      await this.sleep(2000);
    }
  }
}
```

---

## 📊 Step 7: Quality Control

### Pre-Recording Checklist
- [ ] Clean terminal environment
- [ ] Proper font size (16pt minimum)
- [ ] Recording permissions enabled
- [ ] Audio levels tested
- [ ] Commands tested individually
- [ ] Timing verified

### During Recording
- [ ] Smooth command execution
- [ ] Proper timing between commands
- [ ] No unexpected errors
- [ ] Clear terminal output
- [ ] Consistent theme/colors

### Post-Recording
- [ ] Video quality check
- [ ] Audio sync verification
- [ ] Trim unnecessary parts
- [ ] Export in multiple formats
- [ ] Upload to platforms

---

## 🚀 Usage Examples

### Record All Videos
```bash
# Create batch recording script
#!/bin/bash
videos=(
  "video1-setup:docs/VIDEO_SCRIPTS.md:Video1-30Second-Setup"
  "video2-visual:docs/VIDEO_SCRIPTS.md:Video2-Visual-Mode"
  "video3-hotreload:docs/VIDEO_SCRIPTS.md:Video3-Hot-Reload"
)

for video in "${videos[@]}"; do
  IFS=':' read -r name script output <<< "$video"
  echo "🎬 Recording $name..."
  node record-demo.js "$script" "$output"
  echo "✅ Completed $name"
  sleep 5  # Brief pause between recordings
done
```

### Individual Video Recording
```bash
# Record specific video
node record-demo.js "scripts/video1-30second-setup.md" "SBDK-30Second-Demo"
```

This hybrid approach gives you the automation benefits of MCP while maintaining the high-quality recording capabilities of OBS Studio. The coordination script handles timing and execution, while you focus on the final video quality!