#!/usr/bin/env python3
"""
Serena MCP Integration Demo

Demonstrates how ACE uses Serena MCP when available.

This script shows the complete integration:
1. Auto-detects Serena availability
2. Calls MCP tools via bridge
3. Falls back to regex gracefully
4. Stores insights in Serena memory

Usage:
    python3 demo-serena-integration.py <file.py>
"""

import sys
import json
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from serena-pattern-detector.py (handle hyphenated filename)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "serena_pattern_detector",
    Path(__file__).parent / "serena-pattern-detector.py"
)
serena = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serena)

# Import functions
is_serena_available = serena.is_serena_available
detect_patterns_hybrid = serena.detect_patterns_hybrid
get_serena_symbols_overview = serena.get_serena_symbols_overview
track_pattern_usage = serena.track_pattern_usage
store_ace_insight_in_serena = serena.store_ace_insight_in_serena


def demo_pattern_detection(file_path: str):
    """
    Demonstrate pattern detection with Serena integration.
    """
    print("=" * 60)
    print("ACE + Serena MCP Integration Demo")
    print("=" * 60)
    print()

    # Step 1: Check if Serena is available
    print("Step 1: Detecting Serena MCP availability...")
    serena_detected = is_serena_available()

    if serena_detected:
        print("✅ Serena MCP detected!")
        print("   ACE will use AST-based pattern detection (more accurate)")
    else:
        print("⚠️  Serena MCP not detected")
        print("   ACE will use regex-based pattern detection (still works!)")
    print()

    # Step 2: Get file overview (if Serena available)
    if serena_detected:
        print("Step 2: Getting symbols overview...")
        overview = get_serena_symbols_overview(file_path)

        if overview:
            print(f"✅ Found {overview.get('total_symbols', 0)} symbols")
            print(f"   Classes: {overview.get('total_classes', 0)}")
            print(f"   Functions: {overview.get('total_functions', 0)}")
        else:
            print("⚠️  Overview not available (MCP bridge not connected)")
        print()

    # Step 3: Detect patterns
    print("Step 3: Detecting code patterns...")

    try:
        with open(file_path, 'r') as f:
            code = f.read()
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    patterns = detect_patterns_hybrid(file_path, code)

    if patterns:
        print(f"✅ Detected {len(patterns)} patterns:")
        for i, pattern in enumerate(patterns, 1):
            detection_method = pattern.get('detected_by', 'regex')
            print(f"   {i}. {pattern['name']} ({detection_method})")

            if 'location' in pattern and pattern['location']['line'] > 0:
                print(f"      Location: line {pattern['location']['line']}")
    else:
        print("⚠️  No patterns detected")
    print()

    # Step 4: Track usage (if Serena available)
    if serena_detected and patterns:
        print("Step 4: Tracking pattern usage...")

        for pattern in patterns[:1]:  # Just first one for demo
            if 'symbol_name' in pattern:
                references = track_pattern_usage(
                    pattern['id'],
                    file_path,
                    pattern['symbol_name']
                )

                if references:
                    print(f"✅ Found {len(references)} references to {pattern['symbol_name']}")
                else:
                    print(f"⚠️  Reference tracking not available (MCP bridge not connected)")
                break
        print()

    # Step 5: Store insights (if Serena available)
    if serena_detected and patterns:
        print("Step 5: Storing insights in Serena memory...")

        for pattern in patterns[:1]:  # Just first one for demo
            store_ace_insight_in_serena(
                pattern,
                f"Pattern '{pattern['name']}' detected in {file_path}. Applied correctly.",
                confidence=0.85
            )
            break
        print()

    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  • Serena MCP: {'Available' if serena_detected else 'Not Available'}")
    print(f"  • Detection method: {'AST-based' if serena_detected else 'Regex-based'}")
    print(f"  • Patterns found: {len(patterns)}")
    print(f"  • Integration status: {'Full' if serena_detected else 'Fallback (still works!)'}")
    print("=" * 60)
    print()

    if not serena_detected:
        print("💡 Tip: To enable Serena MCP:")
        print("   1. Add Serena to ~/.claude-code/config.json")
        print("   2. Restart Claude Code")
        print("   3. ACE will automatically detect and use it!")
        print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 demo-serena-integration.py <file.py>")
        print()
        print("Example:")
        print("  python3 scripts/demo-serena-integration.py scripts/ace-cycle.py")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    demo_pattern_detection(file_path)
