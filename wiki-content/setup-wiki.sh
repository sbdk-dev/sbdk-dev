#!/bin/bash

# SBDK.dev GitHub Wiki Setup Script
# This script automates the setup of your GitHub wiki with prepared documentation

set -e  # Exit on error

# Configuration
WIKI_URL="https://github.com/sbdk-dev/sbdk-dev.wiki.git"
WIKI_DIR="$HOME/sbdk-wiki"
# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📚 SBDK.dev GitHub Wiki Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "git is not installed. Please install git first."
        exit 1
    fi

    # Check if source directory exists
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

check_wiki_enabled() {
    print_warning "Before continuing, make sure you have:"
    echo "  1. Enabled the Wiki in GitHub repository settings"
    echo "  2. Created at least one page to initialize the wiki"
    echo ""
    echo "Steps:"
    echo "  • Go to: https://github.com/sbdk-dev/sbdk-dev/settings"
    echo "  • Enable 'Wikis' under Features section"
    echo "  • Go to Wiki tab and create the first page"
    echo ""
    read -p "Have you completed these steps? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please enable and initialize the wiki first, then run this script again."
        exit 1
    fi
}

clone_wiki() {
    print_info "Cloning wiki repository..."

    # Remove existing directory if it exists
    if [ -d "$WIKI_DIR" ]; then
        print_warning "Wiki directory already exists. Removing..."
        rm -rf "$WIKI_DIR"
    fi

    if git clone "$WIKI_URL" "$WIKI_DIR" 2>&1; then
        print_success "Wiki repository cloned successfully"
    else
        print_error "Failed to clone wiki repository"
        print_error "Make sure the wiki is enabled and initialized on GitHub"
        exit 1
    fi
}

copy_content() {
    print_info "Copying prepared wiki content..."

    cd "$WIKI_DIR"

    # Copy all markdown files except setup instructions
    for file in "$SOURCE_DIR"/*.md; do
        filename=$(basename "$file")
        if [ "$filename" != "SETUP-INSTRUCTIONS.md" ]; then
            cp "$file" .
            print_success "Copied: $filename"
        fi
    done
}

commit_and_push() {
    print_info "Committing changes..."

    cd "$WIKI_DIR"

    git add .

    # Check if there are changes to commit
    if git diff --staged --quiet; then
        print_warning "No changes to commit"
        return
    fi

    git commit -m "Initial wiki setup with comprehensive documentation

This commit sets up the SBDK.dev GitHub wiki with complete documentation:

📚 Main Pages:
- Home page with overview and quick start
- Sidebar navigation for easy browsing

📖 Documentation:
- Getting Started guide
- User Guide with complete feature walkthrough
- FAQ with common questions and solutions

🏗️ Architecture:
- System Architecture overview
- DLT Pipeline Architecture details
- DBT Models structure and conventions

⚙️ Configuration:
- Configuration guide
- Complete Configuration Schema reference
- API Reference for all commands

🚀 Advanced Topics:
- Server CLI Guide (webhooks)
- Binary Build instructions
- CI/CD Guide for automation
- GitHub Release Workflow

All documentation is sourced from the docs/ folder and
formatted for optimal GitHub wiki presentation.

Generated with SBDK.dev wiki setup tool"

    print_success "Changes committed"

    print_info "Pushing to GitHub..."

    if git push origin master 2>&1; then
        print_success "Wiki pushed to GitHub successfully!"
    else
        print_error "Failed to push to GitHub"
        print_error "You may need to configure git credentials"
        exit 1
    fi
}

show_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Wiki setup complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_info "Your wiki is now live at:"
    echo "  🌐 https://github.com/sbdk-dev/sbdk-dev/wiki"
    echo ""
    print_info "Wiki content location:"
    echo "  📂 $WIKI_DIR"
    echo ""
    print_info "To update the wiki in the future:"
    echo "  1. cd $WIKI_DIR"
    echo "  2. Edit markdown files"
    echo "  3. git add . && git commit -m 'Update wiki'"
    echo "  4. git push origin master"
    echo ""
    print_info "Pages included:"
    cd "$WIKI_DIR"
    ls -1 *.md | sed 's/^/  • /'
    echo ""
}

# Main execution
main() {
    print_header
    check_prerequisites
    check_wiki_enabled
    clone_wiki
    copy_content
    commit_and_push
    show_summary
}

# Run main function
main
