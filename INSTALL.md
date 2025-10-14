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

## 🔧 Dependencies

### Required:
- **Python 3.7+** (for pattern detection scripts)
  - Uses only standard library - no `pip install` needed!
- **Claude Code CLI 2.0+**

### Optional (for development):
- **Node.js** (only if you want to run old tests)

That's it! The plugin is **self-contained**:
- ✅ SQLite database (Python standard library)
- ✅ Pattern detection (pure regex)
- ✅ Deterministic curation (string similarity)
- ✅ No external dependencies

**For users**: Just install via `/plugin` command - that's all you need!

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
