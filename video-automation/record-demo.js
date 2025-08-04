#!/usr/bin/env node

/**
 * SBDK.dev Video Recording Automation
 * Hybrid MCP + OBS approach for automated demo recording
 */

const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');

class VideoRecorder {
  constructor(scriptPath, outputName) {
    this.scriptPath = scriptPath;
    this.outputName = outputName;
    this.commands = [];
    this.currentIndex = 0;
    this.recordingActive = false;
  }

  async loadScript() {
    console.log(`📋 Loading script: ${this.scriptPath}`);
    const content = await fs.readFile(this.scriptPath, 'utf8');
    this.commands = this.parseCommands(content);
    console.log(`✅ Loaded ${this.commands.length} commands for automation`);
    return this.commands;
  }

  parseCommands(content) {
    // Extract bash code blocks with timing information
    const sections = content.split('```bash');
    const commands = [];

    sections.forEach((section, index) => {
      if (index === 0) return; // Skip content before first code block
      
      const endIndex = section.indexOf('```');
      if (endIndex === -1) return;
      
      const codeBlock = section.substring(0, endIndex);
      const lines = codeBlock.split('\n').filter(line => line.trim());
      
      lines.forEach(line => {
        line = line.trim();
        if (!line || line.startsWith('#')) {
          // Extract timing from comments like # [4-6s]
          const timingMatch = line.match(/# \[(\d+)-(\d+)s\]/);
          if (timingMatch) {
            const timing = {
              start: parseInt(timingMatch[1]),
              end: parseInt(timingMatch[2]),
              description: line.replace(/# \[\d+-\d+s\]/, '').trim()
            };
            // Apply timing to previous command or store for next
            if (commands.length > 0) {
              commands[commands.length - 1].timing = timing;
            } else {
              this.nextTiming = timing;
            }
          }
          return;
        }

        // Clean command (remove comments)
        const cleanCommand = line.split('#')[0].trim();
        if (cleanCommand) {
          const cmd = {
            command: cleanCommand,
            original: line,
            timing: this.nextTiming || { start: 0, end: 3, description: 'Execute command' }
          };
          commands.push(cmd);
          this.nextTiming = null;
        }
      });
    });

    return commands;
  }

  async checkOBSInstallation() {
    return new Promise((resolve) => {
      exec('which obs', (error, stdout) => {
        if (error) {
          console.log('⚠️  OBS Studio not found. Please install it:');
          console.log('   brew install --cask obs');
          console.log('   or download from: https://obsproject.com/');
          resolve(false);
        } else {
          console.log('✅ OBS Studio found');
          resolve(true);
        }
      });
    });
  }

  async promptUser(question) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    return new Promise((resolve) => {
      rl.question(question, (answer) => {
        rl.close();
        resolve(answer.toLowerCase().trim());
      });
    });
  }

  async startRecording() {
    console.log('\n🎬 Recording Workflow Started');
    console.log('==========================================');
    
    const obsAvailable = await this.checkOBSInstallation();
    
    if (obsAvailable) {
      console.log('\n📹 OBS Studio Integration:');
      console.log('1. Open OBS Studio');
      console.log('2. Set up your scene (Display Capture)');
      console.log('3. Configure hotkeys: Cmd+Shift+R (start), Cmd+Shift+S (stop)');
      
      const useOBS = await this.promptUser('\nUse OBS for recording? (y/n): ');
      if (useOBS === 'y') {
        await this.initializeOBS();
      }
    }

    console.log('\n🚀 Starting command automation in 3 seconds...');
    await this.countdown(3);
    
    if (this.recordingActive) {
      await this.sendOBSCommand('start');
      console.log('🔴 OBS Recording started');
    }
  }

  async initializeOBS() {
    console.log('\n⚙️  Initializing OBS integration...');
    this.recordingActive = true;
    
    // Check if OBS is running
    return new Promise((resolve) => {
      exec('pgrep -f "OBS"', (error, stdout) => {
        if (error || !stdout.trim()) {
          console.log('📱 Please start OBS Studio and press Enter when ready...');
          process.stdin.once('data', () => resolve());
        } else {
          console.log('✅ OBS Studio is running');
          resolve();
        }
      });
    });
  }

  async sendOBSCommand(action) {
    if (!this.recordingActive) return;

    const hotkeys = {
      start: 'key code 15 using {command down, shift down}', // Cmd+Shift+R
      stop: 'key code 1 using {command down, shift down}'    // Cmd+Shift+S
    };
    
    const script = `
      tell application "System Events"
        ${hotkeys[action]}
      end tell
    `;
    
    return new Promise((resolve) => {
      const proc = spawn('osascript', ['-e', script]);
      proc.on('close', resolve);
      proc.on('error', () => {
        console.log('⚠️  Could not send OBS hotkey');
        resolve();
      });
    });
  }

  async countdown(seconds) {
    for (let i = seconds; i > 0; i--) {
      process.stdout.write(`\r⏰ Starting in ${i}...`);
      await this.sleep(1000);
    }
    console.log('\r✅ Starting now!        ');
  }

  async executeCommand(cmd, index) {
    const timing = cmd.timing;
    const duration = (timing.end - timing.start) * 1000;
    
    console.log(`\n[${index + 1}/${this.commands.length}] ${timing.description}`);
    console.log(`⏱️  Duration: ${timing.start}-${timing.end}s`);
    console.log(`💻 Command: ${cmd.command}`);
    
    const startTime = Date.now();
    
    return new Promise((resolve, reject) => {
      const proc = spawn('bash', ['-c', cmd.command], {
        stdio: 'inherit',
        env: { 
          ...process.env, 
          PATH: process.env.PATH,
          PS1: '\\[\\033[32m\\]sbdk-demo\\[\\033[0m\\]:\\[\\033[34m\\]\\w\\[\\033[0m\\]$ '
        }
      });

      proc.on('close', async (code) => {
        const elapsed = Date.now() - startTime;
        const remaining = duration - elapsed;
        
        if (remaining > 0) {
          console.log(`⏳ Waiting ${Math.round(remaining/1000)}s for proper timing...`);
          await this.sleep(remaining);
        }
        
        console.log(`✅ Step completed (exit code: ${code})`);
        resolve({ code, elapsed: Date.now() - startTime });
      });

      proc.on('error', (error) => {
        console.error(`❌ Error executing command: ${error.message}`);
        reject(error);
      });
    });
  }

  async stopRecording() {
    if (this.recordingActive) {
      console.log('\n⏹️  Stopping recording...');
      await this.sendOBSCommand('stop');
      console.log('✅ Recording stopped');
    }
    
    console.log('\n🎉 Video recording automation complete!');
    console.log(`📁 Output: ${this.outputName}`);
    console.log('\nNext steps:');
    console.log('1. Check your OBS recording in ~/Videos/');
    console.log('2. Edit and trim as needed');
    console.log('3. Export for different platforms');
  }

  async sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async recordVideo() {
    try {
      console.log('🎬 SBDK.dev Video Recording Automation');
      console.log('=====================================');
      
      await this.loadScript();
      await this.startRecording();

      // Execute all commands with proper timing
      for (let i = 0; i < this.commands.length; i++) {
        await this.executeCommand(this.commands[i], i);
      }

      await this.stopRecording();

    } catch (error) {
      console.error('\n❌ Recording failed:', error.message);
      if (this.recordingActive) {
        await this.sendOBSCommand('stop');
      }
      process.exit(1);
    }
  }

  // Preview mode - show commands without executing
  async previewScript() {
    console.log('👁️  Script Preview Mode');
    console.log('====================');
    
    await this.loadScript();
    
    console.log('\nCommands to be executed:');
    this.commands.forEach((cmd, index) => {
      console.log(`\n${index + 1}. [${cmd.timing.start}-${cmd.timing.end}s] ${cmd.timing.description}`);
      console.log(`   Command: ${cmd.command}`);
    });
    
    const totalTime = Math.max(...this.commands.map(c => c.timing.end));
    console.log(`\n⏱️  Total estimated time: ${totalTime} seconds`);
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('🎬 SBDK.dev Video Recording Automation');
    console.log('Usage:');
    console.log('  node record-demo.js <script-file> <output-name>');
    console.log('  node record-demo.js preview <script-file>');
    console.log('');
    console.log('Examples:');
    console.log('  node record-demo.js scripts/video1-setup.md "SBDK-30Second-Demo"');
    console.log('  node record-demo.js preview scripts/video1-setup.md');
    process.exit(1);
  }

  if (args[0] === 'preview') {
    const scriptPath = args[1];
    if (!scriptPath) {
      console.error('❌ Please provide a script file for preview');
      process.exit(1);
    }
    
    const recorder = new VideoRecorder(scriptPath, 'preview');
    await recorder.previewScript();
    return;
  }

  const [scriptPath, outputName] = args;
  if (!scriptPath || !outputName) {
    console.error('❌ Please provide both script file and output name');
    process.exit(1);
  }

  // Check if script file exists
  try {
    await fs.access(scriptPath);
  } catch (error) {
    console.error(`❌ Script file not found: ${scriptPath}`);
    process.exit(1);
  }

  const recorder = new VideoRecorder(scriptPath, outputName);
  await recorder.recordVideo();
}

// Handle process termination gracefully
process.on('SIGINT', () => {
  console.log('\n\n⏹️  Recording interrupted by user');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\n⏹️  Recording terminated');
  process.exit(0);
});

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  });
}

module.exports = VideoRecorder;