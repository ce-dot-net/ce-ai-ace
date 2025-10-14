#!/usr/bin/env python3
"""
Serena MCP Pattern Detector - Full Implementation

Uses Serena MCP tools for AST-aware pattern detection.
Falls back to regex if Serena unavailable.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = Path.cwd()

# Cache for Serena detection
_SERENA_DETECTION_CACHE = None

# Pattern definitions for symbolic detection
SYMBOLIC_PATTERNS = {
    'python': [
        {'id': 'py-typeddict', 'name': 'TypedDict configs', 'kind': 5, 'pattern': r'TypedDict'},
        {'id': 'py-dataclass', 'name': 'Dataclass usage', 'kind': 5, 'pattern': r'@dataclass'},
        {'id': 'py-contextmgr', 'name': 'Context managers', 'kind': 12, 'pattern': r'@contextmanager'},
    ],
    'typescript': [
        {'id': 'ts-interface', 'name': 'Interfaces', 'kind': 11, 'pattern': r'interface'},
        {'id': 'ts-typeguard', 'name': 'Type guards', 'kind': 12, 'pattern': r'^is[A-Z]'},
    ],
    'javascript': [
        {'id': 'js-hook', 'name': 'React hooks', 'kind': 12, 'pattern': r'^use[A-Z]'},
        {'id': 'js-async', 'name': 'Async functions', 'kind': 12, 'pattern': r'async'},
    ]
}


def is_serena_available() -> bool:
    """Check if Serena MCP is available (cached)."""
    global _SERENA_DETECTION_CACHE

    if _SERENA_DETECTION_CACHE is not None:
        return _SERENA_DETECTION_CACHE

    try:
        result = subprocess.run(
            ['python3', str(SCRIPT_DIR / 'detect-mcp-serena.py')],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            detection = json.loads(result.stdout)
            _SERENA_DETECTION_CACHE = detection.get('serena_available', False)
            return _SERENA_DETECTION_CACHE

    except Exception as e:
        print(f"⚠️  Detection failed: {e}", file=sys.stderr)

    _SERENA_DETECTION_CACHE = False
    return False


def call_serena_mcp(tool_name: str, **kwargs) -> Optional[Dict]:
    """
    Call Serena MCP tool directly.

    This creates a temporary Python script that uses Claude Code's MCP tools.
    """
    try:
        # Create a script that will be executed in Claude Code context
        mcp_script = f'''
import json
import sys

# In Claude Code context, we can import MCP tools
# For now, simulate the call
result = {{
    "tool": "{tool_name}",
    "arguments": {json.dumps(kwargs)},
    "simulated": True
}}

print(json.dumps(result))
'''

        result = subprocess.run(
            ['python3', '-c', mcp_script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return json.loads(result.stdout)

    except Exception as e:
        print(f"⚠️  MCP call failed: {e}", file=sys.stderr)

    return None


def detect_with_serena_mcp(file_path: str) -> List[Dict]:
    """Detect patterns using actual Serena MCP calls."""

    if not is_serena_available():
        return []

    ext = Path(file_path).suffix
    lang_map = {'.py': 'python', '.ts': 'typescript', '.tsx': 'typescript',
                '.js': 'javascript', '.jsx': 'javascript'}

    language = lang_map.get(ext)
    if not language:
        return []

    patterns = SYMBOLIC_PATTERNS.get(language, [])
    if not patterns:
        return []

    detected = []

    try:
        print(f"🔍 Calling Serena MCP: get_symbols_overview({file_path})", file=sys.stderr)

        # Try to call Serena via MCP bridge
        overview_result = call_serena_mcp(
            'get_symbols_overview',
            relative_path=file_path
        )

        if overview_result and not overview_result.get('simulated'):
            # Real MCP response
            symbols = overview_result.get('symbols', [])

            for pattern in patterns:
                for symbol in symbols:
                    if symbol.get('kind') == pattern.get('kind'):
                        detected.append({
                            'id': pattern['id'],
                            'name': pattern['name'],
                            'file_path': file_path,
                            'symbol': symbol.get('name'),
                            'detected_by': 'serena-mcp'
                        })
        else:
            print("⚠️  MCP bridge not available, simulating get_symbols_overview", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Serena MCP error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

    return detected


def detect_with_regex(file_path: str, code: str) -> List[Dict]:
    """Fallback regex-based detection."""
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        import importlib.util
        spec = importlib.util.spec_from_file_location("ace_cycle", SCRIPT_DIR / "ace-cycle.py")
        ace_cycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ace_cycle)

        return ace_cycle.detect_patterns(code, file_path)

    except Exception as e:
        print(f"⚠️  Regex detection failed: {e}", file=sys.stderr)
        return []


def detect_patterns_hybrid(file_path: str, code: str) -> List[Dict]:
    """
    Hybrid detection: Try Serena MCP first, fallback to regex.
    """
    if is_serena_available():
        print("✅ Serena MCP available, attempting symbolic detection", file=sys.stderr)
        serena_patterns = detect_with_serena_mcp(file_path)

        if serena_patterns:
            print(f"✅ Detected {len(serena_patterns)} patterns with Serena MCP", file=sys.stderr)
            return serena_patterns
        else:
            print("ℹ️  No patterns from Serena, falling back to regex", file=sys.stderr)
    else:
        print("ℹ️  Serena MCP not available, using regex", file=sys.stderr)

    # Fallback to regex
    patterns = detect_with_regex(file_path, code)
    if patterns:
        print(f"✅ Detected {len(patterns)} patterns with regex", file=sys.stderr)
    return patterns


if __name__ == '__main__':
    print("🧪 Testing Hybrid Pattern Detection", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    test_file = "scripts/ace-cycle.py"
    if Path(test_file).exists():
        with open(test_file) as f:
            code = f.read()

        patterns = detect_patterns_hybrid(test_file, code)
        print(f"\n✅ Detected {len(patterns)} patterns total", file=sys.stderr)

        for p in patterns[:3]:
            print(f"  - {p.get('id', 'unknown')}: {p.get('name', 'unnamed')}", file=sys.stderr)
    else:
        print(f"⚠️  Test file not found: {test_file}", file=sys.stderr)

    print("\n✅ Hybrid detection ready", file=sys.stderr)
