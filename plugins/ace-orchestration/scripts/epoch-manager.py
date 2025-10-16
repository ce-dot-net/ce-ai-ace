#!/usr/bin/env python3
"""
Multi-Epoch Training Manager - ACE Phase 4

Implements multi-epoch training as per ACE paper:
"Max offline epochs: 5"
"Multi-epoch adds +2.6% improvement"

Allows revisiting training data to refine patterns over multiple passes.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

MAX_EPOCHS = 5  # From ACE paper

def init_epochs_table():
    """Add epochs table to database."""
    # Ensure .ace-memory directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Epochs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS epochs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epoch_number INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            patterns_processed INTEGER DEFAULT 0,
            patterns_refined INTEGER DEFAULT 0,
            avg_confidence_before REAL,
            avg_confidence_after REAL,
            status TEXT DEFAULT 'running'
        )
    ''')

    # Pattern evolution tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pattern_evolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            epoch_number INTEGER NOT NULL,
            confidence_before REAL,
            confidence_after REAL,
            observations_added INTEGER DEFAULT 0,
            refinement_applied INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (pattern_id) REFERENCES patterns(id)
        )
    ''')

    # Training data cache (for offline training)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            code_content TEXT NOT NULL,
            patterns_detected TEXT,
            test_status TEXT,
            cached_at TEXT NOT NULL,
            used_in_epochs TEXT DEFAULT '[]'
        )
    ''')

    conn.commit()
    conn.close()

def get_current_epoch() -> Optional[int]:
    """Get current epoch number (or None if no epochs started)."""
    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        SELECT epoch_number FROM epochs
        WHERE status = 'running'
        ORDER BY epoch_number DESC
        LIMIT 1
    ''')

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def start_epoch() -> int:
    """
    Start a new training epoch.

    Returns:
        Epoch number
    """
    init_epochs_table()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Complete any running epochs
    cursor.execute('''
        UPDATE epochs
        SET status = 'completed', completed_at = ?
        WHERE status = 'running'
    ''', (datetime.now().isoformat(),))

    # Get next epoch number
    cursor.execute('SELECT MAX(epoch_number) FROM epochs')
    max_epoch = cursor.fetchone()[0]
    next_epoch = (max_epoch or 0) + 1

    # Check limit
    if next_epoch > MAX_EPOCHS:
        print(f"⚠️  Max epochs ({MAX_EPOCHS}) reached", file=sys.stderr)
        conn.close()
        return max_epoch

    # Start new epoch
    cursor.execute('''
        INSERT INTO epochs (epoch_number, started_at, status)
        VALUES (?, ?, 'running')
    ''', (next_epoch, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    print(f"🚀 Started epoch {next_epoch}/{MAX_EPOCHS}", file=sys.stderr)
    return next_epoch

def complete_epoch(epoch_number: int, stats: Dict):
    """
    Mark epoch as complete with statistics.

    Args:
        epoch_number: Epoch to complete
        stats: {'patterns_processed': int, 'patterns_refined': int, ...}
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE epochs SET
            completed_at = ?,
            patterns_processed = ?,
            patterns_refined = ?,
            avg_confidence_before = ?,
            avg_confidence_after = ?,
            status = 'completed'
        WHERE epoch_number = ?
    ''', (
        datetime.now().isoformat(),
        stats.get('patterns_processed', 0),
        stats.get('patterns_refined', 0),
        stats.get('avg_confidence_before', 0.0),
        stats.get('avg_confidence_after', 0.0),
        epoch_number
    ))

    conn.commit()
    conn.close()

    print(f"✅ Completed epoch {epoch_number}", file=sys.stderr)

def track_pattern_evolution(
    pattern_id: str,
    epoch_number: int,
    confidence_before: float,
    confidence_after: float,
    observations_added: int = 0,
    refinement_applied: bool = False
):
    """Track how a pattern evolved during an epoch."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO pattern_evolution (
            pattern_id, epoch_number, confidence_before, confidence_after,
            observations_added, refinement_applied, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        pattern_id, epoch_number, confidence_before, confidence_after,
        observations_added, 1 if refinement_applied else 0,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

def cache_training_data(file_path: str, code: str, patterns_detected: List[str], test_status: str):
    """Cache training data for offline epochs."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    import json
    patterns_json = json.dumps(patterns_detected)

    cursor.execute('''
        INSERT INTO training_cache (
            file_path, code_content, patterns_detected, test_status, cached_at
        ) VALUES (?, ?, ?, ?, ?)
    ''', (file_path, code, patterns_json, test_status, datetime.now().isoformat()))

    conn.commit()
    conn.close()

def get_training_data_for_epoch(epoch_number: int) -> List[Dict]:
    """
    Get training data for an epoch.

    For epoch 1: Real-time data
    For epochs 2-5: Cached data from previous epochs
    """
    if epoch_number == 1:
        # First epoch uses real-time data
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get cached data not used in this epoch yet
    import json
    cursor.execute('''
        SELECT * FROM training_cache
        WHERE NOT (used_in_epochs LIKE '%' || ? || '%')
        ORDER BY cached_at DESC
        LIMIT 100
    ''', (str(epoch_number),))

    rows = cursor.fetchall()
    data = []

    for row in rows:
        data.append({
            'id': row['id'],
            'file_path': row['file_path'],
            'code_content': row['code_content'],
            'patterns_detected': json.loads(row['patterns_detected']),
            'test_status': row['test_status']
        })

        # Mark as used in this epoch
        used_epochs = json.loads(row['used_in_epochs'] or '[]')
        used_epochs.append(epoch_number)
        cursor.execute('''
            UPDATE training_cache
            SET used_in_epochs = ?
            WHERE id = ?
        ''', (json.dumps(used_epochs), row['id']))

    conn.commit()
    conn.close()

    return data

def get_epoch_stats() -> List[Dict]:
    """Get statistics for all epochs."""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM epochs
        ORDER BY epoch_number
    ''')

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_pattern_evolution_history(pattern_id: str) -> List[Dict]:
    """Get evolution history for a specific pattern."""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM pattern_evolution
        WHERE pattern_id = ?
        ORDER BY epoch_number
    ''', (pattern_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# ============================================================================
# CLI Commands
# ============================================================================

def cmd_start_epoch():
    """CLI: Start new epoch."""
    epoch = start_epoch()
    print(f"Started epoch {epoch}")

def cmd_complete_epoch():
    """CLI: Complete current epoch."""
    epoch = get_current_epoch()
    if not epoch:
        print("No running epoch")
        return

    # Get stats
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM patterns')
    patterns_processed = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(confidence) FROM patterns')
    avg_confidence = cursor.fetchone()[0] or 0.0

    conn.close()

    complete_epoch(epoch, {
        'patterns_processed': patterns_processed,
        'patterns_refined': 0,
        'avg_confidence_before': avg_confidence,
        'avg_confidence_after': avg_confidence
    })

def cmd_epoch_stats():
    """CLI: Show epoch statistics."""
    stats = get_epoch_stats()

    if not stats:
        print("No epochs yet")
        return

    print("\n📊 Epoch Statistics\n")
    print(f"{'Epoch':<8} {'Status':<12} {'Patterns':<10} {'Avg Conf':<12} {'Duration':<15}")
    print("=" * 70)

    for epoch in stats:
        started = datetime.fromisoformat(epoch['started_at'])
        completed = epoch['completed_at']

        if completed:
            completed_dt = datetime.fromisoformat(completed)
            duration = str(completed_dt - started).split('.')[0]
        else:
            duration = "Running..."

        avg_conf = epoch['avg_confidence_after'] or epoch['avg_confidence_before'] or 0.0

        print(f"{epoch['epoch_number']:<8} {epoch['status']:<12} {epoch['patterns_processed']:<10} {avg_conf:<12.2f} {duration:<15}")

if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'stats'

    # Always initialize tables first
    init_epochs_table()

    if command == 'start':
        cmd_start_epoch()
    elif command == 'complete':
        cmd_complete_epoch()
    elif command == 'stats':
        cmd_epoch_stats()
    else:
        print(f"Unknown command: {command}")
        print("Usage: epoch-manager.py [start|complete|stats]")
        sys.exit(1)
