# Building SBDK Binary Executables

This guide explains how to build standalone binary executables for SBDK that can be distributed without requiring Python or any dependencies to be pre-installed.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Build Methods](#build-methods)
  - [Method 1: PyInstaller (Recommended)](#method-1-pyinstaller-recommended)
  - [Method 2: Nuitka](#method-2-nuitka)
  - [Method 3: cx_Freeze](#method-3-cx_freeze)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Overview

Building SBDK as a standalone binary allows you to:
- 📦 Distribute a single executable file
- 🚀 Run without Python installation
- 🔒 Protect source code
- ⚡ Faster startup times
- 🎯 Simplified deployment

## Prerequisites

Before building, ensure you have:

```bash
# 1. Clone the repository
git clone https://github.com/sbdk-dev/sbdk-dev.git
cd sbdk-dev

# 2. Install uv (for fast package management)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Set up development environment
uv sync --extra dev

# 4. Install build tools
uv pip install pyinstaller
```

## Build Methods

### Method 1: PyInstaller (Recommended)

PyInstaller is the most reliable method for creating cross-platform binaries.

#### Basic Build

```bash
# Simple one-file executable
uv run pyinstaller --onefile --name sbdk sbdk/cli/main.py

# Output will be in: dist/sbdk (or dist/sbdk.exe on Windows)
```

#### Optimized Build with Configuration

Create a `sbdk.spec` file for more control:

```python
# sbdk.spec
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['sbdk/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sbdk/templates', 'sbdk/templates'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'typer',
        'rich',
        'duckdb',
        'pandas',
        'faker',
        'dlt',
        'dbt.core',
        'dbt.adapters.duckdb',
        'fastapi',
        'uvicorn',
        'watchdog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='sbdk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

Build with spec file:

```bash
uv run pyinstaller sbdk.spec
```

#### Advanced Build Options

```bash
# Include icon (create or download an icon file first)
uv run pyinstaller --onefile --name sbdk --icon=assets/sbdk.ico sbdk/cli/main.py

# Optimize for size
uv run pyinstaller --onefile --name sbdk --strip --upx-dir=/usr/local/bin sbdk/cli/main.py

# Include additional files
uv run pyinstaller --onefile --name sbdk \
  --add-data "sbdk/templates:sbdk/templates" \
  --add-data "README.md:." \
  sbdk/cli/main.py
```

### Method 2: Nuitka

Nuitka compiles Python to C++ for better performance.

```bash
# Install Nuitka
uv pip install nuitka

# Build standalone executable
uv run python -m nuitka \
  --standalone \
  --onefile \
  --enable-plugin=anti-bloat \
  --enable-plugin=data-files \
  --include-package-data=sbdk \
  --output-filename=sbdk \
  sbdk/cli/main.py
```

### Method 3: cx_Freeze

Alternative method for cross-platform builds.

```bash
# Install cx_Freeze
uv pip install cx_Freeze

# Create setup.py for cx_Freeze
cat > setup_freeze.py << 'EOF'
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["typer", "rich", "duckdb", "pandas", "faker", "dlt", "dbt", "fastapi"],
    "include_files": [
        ("sbdk/templates", "lib/sbdk/templates"),
        ("README.md", "README.md"),
    ],
}

setup(
    name="sbdk",
    version="1.0.1",
    description="SBDK.dev - Local-first data pipeline sandbox",
    options={"build_exe": build_exe_options},
    executables=[Executable("sbdk/cli/main.py", base=None, target_name="sbdk")],
)
EOF

# Build
uv run python setup_freeze.py build
```

## Platform-Specific Instructions

### macOS

```bash
# Build for macOS (Intel and Apple Silicon)
uv run pyinstaller --onefile --name sbdk \
  --target-arch universal2 \
  sbdk/cli/main.py

# Sign the binary (requires Apple Developer account)
codesign --deep --force --sign "Developer ID Application: Your Name" dist/sbdk

# Create DMG for distribution
hdiutil create -volname "SBDK" -srcfolder dist -ov -format UDZO sbdk.dmg
```

### Windows

```bash
# Build for Windows
uv run pyinstaller --onefile --name sbdk.exe \
  --icon=assets/sbdk.ico \
  --version-file=version.txt \
  sbdk/cli/main.py

# Create installer with NSIS or Inno Setup
# Example Inno Setup script available in: scripts/windows-installer.iss
```

### Linux

```bash
# Build for Linux
uv run pyinstaller --onefile --name sbdk sbdk/cli/main.py

# Create AppImage for universal Linux distribution
# 1. Download appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# 2. Create AppDir structure
mkdir -p AppDir/usr/bin
cp dist/sbdk AppDir/usr/bin/
cp assets/sbdk.desktop AppDir/
cp assets/sbdk.png AppDir/

# 3. Create AppImage
./appimagetool-x86_64.AppImage AppDir sbdk-x86_64.AppImage
```

## Distribution

### File Sizes (Approximate)

- **PyInstaller**: 50-80 MB (includes Python runtime)
- **Nuitka**: 30-50 MB (optimized C++ compilation)
- **cx_Freeze**: 60-90 MB (includes dependencies)

### Compression

```bash
# Compress for distribution
# macOS/Linux
tar -czf sbdk-$(uname -s)-$(uname -m).tar.gz dist/sbdk

# Windows (PowerShell)
Compress-Archive -Path dist\sbdk.exe -DestinationPath sbdk-Windows-x64.zip
```

### GitHub Releases

Create automated releases with GitHub Actions:

```yaml
# .github/workflows/build-release.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --extra dev
        uv pip install pyinstaller
    
    - name: Build binary
      run: |
        uv run pyinstaller --onefile --name sbdk sbdk/cli/main.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: sbdk-${{ matrix.os }}
        path: dist/*
```

## Troubleshooting

### Common Issues

#### 1. Missing Modules Error

```bash
# If you get "ModuleNotFoundError" when running the binary:
# Add hidden imports to PyInstaller
uv run pyinstaller --onefile --name sbdk \
  --hidden-import=dbt.adapters.duckdb \
  --hidden-import=dlt.destinations.duckdb \
  sbdk/cli/main.py
```

#### 2. Templates Not Found

```bash
# Include template files in the build
uv run pyinstaller --onefile --name sbdk \
  --add-data "sbdk/templates:sbdk/templates" \
  --collect-data sbdk \
  sbdk/cli/main.py
```

#### 3. Large Binary Size

```bash
# Exclude unnecessary packages
uv run pyinstaller --onefile --name sbdk \
  --exclude-module matplotlib \
  --exclude-module scipy \
  --exclude-module numpy \
  sbdk/cli/main.py
```

#### 4. Antivirus False Positives

- Sign your binaries with a code signing certificate
- Submit false positive reports to antivirus vendors
- Use UPX compression carefully (may trigger more false positives)

### Debug Build

```bash
# Create debug build to troubleshoot issues
uv run pyinstaller --onefile --name sbdk-debug \
  --debug all \
  --log-level DEBUG \
  sbdk/cli/main.py

# Run with verbose output
./dist/sbdk-debug --help
```

### Testing the Binary

```bash
# Test basic functionality
./dist/sbdk version
./dist/sbdk --help

# Test project creation
./dist/sbdk init test_project
cd test_project
../dist/sbdk run

# Test all commands
./dist/sbdk init test_binary_project
./dist/sbdk run --visual
./dist/sbdk debug
```

## Best Practices

1. **Version Management**: Include version info in the binary
2. **Code Signing**: Sign binaries for trust and security
3. **Testing**: Test on clean systems without Python
4. **Documentation**: Include README in the distribution
5. **Updates**: Implement self-update mechanism

## Advanced Topics

### Self-Updating Binary

```python
# Add to sbdk/cli/main.py
import requests
from packaging import version

def check_for_updates():
    """Check GitHub for new releases"""
    try:
        response = requests.get(
            "https://api.github.com/repos/sbdk-dev/sbdk-dev/releases/latest"
        )
        latest_version = response.json()["tag_name"].lstrip("v")
        current_version = __version__
        
        if version.parse(latest_version) > version.parse(current_version):
            console.print(f"[yellow]New version available: {latest_version}[/yellow]")
            console.print("Download from: https://github.com/sbdk-dev/sbdk-dev/releases")
    except:
        pass  # Fail silently
```

### Multi-Architecture Builds

```bash
# Build for multiple architectures
# macOS Universal Binary
uv run pyinstaller --onefile --name sbdk \
  --target-arch universal2 \
  sbdk/cli/main.py

# Linux multi-arch with Docker
docker buildx build --platform linux/amd64,linux/arm64 .
```

## Conclusion

Building SBDK as a binary makes it easy to distribute and use without Python dependencies. Choose the method that best fits your needs:

- **PyInstaller**: Best overall compatibility
- **Nuitka**: Best performance
- **cx_Freeze**: Good alternative option

For production releases, always test thoroughly on target platforms and consider code signing for trust.

---

📚 For more information, see:
- [PyInstaller Documentation](https://pyinstaller.org)
- [Nuitka Documentation](https://nuitka.net)
- [cx_Freeze Documentation](https://cx-freeze.readthedocs.io)