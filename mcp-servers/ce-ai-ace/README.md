# @ce-dot-net/ce-ai-ace

**ACE (Agentic Context Engineering)** - Self-improving LLM contexts via Reflector, Curator, and evolving playbooks.

Based on Stanford/SambaNova/UC Berkeley research: [arXiv:2510.04618](https://arxiv.org/abs/2510.04618)

## 🚀 What is ACE?

ACE is an MCP (Model Context Protocol) server that makes your LLM **learn from experience** and **improve over time** without fine-tuning. It implements the ACE research framework with three key components:

1. **Reflector** - Discovers patterns from your code using Claude
2. **Curator** - Merges and refines patterns using deterministic logic (85% similarity threshold)
3. **Playbook Generator** - Creates evolving context playbooks that grow with your project

## 🎯 Key Features

- ✅ **Works Everywhere** - Claude Code, Cursor, Cline, Claude Desktop, or any MCP-compatible editor
- ✅ **True Pattern Discovery** - No hardcoded rules, learns from YOUR codebase
- ✅ **Research-Based** - Implements ACE paper architecture (Reflector → Curator → Playbook)
- ✅ **Self-Improving** - Patterns evolve with confidence scores and observation counts
- ✅ **Offline Training** - Train on git history for instant pattern discovery
- ✅ **Zero Configuration** - Works out of the box with sensible defaults

## 📦 Installation

### Claude Code

```json
{
  "mcpServers": {
    "ace": {
      "command": "npx",
      "args": ["@ce-dot-net/ce-ai-ace"]
    }
  }
}
```

### Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
{
  "mcpServers": {
    "ace": {
      "command": "npx",
      "args": ["-y", "@ce-dot-net/ce-ai-ace"]
    }
  }
}
```

### Cursor / Cline

```json
{
  "mcpServers": {
    "ace": {
      "command": "npx",
      "args": ["@ce-dot-net/ce-ai-ace"],
      "env": {
        "ACE_STORAGE_PATH": "/path/to/.ace-memory/patterns.db"
      }
    }
  }
}
```

## 🛠️ MCP Tools

ACE provides 6 MCP tools:

- **ace_reflect** - Discover patterns from code
- **ace_train_offline** - Train on git history
- **ace_get_patterns** - Retrieve learned patterns
- **ace_get_playbook** - Generate ACE playbook (Figure 3 format)
- **ace_status** - View statistics
- **ace_clear** - Reset database

## 🔗 Links

- **GitHub**: https://github.com/ce-dot-net/ce-ai-ace
- **Research**: https://arxiv.org/abs/2510.04618
- **NPM**: https://www.npmjs.com/package/@ce-dot-net/ce-ai-ace

## 📝 License

MIT
