#!/usr/bin/env python3
"""
AgentStart Hook - Inject CLAUDE.md into agent context

Ensures agents have access to the ACE playbook for guidance.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd()
PLAYBOOK_PATH = PROJECT_ROOT / 'CLAUDE.md'

def inject_playbook():
    """Inject CLAUDE.md content into agent context."""
    if not PLAYBOOK_PATH.exists():
        # No playbook yet
        print(json.dumps({'continue': True}))
        return

    # Read playbook
    playbook_content = PLAYBOOK_PATH.read_text()

    # Output injection message
    output = {
        'continue': True,
        'context_injection': {
            'file': 'CLAUDE.md',
            'content': playbook_content[:500]  # Preview only
        }
    }

    print(json.dumps(output))
    print("✅ Injected ACE playbook into agent context", file=sys.stderr)

if __name__ == '__main__':
    inject_playbook()
