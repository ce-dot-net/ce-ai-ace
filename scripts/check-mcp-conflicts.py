#!/usr/bin/env python3
"""
ACE Plugin - MCP Conflict Checker

Runs on SessionStart to detect MCP conflicts (especially Serena).
Outputs warning to context if conflicts detected.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

def find_claude_config() -> Optional[Path]:
    """Find Claude Code config file."""
    possible_paths = [
        Path.home() / '.claude.json',
        Path.home() / '.config' / 'claude-code' / 'config.json',
        Path.home() / '.claude-code' / 'config.json',
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None

def load_mcp_servers(config_path: Path) -> Dict[str, dict]:
    """Load MCP servers from Claude config."""
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config.get('mcpServers', {})
    except Exception as e:
        print(f"⚠️  Failed to read config: {e}", file=sys.stderr)
        return {}

def check_serena_conflict(mcp_servers: Dict[str, dict]) -> Optional[str]:
    """
    Check if both 'serena' and 'serena-ace' exist.

    Returns warning message if conflict detected.
    """
    has_serena = 'serena' in mcp_servers
    has_serena_ace = 'serena-ace' in mcp_servers

    if has_serena and has_serena_ace:
        return """
⚠️  **MCP CONFLICT DETECTED** ⚠️

Both 'serena' and 'serena-ace' MCP servers are installed.
This causes tool_use concurrency issues (API Error 400).

**Resolution**:
1. Remove global Serena MCP:
   ```
   claude mcp remove serena --scope global
   ```

2. Or edit ~/.claude.json and remove the "serena" entry

3. Keep only 'serena-ace' (from ACE plugin)

**Why this happens**:
- Both servers use the same underlying mcp-serena
- Claude Code loads duplicate tools → concurrency conflict
- Namespacing doesn't prevent tool ID collisions

**Need help?** See: docs/TROUBLESHOOTING.md
"""

    if has_serena and not has_serena_ace:
        return """
ℹ️  **Serena MCP Detected**

You have 'serena' installed globally. ACE plugin will use 'serena-ace'.

If you experience 400 errors, remove global Serena:
```
claude mcp remove serena --scope global
```
"""

    return None

def check_chromadb_conflict(mcp_servers: Dict[str, dict]) -> Optional[str]:
    """Check ChromaDB conflicts."""
    has_chromadb = 'chromadb' in mcp_servers
    has_chromadb_ace = 'chromadb-ace' in mcp_servers

    if has_chromadb and has_chromadb_ace:
        return """
ℹ️  Both 'chromadb' and 'chromadb-ace' detected.

This usually works fine, but if you see issues:
```
claude mcp remove chromadb --scope global
```
"""

    return None

def main():
    """Run conflict checks and output warnings to context."""
    try:
        # Read SessionStart hook input (optional)
        session_id = 'unknown'
        if not sys.stdin.isatty():
            try:
                hook_input = json.load(sys.stdin)
                session_id = hook_input.get('session_id', 'unknown')
            except json.JSONDecodeError:
                # Stdin empty or invalid - that's ok
                pass

        print(f"🔍 ACE: Checking MCP conflicts (session: {session_id})", file=sys.stderr)

        # Find config
        config_path = find_claude_config()
        if not config_path:
            print("⚠️  Claude config not found, skipping conflict check", file=sys.stderr)
            return

        print(f"📄 Reading config: {config_path}", file=sys.stderr)

        # Load MCP servers
        mcp_servers = load_mcp_servers(config_path)

        if not mcp_servers:
            print("ℹ️  No MCP servers configured", file=sys.stderr)
            return

        print(f"✅ Found {len(mcp_servers)} MCP server(s)", file=sys.stderr)

        # Check for conflicts
        warnings: List[str] = []

        serena_warning = check_serena_conflict(mcp_servers)
        if serena_warning:
            warnings.append(serena_warning)

        chromadb_warning = check_chromadb_conflict(mcp_servers)
        if chromadb_warning:
            warnings.append(chromadb_warning)

        # Output warnings to context (SessionStart stdout → context)
        if warnings:
            print("\n" + "\n---\n".join(warnings), flush=True)
            print("\n🔧 ACE plugin MCP conflict detection complete.\n", file=sys.stderr)
        else:
            print("✅ No MCP conflicts detected", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Conflict check failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == '__main__':
    main()
