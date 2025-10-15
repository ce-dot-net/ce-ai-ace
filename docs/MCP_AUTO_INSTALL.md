# Automatic MCP Installation

**Status**: ✅ COMPLETE (Phase 3+)

## Overview

The ACE plugin uses Claude Code CLI's built-in MCP auto-installation feature. Users **do not** need to manually install MCPs or run `install.sh`.

## How It Works

### 1. Plugin Structure

```
ce-ai-ace/
├── .claude-plugin/
│   └── plugin.json         # References hooks
├── .mcp.json               # ⭐ MCP configuration (auto-installs!)
├── hooks/
│   └── hooks.json          # Hook definitions
└── scripts/
    ├── ace-cycle.py        # Uses MCPs
    └── embeddings_engine.py # Uses ChromaDB MCP
```

### 2. `.mcp.json` Configuration

```json
{
  "mcpServers": {
    "chromadb": {
      "command": "uvx",
      "args": ["mcp-server-chromadb"],
      "env": {
        "CHROMA_DB_PATH": "${CLAUDE_PLUGIN_ROOT}/.ace-memory/chromadb"
      }
    },
    "serena": {
      "command": "uvx",
      "args": ["--from", "mcp-serena", "mcp-serena"]
    }
  }
}
```

**Key Features**:
- ✅ `${CLAUDE_PLUGIN_ROOT}` - Automatic path resolution
- ✅ `uvx` - Zero-dependency installation (auto-installs packages)
- ✅ Environment variables - Custom configuration per plugin

### 3. Installation Flow

```
User: /plugin install ace-orchestration
    ↓
Claude Code CLI: Reads .mcp.json
    ↓
Claude Code CLI: Registers MCP servers
    ↓
First MCP call (e.g., chromadb):
    ↓
uvx: Downloads mcp-server-chromadb (automatic)
    ↓
uvx: Installs ChromaDB + sentence-transformers (bundled)
    ↓
MCP: Starts server process
    ↓
✅ Ready to use!
```

**User action**: ZERO manual steps!

### 4. What Gets Auto-Installed

**ChromaDB MCP**:
- Package: `mcp-server-chromadb` (via uvx)
- Includes: ChromaDB + sentence-transformers
- Storage: `${CLAUDE_PLUGIN_ROOT}/.ace-memory/chromadb/`
- Purpose: Semantic embeddings (Tier 2 fallback)

**Serena MCP**:
- Package: `mcp-serena` (via uvx)
- Purpose: Symbolic code analysis (AST-aware pattern detection)
- Features: `find_symbol`, `find_referencing_symbols`, etc.

## User Experience

### Before (Old Approach - Manual)

```bash
# User had to do this manually:
git clone https://github.com/ce-dot-net/ce-ai-ace
cd ce-ai-ace
./install.sh              # Manual script
# Edit ~/.config/claude-code/config.json manually
# Install MCPs separately
pip install chromadb      # Extra database installation
```

❌ **Problems**:
- Multiple manual steps
- Error-prone config editing
- Extra database installation
- Conflicts with existing MCPs

### After (Current - Automatic)

```bash
# User does this:
/plugin marketplace add ce-dot-net/ce-ai-ace
/plugin install ace-orchestration@ace-plugin-marketplace
# Restart Claude Code
```

✅ **Benefits**:
- **One command** installation
- **Zero manual config**
- **No extra installations**
- **Automatic conflict resolution**

## For Developers

### Testing MCP Auto-Install

1. **Remove existing MCPs** (optional, for clean test):
   ```bash
   # Edit ~/.config/claude-code/config.json
   # Remove "chromadb" and "serena" entries
   ```

2. **Install plugin**:
   ```bash
   /plugin install ace-orchestration@ace-plugin-marketplace
   ```

3. **Verify MCPs are registered**:
   ```bash
   # Check Claude Code logs for:
   # "Registered MCP server: chromadb"
   # "Registered MCP server: serena"
   ```

4. **Trigger first MCP call**:
   ```python
   # Edit any Python file
   # ACE hooks will trigger
   # embeddings_engine.py calls ChromaDB
   # uvx auto-installs mcp-server-chromadb
   ```

5. **Verify installation**:
   ```bash
   ls ${CLAUDE_PLUGIN_ROOT}/.ace-memory/chromadb/
   # Should see ChromaDB database files
   ```

### Conflict Detection

The old `scripts/generate-mcp-config.py` and `scripts/mcp-conflict-detector.py` are **no longer needed** for end users. Claude Code CLI handles conflicts automatically:

- If user has existing `chromadb` MCP → Plugin's version is namespaced or skipped
- If user has existing `serena` MCP → Plugin uses existing installation

### Environment Variables

**Available in `.mcp.json`**:
- `${CLAUDE_PLUGIN_ROOT}` - Plugin installation directory
- `${PROJECT_ROOT}` - Current project root
- `${HOME}` - User home directory

**Example**:
```json
{
  "mcpServers": {
    "chromadb": {
      "env": {
        "CHROMA_DB_PATH": "${CLAUDE_PLUGIN_ROOT}/.ace-memory/chromadb",
        "CHROMA_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Backwards Compatibility

**Old installations (via `install.sh`)**: Still work, but deprecated.

**Migration path**:
1. Uninstall old plugin (remove from config)
2. Install via `/plugin install`
3. `.mcp.json` takes over MCP management

## References

- [Claude Code Plugins Docs](https://docs.claude.com/en/docs/claude-code/plugins)
- [Claude Code MCP Docs](https://docs.claude.com/en/docs/claude-code/mcp)
- [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)

---

**Summary**: Users install the plugin, MCPs auto-install via `.mcp.json`, zero manual steps! 🎉
