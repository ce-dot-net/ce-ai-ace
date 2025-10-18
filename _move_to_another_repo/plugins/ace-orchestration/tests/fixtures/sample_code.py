#!/usr/bin/env python3
"""Sample Python code for testing ACE pattern discovery.

This code demonstrates common Python patterns that ACE should discover:
- subprocess module usage
- pathlib operations
- SQLite database operations
- JSON handling
"""

import subprocess
from pathlib import Path
import sqlite3
import json


def run_git_command():
    """Run git command using subprocess."""
    result = subprocess.run(
        ['git', 'status'],
        capture_output=True,
        timeout=10,
        text=True,
        cwd=str(Path.cwd())
    )
    return result.stdout


def get_database_path():
    """Get database path using pathlib."""
    return Path.cwd() / '.ace-memory' / 'patterns.db'


def query_patterns():
    """Query patterns from SQLite database."""
    db_path = get_database_path()

    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM patterns ORDER BY confidence DESC')
    patterns = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return patterns


def save_config(config_data: dict):
    """Save configuration to JSON file."""
    config_path = Path.cwd() / 'config.json'

    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)


def load_config() -> dict:
    """Load configuration from JSON file."""
    config_path = Path.cwd() / 'config.json'

    if not config_path.exists():
        return {}

    with open(config_path, 'r') as f:
        return json.load(f)
