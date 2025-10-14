#!/usr/bin/env python3
"""
MCP Bridge for Claude Code

Provides a Python interface to call MCP tools from within Claude Code hooks.

Usage:
    from mcp_bridge import call_mcp_tool

    result = call_mcp_tool('serena', 'find_symbol', {
        'name_path': 'MyClass',
        'relative_path': 'src/file.py'
    })
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def call_mcp_tool(server: str, tool: str, params: Dict[str, Any]) -> Optional[Dict]:
    """
    Call an MCP tool through Claude Code's MCP system.

    Args:
        server: MCP server name (e.g., 'serena', 'github', 'filesystem')
        tool: Tool name (e.g., 'find_symbol', 'get_file_contents')
        params: Tool parameters as dict

    Returns:
        Tool result as dict, or None if failed

    Examples:
        >>> call_mcp_tool('serena', 'find_symbol', {
        ...     'name_path': 'MyClass',
        ...     'relative_path': 'src/file.py',
        ...     'include_kinds': [5]
        ... })
        {
            'success': True,
            'symbols': [...]
        }
    """
    # Method 1: Try Claude Code MCP CLI (if available)
    claude_mcp_cli = _try_claude_code_mcp_cli(server, tool, params)
    if claude_mcp_cli:
        return claude_mcp_cli

    # Method 2: Try direct MCP protocol via stdio
    direct_mcp = _try_direct_mcp_call(server, tool, params)
    if direct_mcp:
        return direct_mcp

    # Method 3: Try filesystem-based communication
    filesystem_mcp = _try_filesystem_mcp(server, tool, params)
    if filesystem_mcp:
        return filesystem_mcp

    # All methods failed
    return {
        'success': False,
        'error': 'MCP bridge not available in this context',
        'hint': 'This function works when called from Claude Code hooks'
    }


def _try_claude_code_mcp_cli(server: str, tool: str, params: Dict) -> Optional[Dict]:
    """
    Try calling MCP via Claude Code's built-in CLI.

    Claude Code may provide a helper CLI tool for MCP calls.
    """
    try:
        # Check if Claude Code provides an MCP CLI
        mcp_cli_candidates = [
            'claude-code-mcp',
            'cc-mcp',
            'claude-mcp'
        ]

        for cli in mcp_cli_candidates:
            try:
                # Try to call the CLI
                result = subprocess.run(
                    [
                        cli,
                        'call',
                        f'{server}:{tool}',
                        json.dumps(params)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout:
                    return json.loads(result.stdout)

            except FileNotFoundError:
                continue

    except Exception:
        pass

    return None


def _try_direct_mcp_call(server: str, tool: str, params: Dict) -> Optional[Dict]:
    """
    Try calling MCP server directly via stdio.

    This works if we can invoke the MCP server process directly.
    """
    try:
        # Get MCP server command from config
        config_path = Path.home() / '.claude-code' / 'config.json'
        if not config_path.exists():
            config_path = Path.cwd() / '.claude' / 'settings.local.json'

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

            mcp_servers = config.get('mcpServers', {})
            server_config = mcp_servers.get(server)

            if server_config:
                command = server_config.get('command')
                args = server_config.get('args', [])

                if command:
                    # Call the MCP server directly
                    # This would use MCP protocol (JSON-RPC over stdio)
                    mcp_request = {
                        'jsonrpc': '2.0',
                        'id': 1,
                        'method': f'tools/{tool}',
                        'params': params
                    }

                    result = subprocess.run(
                        [command] + args,
                        input=json.dumps(mcp_request),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.returncode == 0 and result.stdout:
                        response = json.loads(result.stdout)
                        return response.get('result')

    except Exception:
        pass

    return None


def _try_filesystem_mcp(server: str, tool: str, params: Dict) -> Optional[Dict]:
    """
    Try MCP via filesystem-based communication.

    Creates a request file and waits for response file.
    Used when Claude Code monitors a directory for MCP requests.
    """
    try:
        # Check if Claude Code provides an MCP request directory
        mcp_request_dir = Path(os.environ.get('CLAUDE_MCP_DIR', '/tmp/claude-mcp'))

        if not mcp_request_dir.exists():
            return None

        # Create request file
        request_id = os.getpid()
        request_file = mcp_request_dir / f'request-{request_id}.json'
        response_file = mcp_request_dir / f'response-{request_id}.json'

        # Write request
        with open(request_file, 'w') as f:
            json.dump({
                'server': server,
                'tool': tool,
                'params': params
            }, f)

        # Wait for response (with timeout)
        import time
        timeout = 10
        start = time.time()

        while time.time() - start < timeout:
            if response_file.exists():
                with open(response_file) as f:
                    response = json.load(f)

                # Clean up
                request_file.unlink(missing_ok=True)
                response_file.unlink(missing_ok=True)

                return response

            time.sleep(0.1)

        # Cleanup on timeout
        request_file.unlink(missing_ok=True)

    except Exception:
        pass

    return None


def is_mcp_available(server: str) -> bool:
    """
    Check if an MCP server is available.

    Args:
        server: MCP server name (e.g., 'serena')

    Returns:
        True if server is available, False otherwise
    """
    # Try to call a lightweight method
    result = call_mcp_tool(server, 'ping', {})
    return result is not None and result.get('success', False)


# Convenience functions for common MCP servers

def serena_find_symbol(name_path: str, relative_path: str, **kwargs) -> Optional[Dict]:
    """Call serena's find_symbol tool."""
    params = {
        'name_path': name_path,
        'relative_path': relative_path,
        **kwargs
    }
    return call_mcp_tool('serena', 'find_symbol', params)


def serena_get_symbols_overview(relative_path: str, **kwargs) -> Optional[Dict]:
    """Call serena's get_symbols_overview tool."""
    params = {
        'relative_path': relative_path,
        **kwargs
    }
    return call_mcp_tool('serena', 'get_symbols_overview', params)


def serena_find_referencing_symbols(name_path: str, relative_path: str, **kwargs) -> Optional[Dict]:
    """Call serena's find_referencing_symbols tool."""
    params = {
        'name_path': name_path,
        'relative_path': relative_path,
        **kwargs
    }
    return call_mcp_tool('serena', 'find_referencing_symbols', params)


def serena_write_memory(memory_name: str, content: str, **kwargs) -> Optional[Dict]:
    """Call serena's write_memory tool."""
    params = {
        'memory_name': memory_name,
        'content': content,
        **kwargs
    }
    return call_mcp_tool('serena', 'write_memory', params)


def serena_read_memory(memory_file_name: str, **kwargs) -> Optional[Dict]:
    """Call serena's read_memory tool."""
    params = {
        'memory_file_name': memory_file_name,
        **kwargs
    }
    return call_mcp_tool('serena', 'read_memory', params)


if __name__ == '__main__':
    # Test MCP bridge
    print("🧪 Testing MCP Bridge", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Test Serena availability
    if is_mcp_available('serena'):
        print("✅ Serena MCP is available", file=sys.stderr)

        # Test symbols overview
        result = serena_get_symbols_overview('scripts/mcp-bridge.py')
        if result:
            print(f"✅ Got symbols overview: {result}", file=sys.stderr)
        else:
            print("⚠️  Symbols overview failed", file=sys.stderr)
    else:
        print("⚠️  Serena MCP not available", file=sys.stderr)
        print("   This is expected when not running in Claude Code context", file=sys.stderr)

    print("\n✅ MCP Bridge ready", file=sys.stderr)
