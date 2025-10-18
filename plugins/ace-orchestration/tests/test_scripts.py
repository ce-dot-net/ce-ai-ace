"""Tests for ACE scripts (ace-cycle, generate-playbook, etc.)"""

import pytest
import subprocess
import sqlite3
from pathlib import Path
from ace_test_helper import ACETestHelper


@pytest.fixture
def ace_helper(plugin_root, temp_project, claude_env):
    """Create ACE test helper instance."""
    return ACETestHelper(plugin_root, temp_project, claude_env)


@pytest.mark.unit
def test_generate_playbook_with_no_patterns(plugin_root, temp_project):
    """Test playbook generation with empty database."""
    # Initialize empty database
    db_path = temp_project / '.ace-memory' / 'patterns.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Run generate-playbook script
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    # Should succeed
    assert result.returncode == 0

    # Should create CLAUDE.md
    claude_md = temp_project / 'CLAUDE.md'
    assert claude_md.exists()

    # Should contain instructions-only message
    content = claude_md.read_text()
    assert 'ACE Plugin Instructions' in content
    assert 'No patterns learned yet' in content or 'Total patterns' in content


@pytest.mark.unit
def test_generate_playbook_with_patterns(plugin_root, temp_project, temp_db):
    """Test playbook generation with existing patterns."""
    # Add test pattern to database
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO patterns (
            id, bullet_id, name, domain, type, description, language,
            observations, successes, failures, neutrals,
            helpful_count, harmful_count, confidence,
            last_seen, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'test-pattern-001',
        '[test-00001]',
        'Test Pattern',
        'test-domain',
        'helpful',
        'A test pattern for validation',
        'python',
        10, 8, 2, 0,
        0, 0, 0.8,
        '2025-10-18T12:00:00',
        '2025-10-18T10:00:00'
    ))

    conn.commit()
    conn.close()

    # Run generate-playbook script
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    # Should succeed
    assert result.returncode == 0

    # Should create CLAUDE.md
    claude_md = temp_project / 'CLAUDE.md'
    assert claude_md.exists()

    # Should contain pattern statistics
    content = claude_md.read_text()
    assert 'Total patterns' in content
    assert '1' in content  # 1 pattern


@pytest.mark.unit
def test_generate_speckit_playbooks(plugin_root, temp_project, temp_db):
    """Test spec-kit playbook generation."""
    # Add test pattern
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO patterns (
            id, bullet_id, name, domain, type, description, language,
            observations, successes, confidence, last_seen, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'test-pattern-spec',
        '[spec-00001]',
        'Spec Kit Pattern',
        'test-spec',
        'helpful',
        'Test spec-kit generation',
        'python',
        5, 5, 1.0,
        '2025-10-18T12:00:00',
        '2025-10-18T10:00:00'
    ))

    conn.commit()
    conn.close()

    # Create specs directory
    specs_dir = temp_project / 'specs'
    specs_dir.mkdir(parents=True, exist_ok=True)

    # Run spec-kit generation
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-speckit-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    # Should succeed
    assert result.returncode == 0

    # Should create playbook directory
    playbooks_dir = temp_project / 'specs' / 'playbooks'
    assert playbooks_dir.exists()


@pytest.mark.unit
def test_ace_cycle_database_initialization(ace_helper, sample_code, mock_agent_response):
    """Test that ace-cycle initializes database correctly."""
    # Mock agent response
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    # Run ace-cycle
    result = ace_helper.simulate_edit_tool('test.py', '', '')

    # Should create database
    db_path = ace_helper.project_root / '.ace-memory' / 'patterns.db'
    assert db_path.exists()

    # Should have correct schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(patterns)")
    columns = {row[1] for row in cursor.fetchall()}

    assert 'id' in columns
    assert 'bullet_id' in columns
    assert 'name' in columns
    assert 'confidence' in columns
    assert 'helpful_count' in columns
    assert 'harmful_count' in columns

    conn.close()


@pytest.mark.unit
def test_ace_cycle_pattern_storage(ace_helper, sample_code, mock_agent_response, temp_db):
    """Test that ace-cycle stores discovered patterns correctly."""
    # Mock agent response with specific pattern
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    # Run ace-cycle
    result = ace_helper.simulate_edit_tool('test.py', '', '')

    # Should store pattern from mock response
    assert ace_helper.assert_pattern_stored('test-pattern-001')

    # Verify pattern data
    patterns = ace_helper.get_db_patterns()
    pattern = next(p for p in patterns if p['id'] == 'test-pattern-001')

    assert pattern['name'] == 'Test Pattern'
    # Confidence will be recalculated by ace-cycle based on successes/observations
    assert pattern['confidence'] >= 0.0 and pattern['confidence'] <= 1.0
    assert pattern['observations'] == 1
