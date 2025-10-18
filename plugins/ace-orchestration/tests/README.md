# ACE Plugin Test Suite

Comprehensive test suite for the ACE (Agentic Context Engineering) plugin using pytest.

## Overview

This test suite simulates Claude Code CLI behavior to test ACE plugin hooks, agents, scripts, ChromaDB embeddings, and spec-kit playbook generation **without requiring an interactive shell**.

## Test Structure

```
tests/
├── conftest.py                 # pytest fixtures and configuration
├── ace_test_helper.py          # Claude Code CLI simulator
├── test_hooks.py              # Hook tests (PostToolUse, etc.)
├── test_scripts.py            # Script execution tests
├── test_playbooks.py          # CLAUDE.md + spec-kit tests
├── test_integration.py        # Full ACE workflow tests
├── fixtures/
│   ├── sample_code.py         # Test code for pattern discovery
│   ├── hook_inputs.json       # Sample Claude Code hook JSONs
│   └── expected_patterns.json # Expected pattern outputs
├── requirements-test.txt      # Test dependencies
└── README.md                  # This file
```

## Installation

```bash
# Install test dependencies
pip install -r plugins/ace-orchestration/tests/requirements-test.txt
```

## Running Tests

### All Tests
```bash
pytest plugins/ace-orchestration/tests/
```

### Specific Test File
```bash
pytest plugins/ace-orchestration/tests/test_hooks.py
```

### By Marker
```bash
# Run only unit tests (fast, mocked)
pytest -m unit

# Run only integration tests (slower, real components)
pytest -m integration
```

### With Coverage
```bash
pytest --cov=plugins/ace-orchestration/scripts --cov-report=html
```

### Verbose Output
```bash
pytest -v plugins/ace-orchestration/tests/
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Fast tests with mocked dependencies:
- Hook execution with simulated Claude Code JSON stdin
- Script validation
- Database schema checks
- Playbook generation

### Integration Tests (`@pytest.mark.integration`)
Slower tests using real components:
- Full ACE workflow (Edit → patterns → playbooks)
- Pattern merging and curation
- Multi-file pattern discovery
- End-to-end playbook generation

## Key Components

### ACE Test Helper

The `ACETestHelper` class simulates Claude Code CLI behavior:

```python
from ace_test_helper import ACETestHelper

# Create helper
ace_helper = ACETestHelper(plugin_root, temp_project, claude_env)

# Simulate Edit tool → PostToolUse hook
result = ace_helper.simulate_edit_tool('test.py', old='', new='code')

# Mock agent responses
ace_helper.mock_agent_response('reflector', response_json, 'file.py')

# Check database
patterns = ace_helper.get_db_patterns()
assert ace_helper.assert_pattern_stored('pattern-id')
```

### Fixtures

Key pytest fixtures from `conftest.py`:

- `plugin_root`: Path to plugin directory
- `project_root`: Path to project root
- `temp_project`: Isolated temporary project directory
- `temp_db`: Initialized ACE database with schema
- `claude_env`: Claude Code environment variables
- `sample_code`: Sample Python code for testing
- `mock_agent_response`: Pre-recorded agent responses

## Test Examples

### Testing PostToolUse Hook

```python
def test_post_tool_use_edit(ace_helper, temp_db, sample_code, mock_agent_response):
    # Mock agent to avoid real invocation
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'test.py')

    # Create test file
    test_file = ace_helper.project_root / 'test.py'
    test_file.write_text(sample_code)

    # Trigger hook
    result = ace_helper.simulate_edit_tool('test.py', '', '')

    # Verify
    assert result.exit_code == 0
    assert ace_helper.assert_pattern_stored('test-pattern-001')
```

### Testing Playbook Generation

```python
def test_claude_md_generation(plugin_root, temp_project, temp_db):
    # Run playbook generator
    subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        cwd=str(temp_project),
        check=True
    )

    # Verify CLAUDE.md
    claude_md = temp_project / 'CLAUDE.md'
    assert claude_md.exists()
    assert 'ACE Plugin Instructions' in claude_md.read_text()
```

### Testing Full Workflow

```python
@pytest.mark.integration
def test_full_ace_workflow(ace_helper, temp_db, sample_code, mock_agent_response):
    # Mock agent
    ace_helper.mock_agent_response('reflector', mock_agent_response, 'app.py')

    # Trigger Edit
    test_file = ace_helper.project_root / 'app.py'
    test_file.write_text(sample_code)
    result = ace_helper.simulate_edit_tool('app.py', '', '')

    # Verify patterns stored
    assert ace_helper.assert_pattern_stored('test-pattern-001')

    # Generate playbooks
    subprocess.run([...], check=True)

    # Verify CLAUDE.md and spec-kit
    assert (ace_helper.project_root / 'CLAUDE.md').exists()
    assert (ace_helper.project_root / 'specs/playbooks').exists()
```

## What's Tested

✅ **Hooks**: PostToolUse, AgentStart, SessionEnd
✅ **Scripts**: ace-cycle.py, generate-playbook.py, generate-speckit-playbook.py
✅ **Database**: SQLite schema, pattern storage, insights, observations
✅ **Playbooks**: CLAUDE.md generation, delta updates, spec-kit structure
✅ **YAML Frontmatter**: spec.md metadata validation
✅ **Workflow**: Edit → patterns → playbooks (full integration)
✅ **Graceful Degradation**: Handles missing files, agent failures
✅ **Pattern Merging**: Multiple observations of same pattern

## Environment Variables

Tests simulate Claude Code environment:

- `CLAUDE_PLUGIN_ROOT`: Plugin directory path
- `CLAUDE_PROJECT_DIR`: Project directory path
- `CLAUDECODE`: Set to '1'
- `CLAUDE_CODE_ENTRYPOINT`: Set to 'cli'

## Troubleshooting

### Tests failing with "FileNotFoundError: Hook script not found"
Ensure you're running from project root or plugin root.

### Tests failing with "sqlite3.OperationalError"
Database schema may be outdated. Delete `.ace-memory/patterns.db` and rerun.

### Agent tests hanging
Agent responses should be mocked using `ace_helper.mock_agent_response()`.

### Import errors
Install test requirements: `pip install -r tests/requirements-test.txt`

## CI/CD Integration

```yaml
# Example GitHub Actions
- name: Run ACE tests
  run: |
    pip install -r plugins/ace-orchestration/tests/requirements-test.txt
    pytest plugins/ace-orchestration/tests/ --cov --cov-report=xml
```

## Contributing

When adding new tests:
1. Use `@pytest.mark.unit` for fast tests with mocks
2. Use `@pytest.mark.integration` for end-to-end tests
3. Add fixtures to `conftest.py` if reusable
4. Update this README with examples

## Reference

- **ACE Research Paper**: https://arxiv.org/abs/2510.04618
- **Claude Code Hooks**: https://docs.claude.com/en/docs/claude-code/hooks
- **pytest Documentation**: https://docs.pytest.org/
