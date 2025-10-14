#!/usr/bin/env python3
"""
Pattern Export/Import - Cross-Project Learning

Enables sharing patterns across projects as suggested in ACE paper Section 5.
Patterns learned on one codebase can benefit another.
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

def export_patterns(output_path: str):
    """Export all patterns to JSON file."""
    if not DB_PATH.exists():
        print("❌ No patterns database found", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Export patterns
    cursor.execute('SELECT * FROM patterns')
    patterns = [dict(row) for row in cursor.fetchall()]

    # Export insights
    cursor.execute('SELECT * FROM insights')
    insights = [dict(row) for row in cursor.fetchall()]

    # Export observations
    cursor.execute('SELECT * FROM observations')
    observations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    export_data = {
        'version': '2.0.0',
        'exported_at': datetime.now().isoformat(),
        'project': str(PROJECT_ROOT.name),
        'patterns': patterns,
        'insights': insights,
        'observations': observations,
        'total_patterns': len(patterns),
        'total_observations': sum(p['observations'] for p in patterns)
    }

    Path(output_path).write_text(json.dumps(export_data, indent=2))
    print(f"✅ Exported {len(patterns)} patterns to {output_path}")

def import_patterns(input_path: str, merge_strategy: str = 'smart'):
    """
    Import patterns from JSON file.

    Args:
        input_path: Path to JSON file
        merge_strategy: 'smart' (use curator), 'overwrite', or 'skip-existing'
    """
    if not Path(input_path).exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    import_data = json.loads(Path(input_path).read_text())

    print(f"📥 Importing patterns from {import_data.get('project', 'unknown')}")
    print(f"   Exported: {import_data.get('exported_at', 'unknown')}")
    print(f"   Patterns: {import_data.get('total_patterns', 0)}")
    print()

    if not DB_PATH.exists():
        # Initialize database
        sys.path.insert(0, str(Path(__file__).parent))
        from ace_cycle import init_database
        init_database()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    patterns_imported = 0
    patterns_merged = 0
    patterns_skipped = 0

    for pattern in import_data.get('patterns', []):
        # Check if exists
        cursor.execute('SELECT * FROM patterns WHERE id = ?', (pattern['id'],))
        existing = cursor.fetchone()

        if existing and merge_strategy == 'skip-existing':
            patterns_skipped += 1
            continue

        if existing and merge_strategy == 'smart':
            # Merge using ACE curator logic
            cursor.execute('''
                UPDATE patterns SET
                    observations = observations + ?,
                    successes = successes + ?,
                    failures = failures + ?,
                    neutrals = neutrals + ?,
                    confidence = (successes + ?) / CAST(observations + ? AS REAL),
                    last_seen = ?
                WHERE id = ?
            ''', (
                pattern['observations'], pattern['successes'],
                pattern['failures'], pattern['neutrals'],
                pattern['successes'], pattern['observations'],
                pattern['last_seen'], pattern['id']
            ))
            patterns_merged += 1

        else:
            # Insert or overwrite
            cursor.execute('''
                INSERT OR REPLACE INTO patterns (
                    id, bullet_id, name, domain, type, description, language,
                    observations, successes, failures, neutrals,
                    helpful_count, harmful_count, confidence, last_seen, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern['id'], pattern['bullet_id'], pattern['name'],
                pattern['domain'], pattern['type'], pattern['description'],
                pattern['language'], pattern['observations'],
                pattern['successes'], pattern['failures'], pattern['neutrals'],
                pattern.get('helpful_count', 0), pattern.get('harmful_count', 0),
                pattern['confidence'], pattern['last_seen'],
                pattern.get('created_at', datetime.now().isoformat())
            ))
            patterns_imported += 1

    conn.commit()
    conn.close()

    print(f"✅ Import complete:")
    print(f"   Imported: {patterns_imported}")
    print(f"   Merged: {patterns_merged}")
    print(f"   Skipped: {patterns_skipped}")

    # Regenerate playbook
    import subprocess
    subprocess.run([
        'python3',
        str(Path(__file__).parent / 'generate-playbook.py')
    ], check=False)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='ACE Pattern Export/Import')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export patterns to JSON')
    export_parser.add_argument('--output', required=True, help='Output JSON file path')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import patterns from JSON')
    import_parser.add_argument('--input', required=True, help='Input JSON file path')
    import_parser.add_argument(
        '--strategy',
        choices=['smart', 'overwrite', 'skip-existing'],
        default='smart',
        help='Merge strategy (default: smart)'
    )

    args = parser.parse_args()

    if args.command == 'export':
        export_patterns(args.output)
    elif args.command == 'import':
        import_patterns(args.input, args.strategy)

if __name__ == '__main__':
    main()
