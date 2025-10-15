#!/bin/bash
set -e

# ACE Plugin Installation Script
#
# ⚠️  NOTE: This script is DEPRECATED for end users!
#
# Users should install via Claude Code CLI plugin system:
#   /plugin marketplace add ce-dot-net/ce-ai-ace
#   /plugin install ace-orchestration@ace-plugin-marketplace
#
# This script is only for development/testing purposes:
# - Creates .ace-memory/ directory structure
# - Initializes SQLite database
#
# MCPs are now auto-installed via plugin.json when the plugin loads.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

echo "⚠️  DEPRECATION NOTICE"
echo "===================="
echo ""
echo "This install.sh script is for DEVELOPMENT/TESTING ONLY."
echo ""
echo "For end users, install via Claude Code CLI:"
echo "  /plugin marketplace add ce-dot-net/ce-ai-ace"
echo "  /plugin install ace-orchestration@ace-plugin-marketplace"
echo ""
echo "MCPs auto-install via plugin.json - no manual setup needed!"
echo ""
echo "Press Ctrl+C to cancel, or wait 5 seconds to continue (dev mode)..."
sleep 5
echo ""
echo "🚀 Installing ACE Plugin (Development Mode)"
echo "============================================"
echo ""

# Step 1: Create ACE memory directory
echo "📁 Setting up ACE memory storage..."
ACE_MEMORY_DIR="$SCRIPT_DIR/.ace-memory"
mkdir -p "$ACE_MEMORY_DIR"
mkdir -p "$ACE_MEMORY_DIR/chromadb"
mkdir -p "$ACE_MEMORY_DIR/embeddings"

echo "✅ Directory structure created:"
echo "   - $ACE_MEMORY_DIR"
echo "   - $ACE_MEMORY_DIR/chromadb"
echo "   - $ACE_MEMORY_DIR/embeddings"

# Step 2: Initialize database if needed
if [ ! -f "$ACE_MEMORY_DIR/patterns.db" ]; then
    echo ""
    echo "📊 Initializing pattern database..."
    if [ -f "$SCRIPTS_DIR/initialize-db.py" ]; then
        python3 "$SCRIPTS_DIR/initialize-db.py" 2>/dev/null || echo "⚠️  initialize-db.py not found, skipping"
    else
        echo "⚠️  initialize-db.py not found, database will be created on first use"
    fi
else
    echo ""
    echo "✅ Pattern database already exists"
fi

echo ""
echo "✅ ACE memory storage ready"
echo ""

# Step 3: Verify plugin structure
echo "🔍 Verifying plugin structure..."
PLUGIN_JSON="$SCRIPT_DIR/.claude-plugin/plugin.json"
HOOKS_JSON="$SCRIPT_DIR/hooks/hooks.json"

if [ -f "$PLUGIN_JSON" ]; then
    echo "✅ plugin.json found"
    # Check if MCPs are defined
    if grep -q "mcpServers" "$PLUGIN_JSON"; then
        echo "✅ MCPs configured in plugin.json"
    else
        echo "⚠️  No MCPs found in plugin.json"
    fi
else
    echo "❌ ERROR: plugin.json not found!"
    exit 1
fi

if [ -f "$HOOKS_JSON" ]; then
    echo "✅ hooks.json found"
else
    echo "⚠️  hooks.json not found"
fi

echo ""

# Done
echo "🎉 Development Setup Complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 Next Steps:"
echo ""
echo "  For development testing:"
echo "    1. The plugin is ready to test locally"
echo "    2. MCPs defined in plugin.json will auto-install"
echo "    3. Hooks are configured and ready"
echo ""
echo "  For end users:"
echo "    1. Install via Claude Code CLI plugin system"
echo "    2. /plugin marketplace add ce-dot-net/ce-ai-ace"
echo "    3. /plugin install ace-orchestration@ace-plugin-marketplace"
echo ""
echo "📚 Documentation:"
echo "  - Usage Guide: docs/USAGE_GUIDE.md"
echo "  - MCP Auto-Install: docs/MCP_AUTO_INSTALL.md"
echo "  - Gap Analysis: docs/GAP_ANALYSIS.md"
echo ""
echo "💡 ACE Commands:"
echo "  - /ace-status              View learning statistics"
echo "  - /ace-patterns            List learned patterns"
echo "  - /ace-force-reflect FILE  Analyze a specific file"
echo "  - /ace-clear --confirm     Reset pattern database"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ACE Plugin is ready! Happy coding! 🎨"
