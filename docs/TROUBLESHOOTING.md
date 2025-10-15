# ACE Plugin Troubleshooting Guide

## 🚨 API Error 400: Tool Use Concurrency Issues

**Error Message**:
```
API Error: 400 due to tool use concurrency issues. Run /rewind to recover the conversation.
```

### Root Cause

This error occurs when you have **duplicate MCP servers** installed:
- Global Serena: `serena` (in `~/.claude.json`)
- Plugin Serena: `serena-ace` (from ACE plugin)

Both servers use the same underlying `mcp-serena` package, causing Claude Code to receive duplicate tool definitions, which creates tool ID collisions.

### Solution

**Option 1: Remove Global Serena (Recommended)**

```bash
# Remove global Serena MCP
claude mcp remove serena --scope global

# Restart Claude Code
```

**Option 2: Manual Removal**

Edit `~/.claude.json` and remove the `"serena"` entry:

```json
{
  "mcpServers": {
    "serena": { ... },  // ← DELETE THIS ENTIRE BLOCK
    "github": { ... },
    ...
  }
}
```

**Option 3: Keep Global, Disable Plugin**

If you prefer global Serena:

```bash
# Disable ACE plugin (loses pattern learning features)
/plugin disable ace-orchestration
```

### Verification

After removal, verify the conflict is gone:

```bash
# Check MCP servers
claude mcp list

# Should see:
# - serena-ace (from plugin) ✅
# - chromadb-ace (from plugin) ✅
# - NO "serena" entry ✅
```

---

## ⚠️  Automatic Detection

ACE plugin **automatically checks** for MCP conflicts on session start.

If you see this warning at startup:

```
⚠️  **MCP CONFLICT DETECTED** ⚠️

Both 'serena' and 'serena-ace' MCP servers are installed.
```

Follow the resolution steps above **immediately** to prevent 400 errors.

---

## 🔍 Other MCP Conflicts

### ChromaDB Conflict

**Symptoms**: Similar 400 errors with ChromaDB tools

**Solution**:
```bash
# Remove global ChromaDB
claude mcp remove chromadb --scope global

# Plugin will use chromadb-ace instead
```

### Generic MCP Conflict

**Check for duplicates**:
```bash
# List all MCPs
claude mcp list

# Look for pairs like:
# - foo + foo-ace
# - bar + bar-ace
```

**Rule**: Keep only the `-ace` versions (from plugin) or only the global versions (not both).

---

## 🐛 Plugin Not Working

### Hooks Not Triggering

**Check hooks are registered**:
```bash
cat hooks/hooks.json | python3 -m json.tool
```

**Verify plugin is enabled**:
```bash
/plugin list
# Should show: ace-orchestration [enabled]
```

**Check logs**:
```bash
# Look for hook execution errors
tail -f ~/.claude-code/logs/latest.log | grep -i "hook\|error"
```

### Database Not Initialized

**Symptoms**: No patterns detected, `/ace-status` shows 0 patterns

**Solution**:
```bash
# Reinitialize database
cd /path/to/plugin
./install.sh

# Or manually:
mkdir -p .ace-memory/chromadb .ace-memory/embeddings
python3 scripts/initialize-db.py
```

### MCPs Not Auto-Installing

**Symptoms**: "mcp-server-chromadb not found" or "mcp-serena not found"

**Solution**:
```bash
# Install uvx (required for MCP auto-install)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart Claude Code
```

**Verify uvx**:
```bash
which uvx
uvx --version
```

---

## 📊 Pattern Learning Issues

### Patterns Not Being Detected

**Check ACE cycle is running**:
```bash
# Edit any file
# Check stderr for:
# "🔍 ACE: Analyzing code changes..."
```

**Verify hooks**:
```bash
# PostToolUse hook should trigger after Edit/Write
grep "PostToolUse" hooks/hooks.json
```

**Check database**:
```bash
sqlite3 .ace-memory/patterns.db "SELECT COUNT(*) FROM patterns"
# Should show number > 0 after editing files
```

### Low Confidence Patterns

**Symptoms**: All patterns show 0% confidence

**Cause**: Not enough observations (need ~10+ per pattern)

**Solution**: Keep coding! ACE learns from:
- Code edits (Edit/Write tools)
- Test results (npm test)
- Execution feedback

### Patterns Not Showing in CLAUDE.md

**Check playbook generation**:
```bash
# Manually generate
python3 scripts/generate-playbook.py

# Check output
cat CLAUDE.md
```

**Verify SessionEnd hook**:
```bash
# SessionEnd should regenerate playbook
grep "SessionEnd" hooks/hooks.json
```

---

## 🔧 Advanced Troubleshooting

### Enable Debug Mode

Set environment variable for verbose logging:

```bash
export ACE_DEBUG=1
export ACE_VERBOSE=1

# Run Claude Code
claude
```

### Check MCP Server Status

```bash
# List running MCP servers
ps aux | grep mcp

# Should see:
# - uvx mcp-server-chromadb
# - uvx mcp-serena
```

### Test MCP Servers Manually

**ChromaDB**:
```bash
uvx mcp-server-chromadb
# Should start without errors
```

**Serena**:
```bash
uvx --from mcp-serena mcp-serena
# Should start without errors
```

### Reset ACE State

**Nuclear option** - wipes all learned patterns:

```bash
# Backup first!
cp -r .ace-memory .ace-memory.backup

# Reset
rm -rf .ace-memory
./install.sh

# Or via command:
/ace-clear --confirm
```

---

## 📚 Additional Resources

- [Usage Guide](USAGE_GUIDE.md) - Complete feature walkthrough
- [MCP Auto-Install](MCP_AUTO_INSTALL.md) - MCP configuration details
- [Gap Analysis](GAP_ANALYSIS.md) - Implementation status
- [GitHub Issues](https://github.com/ce-dot-net/ce-ai-ace/issues) - Report bugs

---

## 🆘 Still Having Issues?

1. **Check GitHub Issues**: [ce-dot-net/ce-ai-ace/issues](https://github.com/ce-dot-net/ce-ai-ace/issues)
2. **Enable debug mode** (see above) and share logs
3. **File a bug report** with:
   - Error message
   - Steps to reproduce
   - Output of `claude mcp list`
   - Output of `/ace-status`

---

**Last Updated**: 2025-10-15
**Plugin Version**: 2.0.0
