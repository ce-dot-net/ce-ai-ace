#!/usr/bin/env python3
"""List ACE patterns with filtering - called by /ace-patterns command"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

def list_patterns(domain_filter=None, min_confidence=None):
    if not DB_PATH.exists():
        print("📊 No patterns learned yet.")
        print("\nPatterns will be detected automatically as you code!")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    query = 'SELECT * FROM patterns WHERE 1=1'
    params = []

    if domain_filter:
        query += ' AND (domain LIKE ? OR language LIKE ?)'
        params.extend([f'%{domain_filter}%', f'%{domain_filter}%'])

    if min_confidence:
        try:
            min_conf = float(min_confidence)
            query += ' AND confidence >= ?'
            params.append(min_conf)
        except ValueError:
            pass

    query += ' ORDER BY confidence DESC, observations DESC'

    cursor.execute(query, params)
    patterns = cursor.fetchall()

    if not patterns:
        print(f"No patterns found matching filters.")
        return

    print(f"🎯 ACE Learned Patterns ({len(patterns)} total)\n")

    # Group by confidence
    high = [p for p in patterns if p['confidence'] >= 0.7]
    medium = [p for p in patterns if 0.3 <= p['confidence'] < 0.7]
    low = [p for p in patterns if p['confidence'] < 0.3]

    # High confidence
    if high:
        print("## 🟢 High Confidence (≥70%)\n")
        for p in high:
            print(f"### {p['name']}")
            print(f"**ID**: {p['id']}")
            print(f"**Domain**: {p['domain']}")
            print(f"**Language**: {p['language']}")
            print(f"**Confidence**: {p['confidence']*100:.1f}% ({p['successes']}/{p['observations']} successes)")
            print(f"**Observations**: {p['observations']}")
            print(f"\n**Description**: {p['description']}\n")

            # Get latest insights
            cursor.execute('SELECT * FROM insights WHERE pattern_id = ? ORDER BY timestamp DESC LIMIT 3', (p['id'],))
            insights = cursor.fetchall()

            if insights:
                print("💡 **Latest Insights**:")
                for ins in insights:
                    ts = datetime.fromisoformat(ins['timestamp']).strftime('%Y-%m-%d')
                    print(f"- [{ts}] {ins['insight']}")

                print(f"\n📋 **Recommendation**: {insights[0]['recommendation']}\n")

            print("---\n")

    # Medium confidence
    if medium:
        print("## 🟡 Medium Confidence (30-70%)\n")
        for p in medium:
            print(f"### {p['name']}")
            print(f"**Confidence**: {p['confidence']*100:.1f}% ({p['successes']}/{p['observations']} successes)")
            print(f"**Domain**: {p['domain']} | **Language**: {p['language']}")
            print(f"\n{p['description']}\n")

            cursor.execute('SELECT * FROM insights WHERE pattern_id = ? ORDER BY timestamp DESC LIMIT 1', (p['id'],))
            insight = cursor.fetchone()
            if insight:
                print(f"💡 **Latest**: {insight['insight']}\n")

            print("---\n")

    # Low confidence
    if low:
        print("## 🔴 Low Confidence (<30%)\n")
        print("*These patterns may be pruned if they don't improve.*\n")
        for p in low:
            print(f"- **{p['name']}** ({p['confidence']*100:.0f}%, {p['observations']} obs)")
        print("\n---\n")

    print("\n💡 Commands: /ace-status | /ace-clear | /ace-force-reflect")

    conn.close()

if __name__ == '__main__':
    domain = sys.argv[1] if len(sys.argv) > 1 else None
    min_conf = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        list_patterns(domain, min_conf)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
