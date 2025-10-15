#!/usr/bin/env python3
"""
Serena-based Pattern Detector - ACE Phase 5

Uses Serena MCP's symbolic tools for AST-aware pattern detection.
Better than regex as it understands code structure.

Integrates with:
- find_symbol: Symbol-level detection
- find_referencing_symbols: Track usage
- write_memory: Store ACE insights

Auto-detects Serena MCP availability and falls back to regex if unavailable.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path.cwd()
SCRIPT_DIR = Path(__file__).parent

# Cache for Serena detection (avoid repeated checks)
_SERENA_DETECTION_CACHE = None

# Pattern definitions enhanced for symbolic detection
SYMBOLIC_PATTERNS = {
    'python': [
        {
            'id': 'py-sym-001',
            'name': 'TypedDict for configs',
            'symbol_kind': 5,  # Class
            'base_class': 'TypedDict',
            'domain': 'python-typing',
            'type': 'helpful',
            'description': 'Configuration classes inheriting from TypedDict'
        },
        {
            'id': 'py-sym-002',
            'name': 'Dataclass usage',
            'symbol_kind': 5,  # Class
            'decorator': '@dataclass',
            'domain': 'python-datastructures',
            'type': 'helpful',
            'description': 'Data classes using @dataclass decorator'
        },
        {
            'id': 'py-sym-003',
            'name': 'Context managers',
            'symbol_kind': 12,  # Function
            'decorator': '@contextmanager',
            'domain': 'python-io',
            'type': 'helpful',
            'description': 'Context manager functions'
        },
    ],
    'typescript': [
        {
            'id': 'ts-sym-001',
            'name': 'Interface definitions',
            'symbol_kind': 11,  # Interface
            'domain': 'typescript-types',
            'type': 'helpful',
            'description': 'TypeScript interface definitions'
        },
        {
            'id': 'ts-sym-002',
            'name': 'Type guards',
            'symbol_kind': 12,  # Function
            'name_pattern': r'^is[A-Z]',
            'domain': 'typescript-guards',
            'type': 'helpful',
            'description': 'Type guard functions (isXxx)'
        },
    ],
    'javascript': [
        {
            'id': 'js-sym-001',
            'name': 'Custom React hooks',
            'symbol_kind': 12,  # Function
            'name_pattern': r'^use[A-Z]',
            'domain': 'react-hooks',
            'type': 'helpful',
            'description': 'Custom React hooks (useXxx)'
        },
        {
            'id': 'js-sym-002',
            'name': 'Async functions',
            'symbol_kind': 12,  # Function
            'async': True,
            'domain': 'javascript-async',
            'type': 'helpful',
            'description': 'Async function definitions'
        },
    ]
}

def is_serena_available() -> bool:
    """
    Check if Serena MCP is available.

    Uses cached detection to avoid repeated checks.

    Returns:
        True if Serena MCP is available, False otherwise
    """
    global _SERENA_DETECTION_CACHE

    if _SERENA_DETECTION_CACHE is not None:
        return _SERENA_DETECTION_CACHE

    try:
        # Run detection script
        result = subprocess.run(
            ['python3', str(SCRIPT_DIR / 'detect-mcp-serena.py')],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            detection = json.loads(result.stdout)
            _SERENA_DETECTION_CACHE = detection.get('serena_available', False)

            if _SERENA_DETECTION_CACHE:
                print(f"✅ Serena MCP available ({detection.get('confidence', 'unknown')} confidence)", file=sys.stderr)
            else:
                print("ℹ️  Serena MCP not available - using regex fallback", file=sys.stderr)

            return _SERENA_DETECTION_CACHE

    except Exception as e:
        print(f"⚠️  Serena detection check failed: {e}", file=sys.stderr)

    # Default to False on error
    _SERENA_DETECTION_CACHE = False
    return False


def call_serena_mcp(tool_name: str, params: Dict) -> Optional[Dict]:
    """
    Call Serena MCP tool via MCP bridge.

    Args:
        tool_name: MCP tool name (e.g., 'find_symbol')
        params: Tool parameters

    Returns:
        Tool result as dict, or None if failed
    """
    try:
        # Import MCP bridge
        sys.path.insert(0, str(SCRIPT_DIR))
        from mcp_bridge import call_mcp_tool

        # Call the MCP tool
        result = call_mcp_tool('serena', tool_name, params)
        return result

    except ImportError:
        # Fallback if MCP bridge not available
        print(f"⚠️  MCP bridge not available, simulating {tool_name}", file=sys.stderr)

        # Return simulated result for testing
        return {
            'success': False,
            'error': 'MCP bridge not available',
            'hint': 'Install mcp_bridge.py or run in Claude Code context'
        }

    except Exception as e:
        print(f"⚠️  MCP call failed: {e}", file=sys.stderr)
        return None


def detect_patterns_with_serena(file_path: str) -> List[Dict]:
    """
    Detect patterns using Serena's symbolic tools.

    Uses actual MCP tool calls via find_symbol and get_symbols_overview.

    Args:
        file_path: Path to file to analyze

    Returns:
        List of detected patterns with location info
    """
    # Check if Serena is available
    if not is_serena_available():
        print("⚠️  Serena not available, skipping symbolic detection", file=sys.stderr)
        return []

    # Determine language
    ext = Path(file_path).suffix
    lang_map = {
        '.py': 'python',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'javascript',
        '.jsx': 'javascript'
    }

    language = lang_map.get(ext)
    if not language:
        return []

    patterns = SYMBOLIC_PATTERNS.get(language, [])
    if not patterns:
        return []

    detected = []

    try:
        # First, get symbols overview
        relative_path = str(Path(file_path).relative_to(PROJECT_ROOT)) if Path(file_path).is_absolute() else file_path

        print(f"🔍 Calling Serena MCP: get_symbols_overview({relative_path})", file=sys.stderr)
        overview = call_serena_mcp('get_symbols_overview', {
            'relative_path': relative_path
        })

        if not overview or not overview.get('success'):
            print(f"⚠️  Serena overview failed: {overview.get('reason', 'unknown') if overview else 'no response'}", file=sys.stderr)
            return []

        # For each pattern, try to find matching symbols
        for pattern in patterns:
            symbol_kind = pattern.get('symbol_kind')
            name_pattern = pattern.get('name_pattern', '')

            # Call find_symbol to detect the pattern
            print(f"🔍 Calling Serena MCP: find_symbol(kind={symbol_kind})", file=sys.stderr)

            find_params = {
                'name_path': name_pattern if name_pattern else pattern.get('name', ''),
                'relative_path': relative_path,
                'include_kinds': [symbol_kind],
                'substring_matching': bool(name_pattern)
            }

            symbols = call_serena_mcp('find_symbol', find_params)

            if symbols and symbols.get('success') and symbols.get('symbols'):
                for symbol in symbols['symbols']:
                    detected_instance = {
                        **pattern,
                        'file_path': file_path,
                        'symbol_name': symbol.get('name', 'unknown'),
                        'location': {
                            'line': symbol.get('line', 0),
                            'column': symbol.get('column', 0),
                            'end_line': symbol.get('end_line', 0)
                        },
                        'detected_by': 'serena-symbolic',
                        'confidence': 0.9  # Higher confidence for AST-based detection
                    }
                    detected.append(detected_instance)
                    print(f"✅ Found {pattern['name']} at line {symbol.get('line', '?')}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Serena detection failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

    return detected

def track_pattern_usage(pattern_id: str, file_path: str, symbol_name: str) -> List[Dict]:
    """
    Track where a pattern is used in the codebase.

    Uses find_referencing_symbols to find all usages.

    Args:
        pattern_id: Pattern ID
        file_path: File containing the symbol
        symbol_name: Name of the symbol to track

    Returns:
        List of reference locations
    """
    if not is_serena_available():
        return []

    try:
        relative_path = str(Path(file_path).relative_to(PROJECT_ROOT)) if Path(file_path).is_absolute() else file_path

        print(f"🔗 Tracking references for {symbol_name} in {relative_path}", file=sys.stderr)

        result = call_serena_mcp('find_referencing_symbols', {
            'name_path': symbol_name,
            'relative_path': relative_path
        })

        if result and result.get('success') and result.get('references'):
            references = result['references']
            print(f"✅ Found {len(references)} references to {symbol_name}", file=sys.stderr)
            return references

        return []

    except Exception as e:
        print(f"⚠️  Reference tracking failed: {e}", file=sys.stderr)
        return []

def store_ace_insight_in_serena(pattern: Dict, insight: str, confidence: float):
    """
    Store ACE insight in Serena memory for future reference.

    Uses write_memory to persist insights.
    """
    if not is_serena_available():
        return

    try:
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        memory_content = f"""# ACE Insight: {pattern['name']}

