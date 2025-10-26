# GitHub Wiki Setup Instructions

This directory contains all the prepared content for your SBDK.dev GitHub wiki.

## Prerequisites

Before you can push to the wiki, you need to **enable and initialize it** on GitHub:

### Step 1: Enable the Wiki on GitHub

1. Go to your repository: https://github.com/sbdk-dev/sbdk-dev
2. Click on **Settings** tab
3. Scroll down to the **Features** section
4. Check the **Wikis** checkbox to enable it
5. Click **Save**

### Step 2: Initialize the Wiki

1. Go to the **Wiki** tab in your repository
2. Click **Create the first page**
3. Enter any title (e.g., "Home") and content (e.g., "Initial setup")
4. Click **Save Page**

This creates the wiki repository and makes it clonable.

## Quick Setup Script

Once the wiki is enabled and initialized on GitHub, run this script:

```bash
#!/bin/bash

# Configuration
WIKI_URL="http://local_proxy@127.0.0.1:59050/git/sbdk-dev/sbdk-dev.wiki.git"
WIKI_DIR="sbdk-wiki"
SOURCE_DIR="/tmp/sbdk-wiki"

echo "📚 Setting up SBDK.dev GitHub Wiki..."

# Clone the wiki repository
echo "Cloning wiki repository..."
git clone "$WIKI_URL" "$WIKI_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to clone wiki repository."
    echo "Make sure the wiki is enabled and initialized on GitHub."
    exit 1
fi

cd "$WIKI_DIR"

# Copy all prepared content
echo "Copying wiki content..."
cp -r "$SOURCE_DIR"/*.md .

# Commit changes
echo "Committing changes..."
git add .
git commit -m "Initial wiki setup with comprehensive documentation

- Add Home page with overview and quick start
- Add sidebar navigation
- Add all documentation pages:
  - Getting Started guide
  - User Guide
  - Architecture documentation
  - Configuration guides
  - API Reference
  - Advanced topics (CI/CD, Binary builds, etc.)

Generated with SBDK.dev wiki setup tool"

# Push to GitHub
echo "Pushing to GitHub..."
git push origin master

echo "✅ Wiki setup complete!"
echo "View your wiki at: https://github.com/sbdk-dev/sbdk-dev/wiki"
```

## Manual Setup

If you prefer to set up manually:

### 1. Clone the Wiki Repository

```bash
git clone http://local_proxy@127.0.0.1:59050/git/sbdk-dev/sbdk-dev.wiki.git sbdk-wiki
cd sbdk-wiki
```

### 2. Copy Prepared Content

```bash
cp /tmp/sbdk-wiki/*.md .
```

### 3. Commit and Push

```bash
git add .
git commit -m "Initial wiki setup with comprehensive documentation"
git push origin master
```

## What's Included

### Main Pages
- **Home.md** - Wiki home page with overview
- **_Sidebar.md** - Navigation sidebar

### Documentation
- **Getting-Started.md** - Quick start guide
- **User-Guide.md** - Complete feature guide
- **FAQ.md** - Frequently asked questions

### Architecture
- **Architecture.md** - System architecture
- **DLT-Pipeline-Architecture.md** - Data loading architecture
- **DBT-Models.md** - Transformation models

### Configuration
- **Configuration.md** - Configuration guide
- **Configuration-Schema.md** - Schema reference
- **API-Reference.md** - Command reference

### Advanced
- **Server-CLI-Guide.md** - Webhook server
- **Build-Binary.md** - Binary builds
- **CI-CD-Guide.md** - CI/CD setup
- **GitHub-Release-Workflow.md** - Release automation

## Updating the Wiki

After initial setup, you can update the wiki content:

```bash
cd sbdk-wiki

# Edit any markdown files
vim Home.md

# Commit and push
git add .
git commit -m "Update wiki content"
git push origin master
```

Changes appear instantly on GitHub!

## Troubleshooting

### Wiki repository not found (502 error)

**Cause**: Wiki not enabled or initialized on GitHub

**Solution**: Follow Step 1 and Step 2 above to enable and initialize the wiki

### Authentication errors

**Cause**: Git credentials not configured

**Solution**: Configure git credentials or use SSH URL

### Permission denied

**Cause**: No write access to repository

**Solution**: Make sure you have admin/write access to the repository

## Next Steps

1. ✅ Enable wiki on GitHub (Settings → Features → Wikis)
2. ✅ Create first page to initialize wiki
3. ✅ Run the setup script or manual steps above
4. ✅ View your wiki at: https://github.com/sbdk-dev/sbdk-dev/wiki
5. ✅ Share the wiki URL with your users!

---

**Questions?** Open an issue at https://github.com/sbdk-dev/sbdk-dev/issues
