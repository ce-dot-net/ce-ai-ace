# ACE Plugin - Installation Guide

## 🚀 Quick Install (Recommended)

### Option 1: Install from GitHub (After Push)

1. **Push this repo to GitHub first**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/ce-ai-ace.git
git branch -M main
git push -u origin main
```

2. **Add the marketplace in Claude Code**:
```bash
/plugin marketplace add YOUR_USERNAME/ce-ai-ace
```

3. **Install the plugin**:
```bash
/plugin install ace-orchestration@ace-plugin-marketplace
```

4. **Restart Claude Code** to activate!

---

### Option 2: Install Locally (For Testing)

1. **Add local marketplace**:
```bash
/plugin marketplace add file:///Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace
```

2. **Install the plugin**:
```bash
/plugin install ace-orchestration@ace-plugin-marketplace
```

3. **Restart Claude Code**

---

## ✅ Verify Installation

After restart, check if hooks are loaded:
```bash
# Plugin should be active
/plugin
```

The ACE plugin runs **automatically** - no manual commands needed!

---

## 📋 What Happens Automatically

Every time you edit code in Claude Code:

1. ✅ **Detects patterns** (Python, JS, TS)
2. ✅ **Gathers test results**
3. ✅ **Reflects on effectiveness** (via sequential-thinking MCP)
4. ✅ **Curates patterns** (deterministic merging)
5. ✅ **Updates CLAUDE.md** (your evolving playbook)

---

## 🔧 Dependencies (Optional)

The plugin works without these, but for full functionality:

### Install MCP Servers

```bash
cd /Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace
npm install
npm run install-mcps
```

This installs:
- `@modelcontextprotocol/server-memory` - Pattern storage
- `@modelcontextprotocol/server-sequential-thinking` - Reflection

**Without MCPs**: Plugin still works, uses test results only (no deep reflection)

---

## 🎯 Why npm install?

You DON'T need `npm install` in Claude Code projects!

`npm install` is only needed **in the plugin folder itself** if you want to:
- Run tests: `npm test`
- Install MCP servers: `npm run install-mcps`
- Develop the plugin further

**For users**: Just install via `/plugin` command - that's it!

---

## 🗑️ Uninstall

```bash
/plugin disable ace-orchestration
/plugin uninstall ace-orchestration
/plugin marketplace remove ace-plugin-marketplace
```

---

## 🐛 Troubleshooting

### Plugin Not Loading?

1. Check plugin is in marketplace:
   ```bash
   /plugin
   ```

2. Verify structure:
   ```bash
   ls -la .claude-plugin/
   # Should see: plugin.json, marketplace.json
   ```

3. Restart Claude Code

### No Patterns Detected?

- Plugin only detects: `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files
- Check console for "🔄 ACE: Starting reflection cycle..."
- If silent, hooks may not be registered

### CLAUDE.md Not Updating?

- Check `.ace-memory/` directory exists
- Run in plugin folder: `npm test` to verify functionality

---

## 📖 Learn More

- **README.md** - Full documentation
- **QUICKSTART.md** - Detailed usage
- **docs/ACE_RESEARCH.md** - Research background

---

**That's it! No npm install needed in your projects - the plugin just works! 🎉**
