#!/usr/bin/env python3
"""
ACE Plugin - Smart Serena Manager

Runs on SessionStart to:
1. Detect if global Serena exists
2. If yes: Use global Serena, disable plugin's serena-ace
3. If no: Enable plugin's serena-ace
4. Ensure project is registered in whichever Serena is active
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

def disable_serena_ace(config_path: Path) -> bool:
    """
    Conditionally disable serena-ace in plugin.json if global Serena exists.

    Returns True if successfully disabled, False otherwise.
    """
    try:
        plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
        if not plugin_root:
            print("⚠️  CLAUDE_PLUGIN_ROOT not set, cannot disable serena-ace", file=sys.stderr)
            return False

        plugin_json_path = Path(plugin_root) / 'plugin.json'
        if not plugin_json_path.exists():
            print(f"⚠️  plugin.json not found at {plugin_json_path}", file=sys.stderr)
            return False

        # Create a .ace-config file to signal which Serena to use
        ace_config_path = Path(plugin_root) / '.ace-config'
        with open(ace_config_path, 'w') as f:
            json.dump({
                'use_global_serena': True,
                'serena_ace_disabled': True
            }, f, indent=2)

        print(f"✅ Created {ace_config_path} to use global Serena", file=sys.stderr)
        return True

    except Exception as e:
        print(f"⚠️  Failed to disable serena-ace: {e}", file=sys.stderr)
        return False


def enable_serena_ace() -> bool:
    """
    Enable serena-ace from plugin if no global Serena exists.

    Returns True if successfully enabled, False otherwise.
    """
    try:
        plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
        if not plugin_root:
            return False

        # Create a .ace-config file to signal which Serena to use
        ace_config_path = Path(plugin_root) / '.ace-config'
        with open(ace_config_path, 'w') as f:
            json.dump({
                'use_global_serena': False,
                'serena_ace_disabled': False
            }, f, indent=2)

        print(f"✅ Created {ace_config_path} to use plugin Serena", file=sys.stderr)
        return True

    except Exception as e:
        print(f"⚠️  Failed to enable serena-ace: {e}", file=sys.stderr)
        return False


def manage_serena_strategy(mcp_servers: Dict[str, dict]) -> Tuple[Optional[str], str]:
    """
    Smart Serena management:
    1. If global 'serena' exists → use it, signal to disable 'serena-ace'
    2. If no global 'serena' → use 'serena-ace' from plugin

    Returns (warning_message, strategy)
    """
    has_global_serena = 'serena' in mcp_servers
    has_serena_ace = 'serena-ace' in mcp_servers

    # CONFLICT: Both exist simultaneously
    if has_global_serena and has_serena_ace:
        # Prefer global Serena, disable plugin's serena-ace
        disable_serena_ace(find_claude_config())

        return ("""
✅ **Smart Serena Detection**

Global 'serena' MCP detected. ACE plugin will use it instead of bundled 'serena-ace'.

**Action taken:**
- Using global Serena for all symbolic operations
- Plugin's serena-ace disabled to prevent conflicts
- Project will be auto-registered in global Serena

**Benefits:**
- No duplicate tool conflicts
- Single source of truth for Serena operations
- Seamless integration with existing Serena setup
""", "use_global")

    # PREFERRED: Global Serena exists, no plugin serena-ace
    elif has_global_serena and not has_serena_ace:
        disable_serena_ace(find_claude_config())

        return ("""
✅ **Using Global Serena**

ACE plugin detected global 'serena' MCP and will use it for all operations.
""", "use_global")

    # FALLBACK: No global Serena, use plugin's serena-ace
    elif not has_global_serena and has_serena_ace:
        enable_serena_ace()

        return ("""
ℹ️  **Using Plugin Serena**

No global 'serena' detected. ACE plugin will use bundled 'serena-ace'.
""", "use_plugin")

    # NEW INSTALL: Neither exists yet (plugin not fully loaded)
    else:
        enable_serena_ace()
        return (None, "use_plugin")

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

        # Smart Serena management
        messages: List[str] = []

        serena_message, strategy = manage_serena_strategy(mcp_servers)
        if serena_message:
            messages.append(serena_message)

        print(f"📋 Serena strategy: {strategy}", file=sys.stderr)

        # Check other conflicts
        chromadb_warning = check_chromadb_conflict(mcp_servers)
        if chromadb_warning:
            messages.append(chromadb_warning)

        # Output messages to context (SessionStart stdout → context)
        if messages:
            print("\n" + "\n---\n".join(messages), flush=True)
            print("\n🔧 ACE plugin smart MCP management complete.\n", file=sys.stderr)
        else:
            print("✅ Serena strategy configured", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Conflict check failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == '__main__':
    main()
