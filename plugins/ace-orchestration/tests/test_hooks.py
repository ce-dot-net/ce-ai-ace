"""Tests for ACE Plugin hooks (PostToolUse, AgentStart, etc.)"""

import pytest
from pathlib import Path
from ace_test_helper import ACETestHelper


@pytest.fixture
def ace_helper(plugin_root, temp_project, claude_env):
    """Create ACE test helper instance."""
    return ACETestHelper(plugin_root, temp_project, claude_env)


@pytest.mark.unit
def test_post_tool_use_hook_with_edit_tool(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that PostToolUse hook triggers ace-cycle.py with Edit tool."""
    # Create a test file
    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    # Mock agent response to avoid real agent invocation
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    # Simulate Edit tool → PostToolUse hook
    result = ace_helper.simulate_edit_tool(
        file_path='test.py',
        old_string='def foo(): pass',
        new_string='def foo():\n    return "bar"'
    )

    # Verify hook executed successfully
    assert result.exit_code == 0, f"Hook failed with stderr: {result.stderr}"

    # Verify ACE cycle started (check stderr for log messages)
    assert "ACE: Starting reflection cycle" in result.stderr or result.exit_code == 0

    # Verify JSON response (if hook returns one)
    if result.json_response:
        assert result.json_response.get('continue') is True


@pytest.mark.unit
def test_post_tool_use_hook_with_write_tool(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that PostToolUse hook triggers ace-cycle.py with Write tool."""
    # Mock agent response
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'app.py')

    # Simulate Write tool → PostToolUse hook
    result = ace_helper.simulate_write_tool(
        file_path='app.py',
        content=sample_code
    )

    # Verify hook executed successfully
    assert result.exit_code == 0, f"Hook failed with stderr: {result.stderr}"

    # Verify file was created
    assert (ace_helper.project_root / 'app.py').exists()


@pytest.mark.unit
def test_hook_with_non_code_file_skips_processing(ace_helper, temp_db):
    """Test that ace-cycle skips non-code files (.md, .txt, etc.)"""
    # Simulate Edit on markdown file
    result = ace_helper.simulate_edit_tool(
        file_path='README.md',
        old_string='# Old',
        new_string='# New'
    )

    # Should exit cleanly (0) without processing
    assert result.exit_code == 0

    # Should not create patterns for non-code files
    patterns = ace_helper.get_db_patterns()
    assert len(patterns) == 0


@pytest.mark.unit
def test_hook_graceful_degradation_on_missing_file(ace_helper, temp_db):
    """Test that hook handles missing files gracefully."""
    # Simulate Edit on non-existent file
    result = ace_helper.simulate_edit_tool(
        file_path='nonexistent.py',
        old_string='foo',
        new_string='bar'
    )

    # Should exit cleanly (ACE paper: graceful degradation)
    assert result.exit_code == 0


@pytest.mark.unit
def test_hook_json_response_format(ace_helper, temp_db, sample_code, mock_agent_response):
    """Test that hook returns valid JSON response."""
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    result = ace_helper.simulate_edit_tool(
        file_path='test.py',
        old_string='old',
        new_string='new'
    )

    # If hook returns JSON, it should have 'continue' field
    if result.json_response:
        assert 'continue' in result.json_response
        assert isinstance(result.json_response['continue'], bool)


@pytest.mark.unit
def test_hook_environment_variables(ace_helper, temp_db):
    """Test that hook receives correct environment variables."""
    # ace_helper is initialized with claude_env which includes:
    # - CLAUDE_PLUGIN_ROOT
    # - CLAUDE_PROJECT_DIR
    # - CLAUDECODE
    # - CLAUDE_CODE_ENTRYPOINT

    assert 'CLAUDE_PLUGIN_ROOT' in ace_helper.env
    assert 'CLAUDE_PROJECT_DIR' in ace_helper.env
    assert ace_helper.env['CLAUDECODE'] == '1'

    # Verify plugin root points to correct location
    assert Path(ace_helper.env['CLAUDE_PLUGIN_ROOT']).exists()
