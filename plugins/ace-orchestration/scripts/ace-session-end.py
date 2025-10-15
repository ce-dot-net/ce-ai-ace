#!/usr/bin/env python3
"""
ACE Session End - Cleanup and finalization

Called by SessionEnd hook to:
1. Deduplicate similar patterns
2. Prune low-confidence patterns (if observations >= 10 and confidence < 30%)
3. Regenerate final playbook
"""

import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

SIMILARITY_THRESHOLD = 0.85
PRUNE_THRESHOLD = 0.30
MIN_OBSERVATIONS = 10

def calculate_similarity(p1: dict, p2: dict) -> float:
    """Simple Jaccard similarity on pattern names and descriptions."""
    name1 = set(p1['name'].lower().split())
    name2 = set(p2['name'].lower().split())
    desc1 = set(p1['description'].lower().split())
    desc2 = set(p2['description'].lower().split())

    name_sim = len(name1 & name2) / max(len(name1 | name2), 1)
    desc_sim = len(desc1 & desc2) / max(len(desc1 | desc2), 1)

    return (name_sim * 0.6) + (desc_sim * 0.4)

def deduplicate_patterns():
    """Find and merge similar patterns."""
    if not DB_PATH.exists():
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all patterns
    cursor.execute('SELECT * FROM patterns ORDER BY observations DESC')
    patterns = [dict(row) for row in cursor.fetchall()]

    if len(patterns) < 2:
        conn.close()
        return 0

    merged_count = 0
    processed = set()

    for i, p1 in enumerate(patterns):
        if p1['id'] in processed:
            continue

        for j, p2 in enumerate(patterns[i+1:], i+1):
            if p2['id'] in processed:
                continue

            # Only compare same domain and type
            if p1['domain'] != p2['domain'] or p1['type'] != p2['type']:
                continue

            similarity = calculate_similarity(p1, p2)

            if similarity >= SIMILARITY_THRESHOLD:
                # Merge p2 into p1
                print(f"🔀 Merging: {p2['name']} → {p1['name']} ({similarity:.0%} similar)", file=sys.stderr)

                # Merge observations
                cursor.execute('''
                    UPDATE patterns SET
                        observations = observations + ?,
                        successes = successes + ?,
                        failures = failures + ?,
                        neutrals = neutrals + ?
                    WHERE id = ?
                ''', (p2['observations'], p2['successes'], p2['failures'], p2['neutrals'], p1['id']))

                # Update confidence
                cursor.execute('''
                    UPDATE patterns SET
                        confidence = CAST(successes AS REAL) / CAST(observations AS REAL)
                    WHERE id = ?
                ''', (p1['id'],))

                # Move insights from p2 to p1
                cursor.execute('UPDATE insights SET pattern_id = ? WHERE pattern_id = ?', (p1['id'], p2['id']))

                # Move observations from p2 to p1
                cursor.execute('UPDATE observations SET pattern_id = ? WHERE pattern_id = ?', (p1['id'], p2['id']))

                # Delete p2
                cursor.execute('DELETE FROM patterns WHERE id = ?', (p2['id'],))

                processed.add(p2['id'])
                merged_count += 1
                break

    conn.commit()
    conn.close()
    return merged_count

def prune_low_confidence():
    """Remove patterns with low confidence after sufficient observations."""
    if not DB_PATH.exists():
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find patterns to prune
    cursor.execute('''
        SELECT id, name, confidence, observations
        FROM patterns
        WHERE observations >= ? AND confidence < ?
    ''', (MIN_OBSERVATIONS, PRUNE_THRESHOLD))

    to_prune = cursor.fetchall()

    if not to_prune:
        conn.close()
        return 0

    pruned_count = 0
    for p in to_prune:
        print(f"🗑️  Pruning: {p['name']} ({p['confidence']*100:.0f}% after {p['observations']} observations)", file=sys.stderr)

        # Delete pattern
        cursor.execute('DELETE FROM patterns WHERE id = ?', (p['id'],))

        # Delete related insights and observations
        cursor.execute('DELETE FROM insights WHERE pattern_id = ?', (p['id'],))
        cursor.execute('DELETE FROM observations WHERE pattern_id = ?', (p['id'],))

        pruned_count += 1

    conn.commit()
    conn.close()
    return pruned_count

def main():
    """Session end cleanup."""
    try:
        # Read hook input (optional, we don't need it)
        if not sys.stdin.isatty():
            _ = json.load(sys.stdin)

        print("🧹 ACE: Session cleanup...", file=sys.stderr)

        # Deduplicate
        merged = deduplicate_patterns()
        if merged > 0:
            print(f"✅ Deduplicated {merged} similar pattern(s)", file=sys.stderr)

        # Prune
        pruned = prune_low_confidence()
        if pruned > 0:
            print(f"✅ Pruned {pruned} low-confidence pattern(s)", file=sys.stderr)

        # Regenerate playbook
        import subprocess
        subprocess.run([
            'python3',
            str(Path(__file__).parent / 'generate-playbook.py')
        ], check=False)

        print("✅ ACE session cleanup complete", file=sys.stderr)

        # Output success
        print(json.dumps({'continue': True}))
        sys.exit(0)

    except Exception as e:
        print(f"❌ Session cleanup failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Continue anyway
        print(json.dumps({'continue': True}))
        sys.exit(0)

if __name__ == '__main__':
    main()
