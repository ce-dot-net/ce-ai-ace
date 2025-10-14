# ACE Plugin - Installation Guide

## 🚀 Quick Install

### Install from GitHub Marketplace

1. **Add the marketplace in Claude Code**:
```bash
/plugin marketplace add ce-dot-net/ce-ai-ace
```

2. **Install the plugin**:
```bash
/plugin install ace-orchestration@ace-plugin-marketplace
```

3. **Restart Claude Code** to activate!

---

## ✅ Verify Installation

After restart, check if the plugin is loaded:
```bash
/plugin
```

You should see `ace-orchestration` listed as active.

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

That's it! The plugin is **self-contained**:
- ✅ SQLite database (Python standard library)
- ✅ Pattern detection (pure regex)
- ✅ Deterministic curation (string similarity)
- ✅ No external dependencies

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

2. Verify marketplace was added:
   ```bash
   /plugin marketplace list
   ```

3. Restart Claude Code

### No Patterns Detected?

- Plugin only detects: `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files
- Check console for "🔄 ACE: Starting reflection cycle..."
- If silent, hooks may not be registered

### CLAUDE.md Not Updating?

- Check `.ace-memory/` directory exists
- Run `/ace-status` to verify patterns are being learned
- Check for errors in Claude Code console

---

## 📖 Learn More

- **README.md** - Full documentation
- **QUICKSTART.md** - Detailed usage guide
- **docs/ACE_RESEARCH.md** - Research background

---

**That's it! Just install and the plugin works automatically! 🎉**
