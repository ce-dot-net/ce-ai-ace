# MCP Integration Guide for ACE Plugin

## How Claude Code Plugins Work with MCP Servers

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           Claude Code CLI                        │
│  ┌───────────────────────────────────────────┐  │
│  │  Plugin System                            │  │
│  │  ├─ Hooks (AgentStart, PostToolUse, etc) │  │
│  │  └─ Commands (/ace-status, etc)          │  │
│  └───────────────────────────────────────────┘  │
│                     ↕                            │
│  ┌───────────────────────────────────────────┐  │
│  │  MCP (Model Context Protocol) Layer       │  │
│  │  ├─ serena (symbolic code tools)          │  │
│  │  ├─ github (GitHub API)                   │  │
│  │  ├─ filesystem (file operations)          │  │
│  │  └─ memory-bank (persistent knowledge)    │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                     ↕
          ┌─────────────────────┐
          │  Python Scripts      │
          │  (ACE orchestration) │
          └─────────────────────┘
```

### Plugin vs MCP Server

**Claude Code Plugin** (ACE):
- Extends Claude Code with custom commands and hooks
- Defined in `.claude-plugin/plugin.json`
- Runs Python scripts in response to events
- Lives in your project or `~/.claude-code/plugins/`

**MCP Server** (Serena):
- Provides tools that Claude can use
- Runs as a separate process
- Registered in `~/.claude-code/config.json`
- Examples: serena, filesystem, github, memory-bank

### How ACE Detects Serena MCP

ACE uses a **3-tier detection strategy**:

#### 1. Config Detection (Highest Confidence)
Checks `~/.claude-code/config.json` or `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "serena": {
      "command": "npx",
      "args": ["-y", "@serena/mcp-server"]
    }
  }
}
```

#### 2. Filesystem Detection (Medium Confidence)
Checks for Serena project directories:
- `.serena/` in project root
- `.serena/memories/` with knowledge files
- `~/.serena/` in home directory

#### 3. Tool List Detection (Low Confidence)
Attempts to enumerate available MCP tools:
- `mcp__serena__find_symbol`
- `mcp__serena__get_symbols_overview`
- etc.

### Implementation in ACE

#### Detection Script (`detect-mcp-serena.py`)

```python
def detect_serena() -> Dict:
    """
    Comprehensive Serena detection using multiple methods.

    Returns:
        {
            'serena_available': bool,
            'detection_method': str,
            'confidence': 'high' | 'medium' | 'low',
            'mcp_tools': [...]
        }
    """
```

#### Hybrid Pattern Detection (`serena-pattern-detector.py`)

```python
def detect_patterns_hybrid(file_path: str, code: str) -> List[Dict]:
    """
    Strategy:
    1. Auto-detect if Serena MCP is available
    2. If available, use Serena (AST-based, accurate)
    3. Fall back to regex if unavailable
    """
    if is_serena_available():
        # Try Serena symbolic detection
        serena_patterns = detect_patterns_with_serena(file_path)
        if serena_patterns:
            return serena_patterns

    # Fallback to regex
    return regex_detect_patterns(code, file_path)
```

### When to Use MCP vs Standalone Scripts

| Scenario | Use MCP? | Reason |
|----------|----------|--------|
| **Symbol-level code analysis** | ✅ Yes (Serena) | AST-aware, accurate symbol detection |
| **Pattern detection** | ⚠️ Optional | Regex works, Serena is better but not required |
| **File reading** | ✅ Yes (filesystem) | Standard MCP provides this |
| **Memory storage** | ✅ Yes (memory-bank) | Cross-session knowledge |
| **GitHub operations** | ✅ Yes (github) | API integration built-in |
| **Database operations** | ❌ No | Use Python scripts with SQLite |
| **Playbook generation** | ❌ No | Pure Python, no need for MCP |

### ACE's Hybrid Approach

ACE is designed to **work with or without Serena**:

✅ **With Serena MCP** (Better):
- AST-based pattern detection
- Symbol-level accuracy
- Reference tracking
- Memory integration

✅ **Without Serena MCP** (Still Works):
- Regex-based pattern detection
- File-level analysis
- SQLite for pattern storage
- Markdown for playbooks

### Configuration Examples

#### Enable Serena for ACE (Optional Enhancement)

Add to `~/.claude-code/config.json`:

```json
{
  "mcpServers": {
    "serena": {
      "command": "npx",
      "args": ["-y", "@serena/mcp-server"],
      "env": {
        "SERENA_PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

#### Project-Level Serena Config

Create `.serena/project.yml`:

```yaml
name: ce-ai-ace
description: ACE plugin for Claude Code
language: python
```

### Calling MCP Tools from Python Scripts

**Current Status**: ACE uses placeholders for Serena calls.

**Future Implementation** (when needed):

```python
# Option 1: Via subprocess (current approach)
import subprocess
import json

result = subprocess.run([
    'claude-code-mcp-call',
    'serena',
    'find_symbol',
    json.dumps({'name_path': 'ClassName', 'relative_path': 'file.py'})
], capture_output=True)

# Option 2: Via MCP client library (if available)
from claude_code_mcp import call_tool

symbols = call_tool('mcp__serena__find_symbol', {
    'name_path': 'ClassName',
    'relative_path': 'file.py'
})
```

### Benefits of ACE's Approach

1. **No Hard Dependencies**: Works out-of-the-box without Serena
2. **Graceful Degradation**: Falls back to regex seamlessly
3. **Performance**: Caches detection result (only checks once)
4. **Flexibility**: Users can enable Serena when they want better accuracy
5. **Portability**: ACE plugin works on any Claude Code installation

### Testing the Integration

```bash
# Check if Serena is detected
python3 scripts/detect-mcp-serena.py

# Test hybrid pattern detection
python3 scripts/serena-pattern-detector.py

# Run ACE cycle (will auto-detect Serena)
python3 scripts/ace-cycle.py < test_input.json
```

### Troubleshooting

#### Serena not detected but installed?

1. Check config files:
   ```bash
   cat ~/.claude-code/config.json
   cat .claude/settings.local.json
   ```

2. Verify Serena directories:
   ```bash
   ls -la .serena/
   ls -la ~/.serena/
   ```

3. Test Serena directly:
   ```bash
   npx @serena/mcp-server --version
   ```

#### Want to force Serena usage?

Set environment variable:
```bash
export ACE_FORCE_SERENA=true
python3 scripts/ace-cycle.py
```

#### Want to disable Serena detection?

Set environment variable:
```bash
export ACE_DISABLE_SERENA=true
python3 scripts/ace-cycle.py
```

### Best Practices

1. **Start without Serena**: ACE works great with regex
2. **Add Serena later**: When you need symbol-level accuracy
3. **Cache detection**: Don't check on every pattern detection
4. **Graceful fallback**: Always have regex as backup
5. **Log clearly**: Show which detection method is being used

### Future Enhancements

- [ ] Direct MCP client library integration
- [ ] Real-time tool availability checking
- [ ] Automatic Serena installation prompt
- [ ] Per-language detection strategies
- [ ] Performance benchmarking (Serena vs regex)

---

## Summary

ACE demonstrates **best practices for Claude Code plugin/MCP integration**:

✅ **Works standalone** (no MCP required)
✅ **Detects available MCP servers** (smart auto-configuration)
✅ **Falls back gracefully** (regex when Serena unavailable)
✅ **Caches detection** (performance optimization)
✅ **Clear logging** (users know what's happening)

This makes ACE **universally compatible** with any Claude Code installation, while still taking advantage of Serena when available!
