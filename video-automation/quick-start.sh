#!/bin/bash

# 🎬 SBDK.dev Video Recording - Quick Start Script
# Sets up the complete hybrid recording environment

set -e  # Exit on any error

echo "🎬 SBDK.dev Video Recording Setup"
echo "================================="

# Check if we're in the right directory
if [[ ! -f "setup.py" ]]; then
    echo "❌ Please run this from the SBDK.dev root directory"
    exit 1
fi

# Create video automation directories
echo "📁 Creating video automation structure..."
mkdir -p video-automation/{scripts,recordings,assets}

# Check Node.js
echo "🔍 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first:"
    echo "   brew install node"
    exit 1
fi

node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [[ $node_version -lt 18 ]]; then
    echo "❌ Node.js 18+ required. Current version: $(node --version)"
    exit 1
fi
echo "✅ Node.js $(node --version) found"

# Check OBS Studio
echo "🔍 Checking OBS Studio..."
if ! command -v obs &> /dev/null; then
    echo "⚠️  OBS Studio not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install --cask obs
        echo "✅ OBS Studio installed via Homebrew"
    else
        echo "❌ Homebrew not found. Please install OBS Studio manually:"
        echo "   Download from: https://obsproject.com/"
        exit 1
    fi
else
    echo "✅ OBS Studio found"
fi

# Check uv package manager
echo "🔍 Checking uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true
    if ! command -v uv &> /dev/null; then
        echo "❌ uv installation failed. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi
echo "✅ uv package manager found"

# Install SBDK.dev if not already installed
echo "🔍 Checking SBDK.dev installation..."
if ! command -v sbdk &> /dev/null; then
    echo "⚠️  SBDK.dev not found. Installing..."
    uv pip install sbdk-dev
    echo "✅ SBDK.dev installed"
else
    echo "✅ SBDK.dev found"
fi

# Test recording script
echo "🧪 Testing recording automation..."
if node video-automation/record-demo.js preview video-automation/video1-30second-setup.md &> /dev/null; then
    echo "✅ Recording automation script working"
else
    echo "❌ Recording automation script has issues"
    echo "   Try: node video-automation/record-demo.js preview video-automation/video1-30second-setup.md"
fi

# Create output directories
echo "📁 Setting up output directories..."
mkdir -p ~/Videos/SBDK-Demos
mkdir -p video-automation/recordings

# Set up terminal for recording
echo "⚙️  Configuring terminal for recording..."
cat > video-automation/terminal-setup.sh << 'EOF'
#!/bin/bash
# Terminal setup for recording
export PS1="\[\033[32m\]sbdk-demo\[\033[0m\]:\[\033[34m\]\w\[\033[0m\]$ "
export TERM=xterm-256color
clear
echo "🎬 Terminal ready for recording!"
echo "💡 Recommended settings:"
echo "   Font: JetBrains Mono, 16pt"
echo "   Background: #1a1a1a"
echo "   Text: #ffffff"
echo "   Accent: #00D4AA"
EOF

chmod +x video-automation/terminal-setup.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo "1. Open OBS Studio and configure:"
echo "   - Scene: Display Capture (full screen)"
echo "   - Hotkeys: Cmd+Shift+R (start), Cmd+Shift+S (stop)"
echo "   - Output: ~/Videos/SBDK-Demos/"
echo ""
echo "2. Set up terminal appearance:"
echo "   source video-automation/terminal-setup.sh"
echo ""
echo "3. Preview your first video:"
echo "   node video-automation/record-demo.js preview video-automation/video1-30second-setup.md"
echo ""
echo "4. Record your first video:"
echo "   node video-automation/record-demo.js video-automation/video1-30second-setup.md \"SBDK-30Second-Demo\""
echo ""
echo "💡 Pro Tips:"
echo "   - Test commands individually first"
echo "   - Use preview mode to check timing"
echo "   - Ensure good lighting and clean desktop"
echo "   - Practice the voiceover separately"
echo ""