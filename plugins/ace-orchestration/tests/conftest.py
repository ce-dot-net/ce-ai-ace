"""pytest configuration and fixtures for ACE plugin tests."""

import os
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def plugin_root():
    """Return the plugin root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent.parent


@pytest.fixture
def claude_env(plugin_root, tmp_path):
    """Provide Claude Code environment variables."""
    return {
        'CLAUDE_PLUGIN_ROOT': str(plugin_root),
        'CLAUDE_PROJECT_DIR': str(tmp_path),
        'CLAUDECODE': '1',
        'CLAUDE_CODE_ENTRYPOINT': 'cli'
    }


@pytest.fixture
def temp_project(tmp_path):
    """Create an isolated temporary project directory."""
    # Create ACE memory directory
    ace_memory = tmp_path / '.ace-memory'
    ace_memory.mkdir(parents=True, exist_ok=True)

    # Create specs directory structure
    specs = tmp_path / 'specs'
    playbooks = specs / 'playbooks'
    memory = specs / 'memory'
    playbooks.mkdir(parents=True, exist_ok=True)
    memory.mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def temp_db(temp_project):
    """Create and initialize a temporary ACE database."""
    db_path = temp_project / '.ace-memory' / 'patterns.db'

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create patterns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id TEXT PRIMARY KEY,
            bullet_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            language TEXT NOT NULL,
            observations INTEGER DEFAULT 0,
            successes INTEGER DEFAULT 0,
            failures INTEGER DEFAULT 0,
            neutrals INTEGER DEFAULT 0,
            helpful_count INTEGER DEFAULT 0,
            harmful_count INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0.0,
            last_seen TEXT,
            created_at TEXT
        )
    ''')

    # Create insights table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            insight TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            confidence REAL NOT NULL,
            applied_correctly INTEGER NOT NULL,
            FOREIGN KEY (pattern_id) REFERENCES patterns(id)
        )
    ''')

    # Create observations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            outcome TEXT NOT NULL,
            test_status TEXT,
            error_logs TEXT,
            file_path TEXT,
            FOREIGN KEY (pattern_id) REFERENCES patterns(id)
        )
    ''')

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_hook_input():
    """Provide sample Claude Code hook input JSON."""
    return {
        'session_id': 'test-session-123',
        'transcript_path': '/tmp/transcript.jsonl',
        'cwd': '/tmp/test-project',
        'hook_event_name': 'PostToolUse',
        'tool_name': 'Edit',
        'tool_input': {
            'file_path': 'test.py',
            'old_string': 'def foo(): pass',
            'new_string': 'def foo():\n    return "bar"'
        },
        'tool_response': {
            'filePath': 'test.py',
            'success': True
        }
    }


@pytest.fixture
def sample_code():
    """Provide sample Python code for pattern discovery."""
    return '''#!/usr/bin/env python3
"""Sample Python code for testing pattern discovery."""

import subprocess
from pathlib import Path
import sqlite3
import json

def run_command():
    """Run a subprocess command."""
    result = subprocess.run(
        ['git', 'status'],
        capture_output=True,
        timeout=10,
        text=True
    )
    return result.stdout

def store_data():
    """Store data in SQLite database."""
    db_path = Path.cwd() / '.ace-memory' / 'patterns.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patterns')
    return cursor.fetchall()
'''


@pytest.fixture
def expected_patterns():
    """Provide expected pattern definitions for validation."""
    return [
        {
            'id': 'discovered-subprocess-usage',
            'name': 'subprocess module usage',
            'domain': 'python-stdlib',
            'type': 'helpful',
            'language': 'python',
            'description': 'Uses Python subprocess.run() to execute external commands'
        },
        {
            'id': 'discovered-pathlib-operations',
            'name': 'pathlib for file path operations',
            'domain': 'python-stdlib',
            'type': 'helpful',
            'language': 'python',
            'description': 'Uses pathlib.Path for cross-platform file path handling'
        },
        {
            'id': 'discovered-sqlite-row-factory',
            'name': 'SQLite with row_factory for dict access',
            'domain': 'python-database',
            'type': 'helpful',
            'language': 'python',
            'description': 'Uses sqlite3.Row factory for dictionary-like result access'
        }
    ]


@pytest.fixture
def mock_agent_response():
    """Provide mock agent response for pattern discovery."""
    return {
        'discovered_patterns': [
            {
                'id': 'test-pattern-001',
                'name': 'Test Pattern',
                'description': 'A test pattern for validation',
                'domain': 'test-domain',
                'type': 'helpful',
                'language': 'python',
                'applied_correctly': True,
                'contributed_to': 'success',
                'confidence': 0.8,
                'insight': 'This is a test pattern discovered from code analysis.',
                'recommendation': 'Use this pattern when testing ACE functionality.'
            }
        ],
        'meta_insights': ['Test pattern discovery completed successfully']
    }


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (slower, requires real components)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as fast unit tests (mocked dependencies)"
    )
