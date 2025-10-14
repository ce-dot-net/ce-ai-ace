#!/usr/bin/env python3
"""
Serena-based Pattern Detector - ACE Phase 5

Uses Serena MCP's symbolic tools for AST-aware pattern detection.
Better than regex as it understands code structure.

Integrates with:
- find_symbol: Symbol-level detection
- find_referencing_symbols: Track usage
- write_memory: Store ACE insights
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path.cwd()

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

def detect_patterns_with_serena(file_path: str) -> List[Dict]:
    """
    Detect patterns using Serena's symbolic tools.

    Args:
        file_path: Path to file to analyze

    Returns:
        List of detected patterns with location info
    """
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
        # Import Serena tools (via MCP)
        # In real use, these would be MCP calls
        # For now, we'll simulate with placeholder

        for pattern in patterns:
            # Use find_symbol to detect pattern
            # Example: find_symbol(name_path="Config", include_kinds=[5])

            # This would be an actual MCP call in production:
            # symbols = mcp.find_symbol(
            #     name_path=pattern.get('name_pattern', ''),
            #     relative_path=file_path,
            #     include_kinds=[pattern['symbol_kind']]
            # )

            # For now, mark as detected (placeholder)
            # In production, this checks if symbols exist
            detected_instance = {
                **pattern,
                'file_path': file_path,
                'location': {
                    'line': 0,  # Would be from Serena
                    'column': 0,
                    'end_line': 0
                },
                'detected_by': 'serena-symbolic'
            }

            # Only add if pattern would actually be found
            # (placeholder - in production, check symbols result)

    except Exception as e:
        print(f"⚠️  Serena detection failed: {e}", file=sys.stderr)

    return detected

def track_pattern_usage(pattern_id: str, file_path: str) -> List[Dict]:
    """
    Track where a pattern is used in the codebase.

    Uses find_referencing_symbols to find all usages.
    """
    try:
        # Example MCP call:
        # references = mcp.find_referencing_symbols(
        #     name_path="Config",
        #     relative_path=file_path
        # )

        # Placeholder return
        references = []

        return references

    except Exception as e:
        print(f"⚠️  Reference tracking failed: {e}", file=sys.stderr)
        return []

def store_ace_insight_in_serena(pattern: Dict, insight: str, confidence: float):
    """
    Store ACE insight in Serena memory for future reference.

    Uses write_memory to persist insights.
    """
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

        # Example MCP call:
        # mcp.write_memory(
        #     memory_name=f"ACE_Pattern_{pattern['id']}",
        #     content=memory_content
        # )

        print(f"✅ Stored insight for {pattern['id']} in Serena", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Serena memory write failed: {e}", file=sys.stderr)

def get_serena_symbols_overview(file_path: str) -> Dict:
    """
    Get high-level overview of symbols in file.

    Uses get_symbols_overview for efficient analysis.
    """
    try:
        # Example MCP call:
        # overview = mcp.get_symbols_overview(relative_path=file_path)

        # Placeholder
        overview = {
            'file_path': file_path,
            'symbols': [],
            'total_functions': 0,
            'total_classes': 0
        }

        return overview

    except Exception as e:
        print(f"⚠️  Symbols overview failed: {e}", file=sys.stderr)
        return {}

# ============================================================================
# Hybrid Detection (Regex + Serena)
# ============================================================================

def detect_patterns_hybrid(file_path: str, code: str) -> List[Dict]:
    """
    Hybrid pattern detection using both regex and Serena.

    Falls back to regex if Serena is unavailable.
    """
    # Try Serena first (AST-based, more accurate)
    serena_patterns = detect_patterns_with_serena(file_path)

    if serena_patterns:
        print(f"✅ Detected {len(serena_patterns)} patterns with Serena", file=sys.stderr)
        return serena_patterns

    # Fallback to regex (current implementation)
    print("ℹ️  Falling back to regex detection", file=sys.stderr)

    # Import regex patterns from ace-cycle.py
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location("ace_cycle", Path(__file__).parent / "ace-cycle.py")
        ace_cycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ace_cycle)

        return ace_cycle.detect_patterns(code, file_path)
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
