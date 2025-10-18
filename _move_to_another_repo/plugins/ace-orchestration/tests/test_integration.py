"""Integration tests for full ACE workflow"""

import pytest
import subprocess
from pathlib import Path
from ace_test_helper import ACETestHelper


@pytest.fixture
def ace_helper(plugin_root, temp_project, claude_env):
    """Create ACE test helper instance."""
    return ACETestHelper(plugin_root, temp_project, claude_env)


@pytest.mark.integration
def test_full_ace_workflow_edit_to_playbooks(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test complete ACE workflow: Edit → ace-cycle → patterns → playbooks."""
    # Step 1: Mock agent response
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'app.py')

    # Step 2: Simulate Edit tool (triggers PostToolUse → ace-cycle)
    test_file = ace_helper.project_root / 'app.py'
    test_file.write_text(sample_code)

    result = ace_helper.simulate_edit_tool(
        file_path='app.py',
        old_string='def foo(): pass',
        new_string='def foo():\n    return "bar"'
    )

    # Step 3: Verify ace-cycle executed
    assert result.exit_code == 0

    # Step 4: Verify pattern stored in SQLite
    patterns = ace_helper.get_db_patterns()
    assert len(patterns) > 0
    assert ace_helper.assert_pattern_stored('test-pattern-001')

    # Step 5: Generate playbooks
    subprocess.run(
        ['python3', str(ace_helper.plugin_root / 'scripts' / 'generate-playbook.py')],
        cwd=str(ace_helper.project_root),
        check=True
    )

    # Step 6: Verify CLAUDE.md created
    claude_md = ace_helper.project_root / 'CLAUDE.md'
    assert claude_md.exists()

    content = claude_md.read_text()
    assert 'ACE Plugin Instructions' in content
    assert 'Total patterns' in content

    # Step 7: Generate spec-kit playbooks
    specs_dir = ace_helper.project_root / 'specs'
    specs_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ['python3', str(ace_helper.plugin_root / 'scripts' / 'generate-speckit-playbook.py')],
        cwd=str(ace_helper.project_root),
        check=True
    )

    # Step 8: Verify spec-kit playbooks created
    playbooks_dir = ace_helper.project_root / 'specs' / 'playbooks'
    assert playbooks_dir.exists()


@pytest.mark.integration
def test_multiple_edits_pattern_merging(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that multiple edits with similar patterns trigger merging."""
    # First edit
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'file1.py')

    file1 = ace_helper.project_root / 'file1.py'
    file1.write_text(sample_code)

    result1 = ace_helper.simulate_edit_tool('file1.py', '', '')
    assert result1.exit_code == 0

    # Second edit with same pattern
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'file2.py')

    file2 = ace_helper.project_root / 'file2.py'
    file2.write_text(sample_code)

    result2 = ace_helper.simulate_edit_tool('file2.py', '', '')
    assert result2.exit_code == 0

    # Verify patterns were merged (should have 1 pattern with 2 observations)
    patterns = ace_helper.get_db_patterns()
    pattern = next(p for p in patterns if p['id'] == 'test-pattern-001')

    # Pattern should have been seen twice
    assert pattern['observations'] >= 2


@pytest.mark.integration
def test_write_tool_triggers_full_workflow(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that Write tool also triggers full ACE workflow."""
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'new_file.py')

    result = ace_helper.simulate_write_tool('new_file.py', sample_code)

    assert result.exit_code == 0

    # Verify pattern discovered
    assert ace_helper.assert_pattern_stored('test-pattern-001')

    # Verify file was created
    assert (ace_helper.project_root / 'new_file.py').exists()


@pytest.mark.integration
def test_end_to_end_with_real_playbook_generation(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test end-to-end workflow including playbook generation."""
    # Trigger pattern discovery
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'app.py')

    test_file = ace_helper.project_root / 'app.py'
    test_file.write_text(sample_code)

    result = ace_helper.simulate_edit_tool('app.py', '', '')
    assert result.exit_code == 0

    # Generate both playbook formats
    subprocess.run(
        ['python3', str(ace_helper.plugin_root / 'scripts' / 'generate-playbook.py'), '--format', 'both'],
        cwd=str(ace_helper.project_root),
        check=True
    )

    # Verify CLAUDE.md
    claude_md = ace_helper.project_root / 'CLAUDE.md'
    assert claude_md.exists()

    content = claude_md.read_text()
    assert '<!-- ACE-PLUGIN-START -->' in content
    assert '<!-- ACE-PLUGIN-END -->' in content

    # Verify size is reasonable (not bloated)
    lines = content.split('\n')
    assert len(lines) < 150


@pytest.mark.integration
def test_graceful_degradation_on_agent_failure(ace_helper, temp_db, sample_code):
    """Test ACE graceful degradation when agent fails (no cached response)."""
    # Don't mock agent response - simulate agent failure

    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    result = ace_helper.simulate_edit_tool('test.py', '', '')

    # Should still exit successfully (graceful degradation)
    assert result.exit_code == 0

    # No patterns should be discovered (no agent response)
    patterns = ace_helper.get_db_patterns()
    assert len(patterns) == 0


@pytest.mark.integration
def test_database_schema_integrity(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that database schema remains intact after workflow."""
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    result = ace_helper.simulate_edit_tool('test.py', '', '')
    assert result.exit_code == 0

    # Verify database schema
    import sqlite3

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Check patterns table
    cursor.execute("PRAGMA table_info(patterns)")
    pattern_columns = {row[1] for row in cursor.fetchall()}

    required_columns = {
        'id', 'bullet_id', 'name', 'domain', 'type', 'description', 'language',
        'observations', 'successes', 'failures', 'neutrals',
        'helpful_count', 'harmful_count', 'confidence',
        'last_seen', 'created_at'
    }

    assert required_columns.issubset(pattern_columns)

    # Check insights table
    cursor.execute("PRAGMA table_info(insights)")
    insight_columns = {row[1] for row in cursor.fetchall()}

    assert 'pattern_id' in insight_columns
    assert 'insight' in insight_columns
    assert 'recommendation' in insight_columns

    # Check observations table
    cursor.execute("PRAGMA table_info(observations)")
    obs_columns = {row[1] for row in cursor.fetchall()}

    assert 'pattern_id' in obs_columns
    assert 'outcome' in obs_columns
    assert 'test_status' in obs_columns

    conn.close()