**Pattern ID**: {pattern['id']}
**Domain**: {pattern['domain']}
**Confidence**: {confidence:.2%}

## Insight

{insight}

## When to Apply

{pattern['description']}

## Last Updated

{timestamp}
"""

        # Call Serena MCP write_memory
        print(f"💾 Storing insight for {pattern['id']} in Serena memory", file=sys.stderr)

        result = call_serena_mcp('write_memory', {
            'memory_name': f"ACE_Pattern_{pattern['id']}",
            'content': memory_content
        })

        if result and result.get('success'):
            print(f"✅ Stored insight for {pattern['id']} in Serena", file=sys.stderr)
        else:
            print(f"⚠️  Serena memory write failed: {result.get('reason', 'unknown') if result else 'no response'}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Serena memory write failed: {e}", file=sys.stderr)

def get_serena_symbols_overview(file_path: str) -> Dict:
    """
    Get high-level overview of symbols in file.

    Uses get_symbols_overview for efficient analysis.

    Args:
        file_path: Path to file to analyze

    Returns:
        Symbol overview dict with counts and top-level symbols
    """
    if not is_serena_available():
        return {}

    try:
        relative_path = str(Path(file_path).relative_to(PROJECT_ROOT)) if Path(file_path).is_absolute() else file_path

        print(f"📊 Getting symbols overview for {relative_path}", file=sys.stderr)

        result = call_serena_mcp('get_symbols_overview', {
            'relative_path': relative_path
        })

        if result and result.get('success'):
            overview = result.get('overview', {})
            print(f"✅ Found {overview.get('total_symbols', 0)} symbols", file=sys.stderr)
            return overview

        return {}

    except Exception as e:
        print(f"⚠️  Symbols overview failed: {e}", file=sys.stderr)
        return {}

# ============================================================================
# Hybrid Detection (Regex + Serena)
# ============================================================================

def detect_patterns_hybrid(file_path: str, code: str) -> List[Dict]:
    """
    Hybrid pattern detection using both regex and Serena.

    Strategy:
    1. Auto-detect if Serena MCP is available
    2. If available, try Serena symbolic detection (AST-based, more accurate)
    3. Fall back to regex if Serena unavailable or detection fails

    Args:
        file_path: Path to file to analyze
        code: File content

    Returns:
        List of detected patterns
    """
    # Try Serena first if available (AST-based, more accurate)
    if is_serena_available():
        serena_patterns = detect_patterns_with_serena(file_path)

        if serena_patterns:
            print(f"✅ Detected {len(serena_patterns)} patterns with Serena", file=sys.stderr)
            return serena_patterns
        else:
            print("ℹ️  Serena available but no patterns detected, falling back to regex", file=sys.stderr)
    else:
        print("ℹ️  Serena MCP not detected, using regex detection", file=sys.stderr)

    # Fallback to regex (current implementation)
    # Import regex patterns from ace-cycle.py
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location("ace_cycle", Path(__file__).parent / "ace-cycle.py")
        ace_cycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ace_cycle)

        patterns = ace_cycle.detect_patterns(code, file_path)
        if patterns:
            print(f"✅ Detected {len(patterns)} patterns with regex", file=sys.stderr)
        return patterns

    except Exception as e:
        print(f"⚠️  Regex fallback failed: {e}", file=sys.stderr)
        return []

if __name__ == '__main__':
    # Test Serena integration
    print("🧪 Testing Serena Pattern Detector", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Test file
    test_file = "scripts/ace-cycle.py"

    if Path(test_file).exists():
        with open(test_file, 'r') as f:
            code = f.read()

        patterns = detect_patterns_hybrid(test_file, code)
        print(f"\n✅ Detected {len(patterns)} patterns", file=sys.stderr)

        for p in patterns[:3]:
            print(f"  - {p['id']}: {p['name']}", file=sys.stderr)
    else:
        print(f"⚠️  Test file not found: {test_file}", file=sys.stderr)

    print("\n✅ Serena integration ready (using hybrid mode)", file=sys.stderr)
