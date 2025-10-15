#!/usr/bin/env python3
"""
Pattern Convergence Checker - ACE Research Feature

Checks if patterns have stabilized (converged) based on ACE paper insight:
"Patterns stabilize after sufficient observations"

A pattern has converged when confidence hasn't changed significantly
in the last N observations.
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

MIN_OBSERVATIONS_FOR_CONVERGENCE = 20
CONFIDENCE_VARIANCE_THRESHOLD = 0.05  # 5% variance = converged

def has_converged(pattern_id: str) -> Tuple[bool, float, str]:
    """
    Check if a pattern has converged.

    Args:
        pattern_id: Pattern to check

    Returns:
        (has_converged, confidence, reason)
    """
    if not DB_PATH.exists():
        return (False, 0.0, "No database")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get pattern
    cursor.execute('SELECT * FROM patterns WHERE id = ?', (pattern_id,))
    pattern = cursor.fetchone()

    if not pattern:
        conn.close()
        return (False, 0.0, "Pattern not found")

    observations = pattern['observations']
    confidence = pattern['confidence']

    # Need minimum observations
    if observations < MIN_OBSERVATIONS_FOR_CONVERGENCE:
        conn.close()
        return (False, confidence, f"Need {MIN_OBSERVATIONS_FOR_CONVERGENCE - observations} more observations")

    # Check confidence history from insights
    cursor.execute('''
        SELECT confidence
        FROM insights
        WHERE pattern_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (pattern_id,))

    recent_confidences = [row['confidence'] for row in cursor.fetchall()]
    conn.close()

    if len(recent_confidences) < 5:
        return (False, confidence, "Need more insight history")

    # Calculate variance
    mean_conf = sum(recent_confidences) / len(recent_confidences)
    variance = sum((c - mean_conf) ** 2 for c in recent_confidences) / len(recent_confidences)
    std_dev = variance ** 0.5

    converged = std_dev < CONFIDENCE_VARIANCE_THRESHOLD

    if converged:
        return (True, confidence, f"Converged (σ={std_dev:.3f})")
    else:
        return (False, confidence, f"Still learning (σ={std_dev:.3f})")

def check_all_patterns() -> Dict:
    """
    Check convergence for all patterns.

    Returns:
        Statistics about convergence
    """
    if not DB_PATH.exists():
        return {}

    conn = sqlite3.connect(str(DB_PATH))
    cursor = cursor = conn.cursor()

    cursor.execute('SELECT id FROM patterns')
    pattern_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    converged_patterns = []
    learning_patterns = []
    insufficient_data = []

    for pattern_id in pattern_ids:
        is_converged, conf, reason = has_converged(pattern_id)

        if "Need" in reason or "history" in reason:
            insufficient_data.append((pattern_id, conf, reason))
        elif is_converged:
            converged_patterns.append((pattern_id, conf, reason))
        else:
            learning_patterns.append((pattern_id, conf, reason))

    return {
        'converged': converged_patterns,
        'learning': learning_patterns,
        'insufficient': insufficient_data,
        'total': len(pattern_ids),
        'convergence_rate': len(converged_patterns) / max(len(pattern_ids), 1)
    }

def main():
    """CLI for convergence checking."""
    stats = check_all_patterns()

    print("\n📊 Pattern Convergence Analysis\n")
    print(f"Total Patterns: {stats['total']}")
    print(f"Convergence Rate: {stats['convergence_rate']:.0%}\n")

    print(f"✅ Converged Patterns: {len(stats['converged'])}")
    for pattern_id, conf, reason in stats['converged']:
        print(f"   [{pattern_id}] {conf:.0%} - {reason}")

    print(f"\n📚 Still Learning: {len(stats['learning'])}")
    for pattern_id, conf, reason in stats['learning'][:5]:  # Show top 5
        print(f"   [{pattern_id}] {conf:.0%} - {reason}")

    print(f"\n⏳ Insufficient Data: {len(stats['insufficient'])}")
    for pattern_id, conf, reason in stats['insufficient'][:5]:  # Show top 5
        print(f"   [{pattern_id}] {conf:.0%} - {reason}")

    print()

if __name__ == '__main__':
    main()
