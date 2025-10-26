# GitHub Release Workflow Setup Guide

This guide explains how to set up and use the GitHub Actions workflow for building, publishing, and releasing SBDK with standalone binaries.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setting Up PyPI Publishing](#setting-up-pypi-publishing)
- [Creating a Release](#creating-a-release)
- [Workflow Features](#workflow-features)
- [Testing the Workflow](#testing-the-workflow)
- [Troubleshooting](#troubleshooting)
- [Binary Distribution](#binary-distribution)

## Overview

The `python-publish.yml` workflow automatically:

1. **Builds Python packages** when a release is created
2. **Creates standalone binaries** for Windows, macOS, and Linux
3. **Publishes to PyPI** using trusted publishing
4. **Uploads binaries** to the GitHub release

## Prerequisites

### 1. Repository Setup

Ensure your repository has:
- ✅ The workflow file at `.github/workflows/python-publish.yml`
- ✅ A valid `pyproject.toml` with proper package configuration
- ✅ Version number in `sbdk/__init__.py`

### 2. PyPI Account

1. Create an account at [pypi.org](https://pypi.org)
2. Verify your email address
3. Enable 2FA (recommended)

## Setting Up PyPI Publishing

### Step 1: Configure PyPI Trusted Publishing

1. Go to your PyPI account settings
2. Navigate to "Publishing" → "Add a new pending publisher"
3. Fill in the form:
   ```
   PyPI Project Name: sbdk-dev
   Owner: sbdk-dev (your GitHub username/org)
   Repository: sbdk-dev
   Workflow name: python-publish.yml
   Environment name: pypi
   ```
4. Click "Add"

### Step 2: Configure GitHub Repository

1. Go to your GitHub repository
2. Navigate to Settings → Environments
3. Click "New environment"
4. Name it `pypi`
5. Add protection rules (optional but recommended):
   - Required reviewers
   - Restrict deployment branches to `main` or `master`

### Step 3: No Secrets Needed!

With trusted publishing, you don't need to store PyPI tokens in GitHub secrets. The workflow uses OpenID Connect (OIDC) for authentication.

## Creating a Release

### Method 1: GitHub Web Interface (Recommended)

1. Go to your repository on GitHub
2. Click "Releases" in the right sidebar
3. Click "Draft a new release"
4. Fill in the release form:
   ```
   Tag version: v1.0.2
   Target: main
   Release title: v1.0.2 - Feature Release
   
   Describe this release:
   ## What's New
   - Added feature X
   - Fixed bug Y
   - Improved performance of Z
   
   ## Binary Downloads
   Standalone executables will be attached automatically after release.
   ```
5. Click "Publish release"

### Method 2: GitHub CLI

```bash
# Install GitHub CLI
brew install gh  # macOS
# or visit: https://cli.github.com/

# Authenticate
gh auth login

# Create a release
gh release create v1.0.2 \
  --title "v1.0.2 - Feature Release" \
  --notes "## What's New\n- Added feature X\n- Fixed bug Y" \
  --target main
```

### Method 3: Git Tags

```bash
# Create and push a tag
git tag -a v1.0.2 -m "Release version 1.0.2"
git push origin v1.0.2

# Then create the release on GitHub web interface
```

## Workflow Features

### Automatic Triggers

The workflow runs automatically when:
- 🚀 A new release is published
- 🧪 Manual trigger via workflow_dispatch (for testing)

### Multi-Platform Binaries

Builds standalone executables for:
- 🐧 **Linux**: `sbdk-linux-x86_64.tar.gz`
- 🪟 **Windows**: `sbdk-windows-x86_64.exe.zip`
- 🍎 **macOS**: `sbdk-macos-universal.tar.gz`

### Build Matrix

```yaml
matrix:
  include:
    - os: ubuntu-latest
      name: linux
    - os: windows-latest
      name: windows
    - os: macos-latest
      name: macos
```

## Testing the Workflow

### Test Without Publishing

1. Go to Actions tab in your repository
2. Select "Build, Publish, and Release"
3. Click "Run workflow"
4. Select branch and check "Test release"
5. Click "Run workflow"

This will:
- ✅ Build Python packages
- ✅ Create binaries for all platforms
- ❌ Skip PyPI publishing
- ❌ Skip GitHub release upload

### Monitor Progress

1. Click on the running workflow
2. Watch each job's progress:
   - `release-build`: Python package building
   - `build-binaries`: Binary creation (3 parallel jobs)
   - `pypi-publish`: PyPI upload (skipped in test)
   - `upload-release-assets`: Release upload (skipped in test)

## Troubleshooting

### Common Issues

#### 1. PyPI Publishing Fails

**Error**: "Trusted publishing not configured"

**Solution**:
1. Ensure PyPI project name matches exactly: `sbdk-dev`
2. Check environment name is `pypi`
3. Verify workflow filename is `python-publish.yml`
4. Wait 5 minutes after PyPI configuration

#### 2. Binary Build Fails

**Error**: "ModuleNotFoundError during PyInstaller build"

**Solution**:
Add missing imports to the workflow:
```yaml
--hidden-import missing_module_name \
```

#### 3. Release Asset Upload Fails

**Error**: "Resource not accessible by integration"

**Solution**:
Check workflow permissions:
```yaml
permissions:
  contents: write  # Required for release uploads
```

#### 4. macOS Code Signing Warning

**Warning**: "Binary not signed"

**Solution** (optional):
- This is normal for open-source projects
- Users may need to allow the app in System Preferences
- For production, consider code signing with Apple Developer account

### Debug Tips

1. **Check workflow logs**: Click on failed job → View logs
2. **Test locally**: Try building with PyInstaller locally first
3. **Version mismatch**: Ensure version in `__init__.py` matches tag

## Binary Distribution

### Download Links

After release, binaries are available at:
```
https://github.com/sbdk-dev/sbdk-dev/releases/latest
```

### Installation Instructions for Users

Include in your release notes:

```markdown
## Installation

### From PyPI (Recommended)
\```bash
pip install sbdk-dev
\```

### Standalone Binaries

Download for your platform:
- 🐧 **Linux**: [sbdk-linux-x86_64.tar.gz](link)
- 🪟 **Windows**: [sbdk-windows-x86_64.exe.zip](link)
- 🍎 **macOS**: [sbdk-macos-universal.tar.gz](link)

#### Linux/macOS
\```bash
tar -xzf sbdk-*.tar.gz
chmod +x sbdk
./sbdk --help
\```

#### Windows
1. Extract the zip file
2. Run `sbdk.exe` from Command Prompt or PowerShell
```

## Advanced Configuration

### Custom Build Options

Modify the workflow to add:

```yaml
# Icon for Windows
--icon=assets/sbdk.ico \

# Version information
--version-file=version.txt \

# Optimization
--strip \
--upx-dir=/usr/local/bin \
```

### Additional Platforms

Add more platforms to the matrix:

```yaml
- os: ubuntu-20.04
  name: linux-ubuntu20
  binary_name: sbdk
  asset_name: sbdk-linux-ubuntu20-x86_64
```

### Caching Dependencies

Speed up builds with caching:

```yaml
- name: Cache uv dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}
```

## Release Checklist

Before creating a release:

- [ ] Update version in `sbdk/__init__.py`
- [ ] Update CHANGELOG.md
- [ ] Run tests locally: `uv run pytest`
- [ ] Test binary build locally: `uv run pyinstaller --onefile sbdk/cli/main.py`
- [ ] Commit all changes
- [ ] Push to main branch
- [ ] Create release on GitHub

## Best Practices

1. **Semantic Versioning**: Use format `v1.2.3`
2. **Release Notes**: Include user-facing changes
3. **Test First**: Use workflow_dispatch before real release
4. **Monitor Actions**: Watch the workflow execution
5. **Verify Release**: Test downloaded binaries after release

## Security Considerations

1. **No Secrets in Code**: The workflow uses OIDC, no tokens needed
2. **Protected Branches**: Require PR reviews for main branch
3. **Environment Protection**: Add reviewers to `pypi` environment
4. **Artifact Scanning**: GitHub automatically scans uploads

## Conclusion

With this setup, every GitHub release automatically:
- 📦 Builds and publishes to PyPI
- 🔨 Creates standalone binaries
- 📎 Attaches binaries to the release
- 🚀 Makes SBDK easily installable

Users can choose between:
- `pip install sbdk-dev` for Python users
- Downloaded binaries for non-Python users

The workflow handles all the complexity, making releases simple and reliable!

---

For more information:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [PyInstaller Documentation](https://pyinstaller.org)