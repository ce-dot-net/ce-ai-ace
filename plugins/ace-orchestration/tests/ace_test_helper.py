"""ACE Test Helper - Claude Code CLI Simulator

This module provides utilities to simulate Claude Code CLI behavior for testing
ACE plugin hooks, agents, and scripts without requiring an interactive shell.
"""

import json
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class HookResult:
    """Result from hook execution."""
    exit_code: int
    stdout: str
    stderr: str
    json_response: Optional[Dict] = None


class ACETestHelper:
    """Helper class to simulate Claude Code CLI interactions."""

    def __init__(self, plugin_root: Path, project_root: Path, env: Dict[str, str]):
        """
        Initialize ACE Test Helper.

        Args:
            plugin_root: Path to plugin directory
            project_root: Path to project directory (usually temp dir in tests)
            env: Environment variables dict (from claude_env fixture)
        """
        self.plugin_root = plugin_root
        self.project_root = project_root
        self.env = env.copy()
        self.scripts_dir = plugin_root / 'scripts'

    def run_hook(
        self,
        hook_name: str,
        hook_input: Dict[str, Any],
        timeout: int = 30
    ) -> HookResult:
        """
        Execute a hook script with Claude Code JSON stdin.

        This simulates how Claude Code CLI executes hooks by:
        1. Setting proper environment variables
        2. Piping JSON input to the script via stdin
        3. Capturing stdout/stderr
        4. Parsing JSON response if present

        Args:
            hook_name: Name of hook script (e.g., 'ace-cycle', 'inject-playbook')
            hook_input: Claude Code hook input JSON
            timeout: Timeout in seconds

        Returns:
            HookResult with exit_code, stdout, stderr, and optional json_response
        """
        script_path = self.scripts_dir / f'{hook_name}.py'

        if not script_path.exists():
            raise FileNotFoundError(f"Hook script not found: {script_path}")

        # Run script with JSON stdin
        result = subprocess.run(
            ['python3', str(script_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=self.env,
            cwd=str(self.project_root)
        )

        # Try to parse JSON response from stdout
        json_response = None
        if result.stdout.strip():
            try:
                json_response = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                # Not JSON output, that's fine
                pass

        return HookResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            json_response=json_response
        )

    def simulate_post_tool_use(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_response: Dict[str, Any]
    ) -> HookResult:
        """
        Simulate PostToolUse hook trigger.

        Args:
            tool_name: Tool that was executed (e.g., 'Edit', 'Write')
            tool_input: Tool input parameters
            tool_response: Tool execution result

        Returns:
            HookResult from ace-cycle.py execution
        """
        hook_input = {
            'session_id': 'test-session',
            'transcript_path': str(self.project_root / 'transcript.jsonl'),
            'cwd': str(self.project_root),
            'hook_event_name': 'PostToolUse',
            'tool_name': tool_name,
            'tool_input': tool_input,
            'tool_response': tool_response
        }

        return self.run_hook('ace-cycle', hook_input)

    def simulate_edit_tool(
        self,
        file_path: str,
        old_string: str = '',
        new_string: str = ''
    ) -> HookResult:
        """
        Simulate Edit tool call → PostToolUse hook.

        Args:
            file_path: File being edited
            old_string: Old content (for Edit tool)
            new_string: New content

        Returns:
            HookResult from PostToolUse hook
        """
        tool_input = {
            'file_path': file_path,
            'old_string': old_string,
            'new_string': new_string
        }

        tool_response = {
            'filePath': file_path,
            'success': True
        }

        return self.simulate_post_tool_use('Edit', tool_input, tool_response)

    def simulate_write_tool(
        self,
        file_path: str,
        content: str
    ) -> HookResult:
        """
        Simulate Write tool call → PostToolUse hook.

        Args:
            file_path: File being written
            content: File content

        Returns:
            HookResult from PostToolUse hook
        """
        # Create the file in temp project
        full_path = self.project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

        tool_input = {
            'file_path': file_path,
            'content': content
        }

        tool_response = {
            'filePath': file_path,
            'success': True
        }

        return self.simulate_post_tool_use('Write', tool_input, tool_response)

    def mock_agent_response(
        self,
        agent_name: str,
        response: Dict[str, Any],
        file_path: str = 'test.py'
    ):
        """
        Pre-record agent response for testing.

        Creates a cached agent response in the reflections directory
        so ace-cycle.py can read it without invoking real agent.

        Args:
            agent_name: Agent name (e.g., 'reflector')
            response: Agent response JSON
            file_path: File path for the reflection cache
        """
        reflections_dir = self.project_root / '.ace-memory' / 'reflections'
        reflections_dir.mkdir(parents=True, exist_ok=True)

        # Create response file
        response_file = reflections_dir / f'{Path(file_path).name}.json'
        response_file.write_text(json.dumps(response, indent=2))

    def get_db_patterns(self) -> list:
        """
        Get all patterns from the ACE database.

        Returns:
            List of pattern dictionaries
        """
        import sqlite3

        db_path = self.project_root / '.ace-memory' / 'patterns.db'
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM patterns')
        patterns = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return patterns

    def assert_pattern_stored(self, pattern_id: str) -> bool:
        """
        Assert that a pattern with the given ID is stored in the database.

        Args:
            pattern_id: Pattern ID to check

        Returns:
            True if pattern exists, False otherwise
        """
        patterns = self.get_db_patterns()
        return any(p['id'] == pattern_id for p in patterns)
