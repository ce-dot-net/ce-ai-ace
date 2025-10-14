#!/usr/bin/env python3
"""Show ACE statistics - called by /ace-status command"""

import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

def show_stats():
    if not DB_PATH.exists():
        print("📊 ACE hasn't learned any patterns yet.")
        print("\nStart coding, and patterns will be detected automatically!")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Overall stats
    cursor.execute('SELECT COUNT(*) as total, SUM(observations) as obs, SUM(successes) as succ FROM patterns')
    overall = cursor.fetchone()

    cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence >= 0.7')
    high = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence >= 0.3 AND confidence < 0.7')
    medium = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence < 0.3')
    low = cursor.fetchone()[0]

    total_obs = overall['obs'] or 0
    total_succ = overall['succ'] or 0
    success_rate = (total_succ / total_obs * 100) if total_obs > 0 else 0

    print("🎯 ACE Pattern Learning Status\n")
    print("📊 Overall Statistics:")
    print(f"   • Total Patterns: {overall['total']}")
    print(f"   • High Confidence (≥70%): {high} patterns")
    print(f"   • Medium Confidence (30-70%): {medium} patterns")
    print(f"   • Low Confidence (<30%): {low} patterns")
    print(f"   • Total Observations: {total_obs}")
    print(f"   • Overall Success Rate: {success_rate:.1f}%\n")

    # By domain
    cursor.execute('SELECT domain, COUNT(*) as count, AVG(confidence) as avg_conf FROM patterns GROUP BY domain ORDER BY count DESC')
    domains = cursor.fetchall()

    if domains:
        print("📈 By Domain:")
        for d in domains:
            print(f"   • {d['domain']}: {d['count']} patterns (avg confidence: {d['avg_conf']*100:.1f}%)")
        print()

    # Top patterns
    cursor.execute('SELECT name, confidence, observations FROM patterns WHERE confidence >= 0.7 ORDER BY confidence DESC, observations DESC LIMIT 5')
    top = cursor.fetchall()

    if top:
        print("🔥 Top 5 Most Confident Patterns:")
        for i, p in enumerate(top, 1):
            print(f"   {i}. {p['name']} - {p['confidence']*100:.1f}% confidence ({p['observations']} observations)")
        print()

    # Low confidence (may be pruned)
    cursor.execute('SELECT name, confidence, observations FROM patterns WHERE observations >= 10 AND confidence < 0.3 ORDER BY confidence ASC LIMIT 5')
    prunable = cursor.fetchall()

    if prunable:
        print("📉 Low Confidence Patterns (may be pruned):")
        for p in prunable:
            print(f"   • {p['name']} - {p['confidence']*100:.1f}% confidence ({p['observations']} observations)")
        print()

    # Last updated
    cursor.execute('SELECT MAX(last_seen) FROM patterns')
    last_updated = cursor.fetchone()[0]
    if last_updated:
        print(f"⏰ Last Updated: {last_updated}\n")

    print("💡 Tip: Use /ace-patterns to see detailed pattern list")

    conn.close()

if __name__ == '__main__':
    try:
        show_stats()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
