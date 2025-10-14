#!/usr/bin/env python3
"""
AgentStart Hook - Dynamic Playbook Injection

Injects relevant patterns based on context (ACE paper Section 3.1).
Uses dynamic retrieval instead of full playbook for efficiency.
"""

import json
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path.cwd()
PLAYBOOK_PATH = PROJECT_ROOT / 'CLAUDE.md'

def inject_playbook():
    """
    Inject playbook with dynamic pattern retrieval.

    ACE Enhancement: Instead of injecting full playbook, retrieve
    only the most relevant patterns based on file context.
    """
    # Read hook input to get context
    try:
        input_data = json.load(sys.stdin)
        current_file = input_data.get('current_file', '')
    except:
        current_file = ''

    # Base playbook content
    if PLAYBOOK_PATH.exists():
        playbook_content = PLAYBOOK_PATH.read_text()
    else:
        playbook_content = "# ACE Playbook\n\nLearning patterns..."

    # Dynamic retrieval: Get relevant patterns for current file
    relevant_patterns = ""
    if current_file:
        try:
            from pattern_retrieval import inject_for_file
            relevant_patterns = inject_for_file(current_file)

            if relevant_patterns:
                # Prepend relevant patterns
                playbook_content = relevant_patterns + "\n\n---\n\n" + playbook_content
                print(f"✅ Injected {len(relevant_patterns.split('###')) - 1} relevant patterns for {current_file}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Dynamic retrieval failed: {e}", file=sys.stderr)

    # Output injection
    output = {
        'continue': True,
        'context_injection': {
            'file': 'CLAUDE.md',
            'content': playbook_content,
            'dynamic': bool(relevant_patterns),
            'preview': playbook_content[:500]
        }
    }

    print(json.dumps(output))

    if not relevant_patterns:
        print("✅ Injected full ACE playbook into agent context", file=sys.stderr)

if __name__ == '__main__':
    inject_playbook()
