# SBDK.dev GitHub Wiki - Ready to Deploy!

This directory contains your complete GitHub wiki content, ready to be pushed to your repository.

## 📚 What's Inside

All your documentation from the `docs/` folder has been formatted and prepared for GitHub wiki:

### Core Pages
- **Home.md** - Welcome page with quick start
- **_Sidebar.md** - Navigation menu (appears on every page)

### Documentation (13 Pages)
- Getting Started
- User Guide
- FAQ
- Architecture
- DLT Pipeline Architecture
- DBT Models
- Configuration
- Configuration Schema
- API Reference
- Server CLI Guide
- Build Binary
- CI/CD Guide
- GitHub Release Workflow

## 🚀 Quick Setup

### Option 1: Automatic Setup (Recommended)

```bash
cd /tmp/sbdk-wiki
./setup-wiki.sh
```

The script will:
1. ✅ Check prerequisites
2. ✅ Prompt you to enable wiki on GitHub (if not done)
3. ✅ Clone the wiki repository
4. ✅ Copy all prepared content
5. ✅ Commit and push to GitHub
6. ✅ Show you the live wiki URL

### Option 2: Manual Setup

1. **Enable the wiki on GitHub:**
   - Go to https://github.com/sbdk-dev/sbdk-dev/settings
   - Under "Features", check "Wikis"
   - Click Save

2. **Initialize the wiki:**
   - Go to the Wiki tab
   - Click "Create the first page"
   - Add any content and save

3. **Clone and push:**
   ```bash
   # Clone the wiki repository
   git clone http://local_proxy@127.0.0.1:59050/git/sbdk-dev/sbdk-dev.wiki.git
   cd sbdk-dev.wiki

   # Copy prepared content
   cp /tmp/sbdk-wiki/*.md .

   # Remove setup files
   rm SETUP-INSTRUCTIONS.md README.md

   # Commit and push
   git add .
   git commit -m "Initial wiki setup with comprehensive documentation"
   git push origin master
   ```

4. **View your wiki:**
   - https://github.com/sbdk-dev/sbdk-dev/wiki

## 📝 Important Notes

### Before Running Setup

The GitHub wiki must be **enabled and initialized** before you can clone it:

1. Enable in repository settings
2. Create at least one page (to initialize the repository)
3. Then run the setup script

### Wiki URL Structure

GitHub wikis have special URLs:
- **Wiki Home**: `https://github.com/sbdk-dev/sbdk-dev/wiki`
- **Specific Page**: `https://github.com/sbdk-dev/sbdk-dev/wiki/Page-Name`
- **Edit Page**: `https://github.com/sbdk-dev/sbdk-dev/wiki/Page-Name/_edit`

### Page Naming

GitHub wiki converts filenames to page titles:
- `Getting-Started.md` → "Getting Started" page
- `API-REFERENCE.md` → "API REFERENCE" page
- Spaces are created from hyphens and underscores

## 🔄 Updating the Wiki

After initial setup, update your wiki content:

```bash
cd ~/sbdk-wiki  # Or wherever you cloned it

# Edit any markdown file
vim Home.md

# Commit and push
git add .
git commit -m "Update documentation"
git push origin master
```

Changes appear **instantly** on GitHub!

## 🌐 Linking from Your Website

After setup, point your website to the wiki:

```html
<!-- Link to wiki home -->
<a href="https://github.com/sbdk-dev/sbdk-dev/wiki">Documentation</a>

<!-- Link to specific pages -->
<a href="https://github.com/sbdk-dev/sbdk-dev/wiki/Getting-Started">Getting Started</a>
<a href="https://github.com/sbdk-dev/sbdk-dev/wiki/API-Reference">API Reference</a>
```

Or in your README:

```markdown
📖 [Documentation Wiki](https://github.com/sbdk-dev/sbdk-dev/wiki)
```

## 📊 Wiki Features

Your wiki includes:

✅ **Navigation Sidebar** - Easy browsing on every page
✅ **Search** - GitHub's built-in wiki search
✅ **Version Control** - Full git history
✅ **Markdown** - Rich formatting with GitHub-flavored markdown
✅ **Images** - Support for screenshots and diagrams
✅ **Links** - Internal links between pages
✅ **Edit History** - Track all changes

## 🛠️ Maintenance

### Syncing with docs/ folder

If you update docs in your repository:

```bash
# Copy updated docs
cp docs/*.md /tmp/sbdk-wiki/

# Rename to wiki format
cd /tmp/sbdk-wiki
for file in *.md; do
    mv "$file" "${file//_/-}"
done

# Update wiki
cd ~/sbdk-wiki
cp /tmp/sbdk-wiki/*.md .
git add .
git commit -m "Sync with latest docs"
git push origin master
```

### Automation

You can automate wiki updates with GitHub Actions:

```yaml
# .github/workflows/sync-wiki.yml
name: Sync Wiki
on:
  push:
    paths:
      - 'docs/**'
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update Wiki
        # Add script to sync docs to wiki
```

## 📖 Resources

- **Setup Instructions**: See `SETUP-INSTRUCTIONS.md` for detailed steps
- **GitHub Wiki Docs**: https://docs.github.com/en/communities/documenting-your-project-with-wikis
- **Markdown Guide**: https://guides.github.com/features/mastering-markdown/

## ❓ Troubleshooting

### Wiki clone fails (502 error)

**Problem**: Wiki not initialized on GitHub

**Solution**: Create at least one page in the wiki through GitHub's web interface

### Changes not showing

**Problem**: Cache or push failed

**Solution**:
- Hard refresh browser (Ctrl+Shift+R)
- Verify push succeeded: `git log --oneline`
- Check GitHub wiki page directly

### Permission denied

**Problem**: No write access

**Solution**: Make sure you have admin/write access to the repository

## 🎉 Next Steps

1. Run `./setup-wiki.sh` to deploy your wiki
2. Visit https://github.com/sbdk-dev/sbdk-dev/wiki
3. Share the wiki URL with your users!
4. Update your website/README to link to the wiki

---

**Questions?** Open an issue at https://github.com/sbdk-dev/sbdk-dev/issues
