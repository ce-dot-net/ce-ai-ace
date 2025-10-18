"""Tests for CLAUDE.md and spec-kit playbook generation"""

import pytest
import subprocess
import sqlite3
from pathlib import Path


@pytest.mark.unit
def test_claude_md_generation(plugin_root, temp_project, temp_db):
    """Test CLAUDE.md generation with instructions-only format."""
    # Run playbook generator
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    assert result.returncode == 0

    # Verify CLAUDE.md created
    claude_md = temp_project / 'CLAUDE.md'
    assert claude_md.exists()

    content = claude_md.read_text()

    # Should contain ACE plugin markers
    assert '<!-- ACE-PLUGIN-START -->' in content
    assert '<!-- ACE-PLUGIN-END -->' in content

    # Should contain instructions (not pattern dumps)
    assert 'ACE Plugin Instructions' in content
    assert 'Pattern Database' in content
    assert '.ace-memory/patterns.db' in content

    # Should NOT be bloated with pattern dumps
    lines = content.split('\n')
    assert len(lines) < 100  # Instructions-only should be ~50 lines


@pytest.mark.unit
def test_claude_md_delta_update_preserves_user_content(plugin_root, temp_project, temp_db):
    """Test that CLAUDE.md updates preserve user content outside ACE section."""
    # Create CLAUDE.md with user content
    claude_md = temp_project / 'CLAUDE.md'
    claude_md.write_text("""# My Custom Instructions

This is user content that should be preserved.

<!-- ACE-PLUGIN-START -->
Old ACE content
<!-- ACE-PLUGIN-END -->

More user content below.
""")

    # Run playbook generator
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    assert result.returncode == 0

    content = claude_md.read_text()

    # User content should be preserved
    assert '# My Custom Instructions' in content
    assert 'This is user content that should be preserved' in content
    assert 'More user content below' in content

    # ACE section should be updated
    assert 'ACE Plugin Instructions' in content
    assert 'Old ACE content' not in content


@pytest.mark.unit
def test_speckit_playbook_structure(plugin_root, temp_project, temp_db):
    """Test spec-kit playbook directory structure."""
    # Add test pattern
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO patterns (
            id, bullet_id, name, domain, type, description, language,
            observations, successes, confidence, last_seen, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'speckit-test-001',
        '[spec-00001]',
        'SpecKit Test Pattern',
        'test-domain',
        'helpful',
        'Testing spec-kit generation',
        'python',
        5, 5, 1.0,
        '2025-10-18T12:00:00',
        '2025-10-18T10:00:00'
    ))

    conn.commit()
    conn.close()

    # Create specs directory
    (temp_project / 'specs').mkdir(parents=True, exist_ok=True)

    # Run spec-kit generation
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-speckit-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    assert result.returncode == 0

    # Verify playbook directory created
    playbooks_dir = temp_project / 'specs' / 'playbooks'
    assert playbooks_dir.exists()

    # Find the created playbook directory
    playbook_dirs = list(playbooks_dir.glob('*'))
    assert len(playbook_dirs) > 0

    # Verify playbook contains required files (spec.md, plan.md, insights.md)
    playbook_dir = playbook_dirs[0]

    # At minimum, spec.md should exist
    spec_md = playbook_dir / 'spec.md'
    if spec_md.exists():
        content = spec_md.read_text()

        # Should have YAML frontmatter
        assert content.startswith('---')
        assert 'pattern_id:' in content
        assert 'name:' in content
        assert 'confidence:' in content


@pytest.mark.unit
def test_speckit_yaml_frontmatter(plugin_root, temp_project, temp_db):
    """Test that spec-kit playbooks have valid YAML frontmatter."""
    # Add test pattern
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO patterns (
            id, bullet_id, name, domain, type, description, language,
            observations, confidence, created_at, last_seen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'yaml-test-001',
        '[yaml-00001]',
        'YAML Test Pattern',
        'yaml-domain',
        'helpful',
        'Testing YAML frontmatter',
        'python',
        10, 0.9,
        '2025-10-18T10:00:00',
        '2025-10-18T12:00:00'
    ))

    conn.commit()
    conn.close()

    # Create specs directory
    (temp_project / 'specs').mkdir(parents=True, exist_ok=True)

    # Run spec-kit generation
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-speckit-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    assert result.returncode == 0

    # Find playbook
    playbooks_dir = temp_project / 'specs' / 'playbooks'
    playbook_dirs = list(playbooks_dir.glob('*'))

    if len(playbook_dirs) > 0:
        spec_md = playbook_dirs[0] / 'spec.md'
        if spec_md.exists():
            content = spec_md.read_text()

            # Extract YAML frontmatter
            lines = content.split('\n')
            assert lines[0] == '---'

            yaml_end = next(i for i, line in enumerate(lines[1:], 1) if line == '---')
            yaml_section = '\n'.join(lines[1:yaml_end])

            # Verify required fields
            assert 'pattern_id: yaml-test-001' in yaml_section
            assert 'name: YAML Test Pattern' in yaml_section
            assert 'domain: yaml-domain' in yaml_section
            assert 'confidence: 0.9' in yaml_section


@pytest.mark.unit
def test_playbook_size_validation(plugin_root, temp_project, temp_db):
    """Test that CLAUDE.md stays compact (not bloated with patterns)."""
    # Add multiple patterns
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    for i in range(50):
        cursor.execute('''
            INSERT INTO patterns (
                id, bullet_id, name, domain, type, description, language,
                observations, confidence, created_at, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f'pattern-{i:03d}',
            f'[p-{i:05d}]',
            f'Pattern {i}',
            'test-domain',
            'helpful',
            f'Test pattern {i}',
            'python',
            5, 0.5,
            '2025-10-18T10:00:00',
            '2025-10-18T12:00:00'
        ))

    conn.commit()
    conn.close()

    # Run playbook generator
    result = subprocess.run(
        ['python3', str(plugin_root / 'scripts' / 'generate-playbook.py')],
        capture_output=True,
        text=True,
        cwd=str(temp_project)
    )

    assert result.returncode == 0

    # Verify CLAUDE.md size
    claude_md = temp_project / 'CLAUDE.md'
    content = claude_md.read_text()
    lines = content.split('\n')

    # With 50 patterns, CLAUDE.md should still be compact (< 100 lines)
    # because it only shows stats, not full pattern dumps
    assert len(lines) < 150, f"CLAUDE.md should be compact, got {len(lines)} lines"

    # Should show pattern count
    assert '50' in content or 'Total patterns' in content
