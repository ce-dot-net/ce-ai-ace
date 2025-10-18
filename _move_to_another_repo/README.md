# ACE Claude Code Plugin Repository

**This folder contains files that will be moved to a separate plugin repository.**

## Structure

```
_move_to_another_repo/
├── .claude-plugin/           # Marketplace discovery
│   └── marketplace.json
└── plugins/
    └── ace-orchestration/    # Claude Code plugin
        ├── plugin.json       # Plugin configuration
        ├── hooks/            # PostToolUse, PostTaskCompletion
        ├── commands/         # Slash commands
        ├── agents/           # Reflector, domain-discoverer
        └── scripts/          # Helper scripts
```

## Future Repository Setup

### Step 1: Create New Repository
```bash
# On GitHub, create: ce-dot-net/ace-claude-code-plugin
# Then:
cd _move_to_another_repo
git init
git add .
git commit -m "Initial commit: ACE Claude Code plugin"
git remote add origin git@github.com:ce-dot-net/ace-claude-code-plugin.git
git push -u origin main
```

### Step 2: Update Plugin to Use npm Package

Edit `plugins/ace-orchestration/plugin.json`:

```json
{
  "mcpServers": {
    "ace-pattern-learning": {
      "command": "npx",
      "args": ["@ce-dot-net/ce-ai-ace"],
      "env": {
        "ACE_STORAGE_PATH": "${CLAUDE_PLUGIN_ROOT}/.ace-memory/patterns.db",
        "ACE_SIMILARITY_THRESHOLD": "0.85",
        "ACE_CONFIDENCE_HIGH": "0.70",
        "ACE_CONFIDENCE_MEDIUM": "0.30"
      }
    }
  }
}
```

### Step 3: Update Marketplace Discovery

Edit `.claude-plugin/marketplace.json`:

```json
{
  "name": "ace-plugin-marketplace",
  "owner": {
    "name": "ACE Team"
  },
  "description": "Marketplace for ACE (Agentic Context Engineering) Claude Code plugin",
  "plugins": [
    {
      "name": "ace-orchestration",
      "source": "./plugins/ace-orchestration",
      "description": "Self-improving LLM contexts via ACE research framework",
      "version": "2.6.0"
    }
  ]
}
```

## Installation for Users

Once published, users can install via:

```bash
# Clone plugin repo
git clone https://github.com/ce-dot-net/ace-claude-code-plugin.git

# MCP server installs automatically via npx when first used
# No manual npm install needed!
```

## Dependencies

- **MCP Server**: `@ce-dot-net/ce-ai-ace` (from npm)
- **Node.js**: >=18.0.0
- **Claude Code CLI**: Latest version

## Notes

- The MCP server (`@ce-dot-net/ce-ai-ace`) will be installed from npm
- No need to include mcp-servers/ folder in plugin repo
- Plugin references npm package via `npx @ce-dot-net/ce-ai-ace`
