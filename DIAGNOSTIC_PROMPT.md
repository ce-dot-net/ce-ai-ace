# 🔍 ACE Plugin - Installation Diagnostic

**Issue**: Scripts working automatically but manual commands can't find them.

Copy this into your Claude Code CLI in test_ace directory:

---

## 📋 DIAGNOSTIC PROMPT:

```
Help me diagnose the ACE plugin installation. Run these commands:

1. Find the actual plugin installation:

find ~/.claude-code-plugins -name "ace-cycle.py" 2>/dev/null
find ~/.claude/plugins -name "ace-cycle.py" 2>/dev/null
ls -la ~/.claude-code-plugins/
ls -la ~/.claude/plugins/marketplaces/ 2>/dev/null

2. Check environment variables:

echo "CLAUDE_PLUGIN_ROOT: $CLAUDE_PLUGIN_ROOT"
echo "CLAUDE_CODE_PLUGINS: $CLAUDE_CODE_PLUGINS"
env | grep -i claude

3. Check which plugin is actually installed:

cat .claude-code/plugins.json 2>/dev/null || echo "No local plugins.json"
cat ~/.claude-code/config.json 2>/dev/null | grep -A5 plugin

4. Check the ACE hooks configuration:

find . -name "hooks.json" -exec cat {} \;

5. Show me all the output so I can identify where the plugin scripts are located.
```

---

## 🎯 **What We're Looking For:**

### Expected Plugin Locations (one of these):
- `~/.claude-code-plugins/marketplace_*/ace-orchestration/`
- `~/.claude-code-plugins/ace-orchestration@*/`
- `~/.claude/plugins/marketplaces/ce-dot-net/ce-ai-ace/`
- Local `.claude-code/plugins/` (if installed locally)

### Expected Files:
```
scripts/
├── ace-cycle.py              ← Main ACE script
├── generate-playbook.py      ← Playbook generator
├── playbook-delta-updater.py ← Phase 3: Delta updates
├── embeddings_engine.py      ← Phase 3: Embeddings
├── epoch-manager.py          ← Phase 4: Multi-epoch
└── serena-pattern-detector.py ← Phase 5: Serena
```

---

## 🔍 **What the Output Will Tell Us:**

### Scenario A: Plugin Found in ~/.claude-code-plugins/
**Solution**: Set CLAUDE_PLUGIN_ROOT or use full paths

### Scenario B: Plugin Found in ~/.claude/plugins/marketplaces/
**Solution**: Use different path structure

### Scenario C: Plugin Not Found
**Solution**: Need to reinstall or install is corrupted

### Scenario D: Old Version Installed
**Solution**: Phase 3-5 scripts missing, need to update

---

## 🚀 **After Running Diagnostic:**

Based on where we find the scripts, I'll give you:
1. **Correct paths** to use in commands
2. **Environment variable** to set (if needed)
3. **Update commands** (if you have old version)
4. **Test commands** to verify Phase 3-5 features work

---

**Run the diagnostic above and show me the results!** 🔍
