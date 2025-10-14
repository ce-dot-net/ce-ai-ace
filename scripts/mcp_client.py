#!/usr/bin/env python3
"""
MCP Client for ACE - Direct communication with MCP servers

Implements JSON-RPC protocol to communicate with MCP servers like Serena.
Allows Python scripts to call MCP tools directly.
"""

import json
import subprocess
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

class MCPClient:
    """Client for calling MCP tools from Python scripts."""

    def __init__(self, server_name: str = "serena"):
        self.server_name = server_name
        self.server_config = self._load_server_config()

    def _load_server_config(self) -> Optional[Dict]:
        """Load MCP server configuration from Claude Code config."""
        config_paths = [
            Path.home() / '.claude-code' / 'config.json',
            Path.home() / '.config' / 'claude-code' / 'config.json',
            Path.cwd() / '.claude' / 'settings.local.json'
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)

                    mcp_servers = config.get('mcpServers', {})
                    if self.server_name in mcp_servers:
                        return mcp_servers[self.server_name]
                except:
                    continue

        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
        """
        Call an MCP tool directly.

        Args:
            tool_name: Name of the tool (e.g., "find_symbol")
            arguments: Tool arguments as dict

        Returns:
            Tool response or None if failed
        """
        if not self.server_config:
            return None

        # Construct MCP request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            # Start MCP server process
            command = self.server_config.get('command', 'npx')
            args = self.server_config.get('args', [])

            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send request
            stdout, stderr = process.communicate(
                input=json.dumps(request) + '\n',
                timeout=10
            )

            # Parse response
            for line in stdout.strip().split('\n'):
                if line.strip():
                    response = json.loads(line)
                    if 'result' in response:
                        return response['result']

            return None

        except Exception as e:
            print(f"⚠️  MCP call failed: {e}", file=sys.stderr)
            return None


class SerenaMCPClient(MCPClient):
    """Specialized client for Serena MCP server."""

    def __init__(self):
        super().__init__("serena")

    def find_symbol(
        self,
        name_path: str,
        relative_path: str = "",
        include_body: bool = False,
        depth: int = 0,
        include_kinds: Optional[List[int]] = None,
        substring_matching: bool = False
    ) -> List[Dict]:
        """
        Find symbols matching the given name path.

        Returns list of symbols with metadata and optionally body.
        """
        arguments = {
            "name_path": name_path,
            "include_body": include_body,
            "depth": depth,
            "substring_matching": substring_matching
        }

        if relative_path:
            arguments["relative_path"] = relative_path

        if include_kinds:
            arguments["include_kinds"] = include_kinds

        result = self.call_tool("find_symbol", arguments)
        return result if result else []

    def get_symbols_overview(self, relative_path: str) -> Dict:
        """Get high-level overview of symbols in a file."""
        result = self.call_tool("get_symbols_overview", {
            "relative_path": relative_path
        })
        return result if result else {}

    def search_for_pattern(
        self,
        substring_pattern: str,
        relative_path: str = "",
        restrict_search_to_code_files: bool = True,
        context_lines_before: int = 0,
        context_lines_after: int = 0
    ) -> Dict:
        """Search for regex pattern in codebase."""
        arguments = {
            "substring_pattern": substring_pattern,
            "restrict_search_to_code_files": restrict_search_to_code_files
        }

        if relative_path:
            arguments["relative_path"] = relative_path

        if context_lines_before:
            arguments["context_lines_before"] = context_lines_before

        if context_lines_after:
            arguments["context_lines_after"] = context_lines_after

        result = self.call_tool("search_for_pattern", arguments)
        return result if result else {}

    def find_referencing_symbols(
        self,
        name_path: str,
        relative_path: str
    ) -> List[Dict]:
        """Find all references to a symbol."""
        result = self.call_tool("find_referencing_symbols", {
            "name_path": name_path,
            "relative_path": relative_path
        })
        return result if result else []

    def write_memory(self, memory_name: str, content: str) -> bool:
        """Write to Serena memory."""
        result = self.call_tool("write_memory", {
            "memory_name": memory_name,
            "content": content
        })
        return result is not None

    def read_memory(self, memory_file_name: str) -> Optional[str]:
        """Read from Serena memory."""
        result = self.call_tool("read_memory", {
            "memory_file_name": memory_file_name
        })
        return result.get('content') if result else None

    def list_memories(self) -> List[str]:
        """List available Serena memories."""
        result = self.call_tool("list_memories", {})
        return result.get('memories', []) if result else []


# Convenience function
def get_serena_client() -> Optional[SerenaMCPClient]:
    """
    Get Serena MCP client if available.

    Returns None if Serena is not configured.
    """
    client = SerenaMCPClient()
    if client.server_config:
        return client
    return None


if __name__ == '__main__':
    # Test the client
    print("🧪 Testing Serena MCP Client", file=sys.stderr)

    client = get_serena_client()

    if client:
        print("✅ Serena client initialized", file=sys.stderr)

        # Test list_memories
        memories = client.list_memories()
        print(f"📝 Found {len(memories)} memories", file=sys.stderr)

        # Test get_symbols_overview on a test file
        test_file = "scripts/ace-cycle.py"
        if Path(test_file).exists():
            overview = client.get_symbols_overview(test_file)
            print(f"🔍 Symbols overview: {len(overview.get('symbols', []))} symbols", file=sys.stderr)
    else:
        print("⚠️  Serena client not available", file=sys.stderr)
        sys.exit(1)
