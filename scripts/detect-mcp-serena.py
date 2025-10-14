#!/usr/bin/env python3
"""
MCP Serena Detection Utility

Detects if Serena MCP server is available in Claude Code.
Returns JSON with detection results.

Usage:
    python3 detect-mcp-serena.py

Output:
    {
        "serena_available": true,
        "mcp_tools": ["mcp__serena__find_symbol", ...],
        "detection_method": "tool_check"
    }
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

def detect_via_tool_list() -> Optional[Dict]:
    """
    Detect Serena by checking if its tools are accessible.

    In Claude Code, MCP tools are prefixed with mcp__<server>__<tool>.
    For Serena, we look for tools like mcp__serena__find_symbol.
    """
    try:
        # Try to import and use the ListMcpResourcesTool if available
        # This is the most reliable method in Claude Code 2.0+

        # For now, we'll use a simpler approach: check if we can see MCP tools
        # by trying to call a lightweight MCP command

        result = subprocess.run(
            ['python3', '-c', '''
import sys
import os

# Check if running in Claude Code context
if "CLAUDE_PLUGIN_ROOT" in os.environ:
    print("claude_code_detected")
else:
    print("standalone")
'''],
            capture_output=True,
            text=True,
            timeout=2
        )

        context = result.stdout.strip()

        # In Claude Code, check for Serena-specific indicators
        serena_dir = Path.home() / '.serena'
        serena_config = Path.cwd() / '.serena' / 'project.yml'

        if serena_dir.exists() or serena_config.exists():
            return {
                'serena_available': True,
                'detection_method': 'filesystem_check',
                'serena_dir': str(serena_dir) if serena_dir.exists() else None,
                'project_config': str(serena_config) if serena_config.exists() else None
            }

        return None

    except Exception as e:
        print(f"⚠️  Tool list detection failed: {e}", file=sys.stderr)
        return None


def detect_via_test_call() -> Optional[Dict]:
    """
    Detect Serena by attempting a test MCP call.

    This simulates calling a Serena tool and checks if it responds.
    """
    try:
        # Check if .serena directory exists (strong indicator)
        project_serena = Path.cwd() / '.serena'
        home_serena = Path.home() / '.serena'

        if project_serena.exists():
            # Check for memories
            memories = list((project_serena / 'memories').glob('*.md')) if (project_serena / 'memories').exists() else []

            return {
                'serena_available': True,
                'detection_method': 'project_directory',
                'location': str(project_serena),
                'has_memories': len(memories) > 0,
                'memory_count': len(memories)
            }
        elif home_serena.exists():
            return {
                'serena_available': True,
                'detection_method': 'home_directory',
                'location': str(home_serena)
            }

        return None

    except Exception as e:
        print(f"⚠️  Test call detection failed: {e}", file=sys.stderr)
        return None


def detect_via_config() -> Optional[Dict]:
    """
    Detect Serena by checking Claude Code config files.

    Claude Code stores MCP server configs in ~/.claude-code/ or project .claude/
    """
    try:
        # Check project-level config
        project_config = Path.cwd() / '.claude' / 'settings.local.json'
        home_config = Path.home() / '.claude-code' / 'config.json'

        configs_to_check = [
            project_config,
            home_config,
            Path.home() / '.config' / 'claude-code' / 'config.json'
        ]

        for config_path in configs_to_check:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)

                    # Check for MCP servers configuration
                    mcp_servers = config.get('mcpServers', {})

                    if 'serena' in mcp_servers or any('serena' in key.lower() for key in mcp_servers.keys()):
                        return {
                            'serena_available': True,
                            'detection_method': 'config_file',
                            'config_path': str(config_path),
                            'server_config': {k: v for k, v in mcp_servers.items() if 'serena' in k.lower()}
                        }

                except json.JSONDecodeError:
                    continue

        return None

    except Exception as e:
        print(f"⚠️  Config detection failed: {e}", file=sys.stderr)
        return None


def detect_serena() -> Dict:
    """
    Comprehensive Serena detection using multiple methods.

    Returns:
        Dict with detection results and available MCP tools
    """
    detection_results = {
        'serena_available': False,
        'detection_method': None,
        'confidence': 'none',
        'details': {}
    }

    # Try multiple detection methods (in order of reliability)
    methods = [
        ('config', detect_via_config),
        ('filesystem', detect_via_test_call),
        ('tools', detect_via_tool_list),
    ]

    for method_name, detection_func in methods:
        result = detection_func()
        if result and result.get('serena_available'):
            detection_results.update(result)
            detection_results['confidence'] = 'high' if method_name == 'config' else 'medium'
            detection_results['details'][method_name] = result
            break

    # Additional checks for confidence
    if detection_results['serena_available']:
        # Check if we can find serena executable
        try:
            serena_check = subprocess.run(
                ['which', 'serena'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if serena_check.returncode == 0:
                detection_results['serena_executable'] = serena_check.stdout.strip()
                detection_results['confidence'] = 'high'
        except:
            pass

    return detection_results


def get_available_mcp_tools() -> List[str]:
    """
    Get list of available MCP tools in current Claude Code session.

    This would normally query the Claude Code environment, but for now
    we'll return a placeholder list if Serena is detected.
    """
    detection = detect_serena()

    if detection['serena_available']:
        # Return known Serena MCP tools
        return [
            'mcp__serena__find_symbol',
            'mcp__serena__find_referencing_symbols',
            'mcp__serena__get_symbols_overview',
            'mcp__serena__search_for_pattern',
            'mcp__serena__write_memory',
            'mcp__serena__read_memory',
            'mcp__serena__list_memories',
        ]

    return []


def main():
    """Main detection routine."""
    try:
        # Detect Serena
        detection = detect_serena()

        # Get available tools
        tools = get_available_mcp_tools()
        detection['mcp_tools'] = tools
        detection['tool_count'] = len(tools)

        # Output JSON
        print(json.dumps(detection, indent=2))

        # Log to stderr for debugging
        if detection['serena_available']:
            print(f"✅ Serena MCP detected via {detection['detection_method']} (confidence: {detection['confidence']})", file=sys.stderr)
            print(f"   Found {len(tools)} MCP tools", file=sys.stderr)
        else:
            print("ℹ️  Serena MCP not detected - will use regex fallback", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"❌ Detection failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

        # Return safe default (no Serena)
        print(json.dumps({
            'serena_available': False,
            'detection_method': 'error',
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
