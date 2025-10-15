#!/usr/bin/env python3
"""
PreToolUse Hook - Validate patterns before code is written

Prevents anti-patterns proactively by checking before Edit/Write operations.
"""

import json
import sys
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

def validate_patterns():
    """Validate code against known anti-patterns."""
    try:
        # Read tool input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get('tool_input', {})
        content = tool_input.get('content', '')

        if not content or not DB_PATH.exists():
            # No content or no patterns yet
            print(json.dumps({'continue': True}))
            return

        # Check for anti-patterns
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, description
            FROM patterns
            WHERE type = 'harmful' AND confidence > 0.7
        ''')

        anti_patterns = cursor.fetchall()
        conn.close()

        warnings = []
        for name, desc in anti_patterns:
            # Simple check (in production, use regex/AST)
            if any(keyword in content.lower() for keyword in name.lower().split()):
                warnings.append(f"⚠️  Possible anti-pattern: {name}")

        if warnings:
            for warning in warnings:
                print(warning, file=sys.stderr)

        # Always continue (don't block)
        print(json.dumps({'continue': True}))

    except Exception as e:
        print(f"⚠️  Pattern validation failed: {e}", file=sys.stderr)
        print(json.dumps({'continue': True}))

if __name__ == '__main__':
    validate_patterns()
