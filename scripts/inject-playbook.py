#!/usr/bin/env python3
"""
AgentStart Hook - Dynamic Playbook Injection

Injects relevant patterns based on context (ACE paper Section 3.1).
Uses dynamic retrieval from spec-kit playbooks for efficiency.
"""

import json
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path.cwd()
PLAYBOOK_PATH = PROJECT_ROOT / 'CLAUDE.md'
SPECS_ROOT = PROJECT_ROOT / 'specs'
PLAYBOOKS_DIR = SPECS_ROOT / 'playbooks'
CONSTITUTION_PATH = SPECS_ROOT / 'memory' / 'constitution.md'

def read_speckit_playbooks(current_file: str = '') -> str:
    """
    Read spec-kit structured playbooks with dynamic filtering.

    Returns formatted markdown for context injection.
    """
    if not PLAYBOOKS_DIR.exists():
        return ""

    content = []

    # Always include constitution (principles)
    if CONSTITUTION_PATH.exists():
        content.append(CONSTITUTION_PATH.read_text())
        content.append("\n---\n")

    # Dynamic retrieval: filter playbooks by file context
    playbook_dirs = sorted(PLAYBOOKS_DIR.glob('*'))

    if current_file:
        # Determine language from file extension
        ext = Path(current_file).suffix
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript'
        }
        target_lang = lang_map.get(ext)

        # Filter relevant playbooks
        relevant_playbooks = []
        for playbook_dir in playbook_dirs:
            spec_file = playbook_dir / 'spec.md'
            if spec_file.exists():
                # Quick check if language matches
                spec_content = spec_file.read_text()
                if target_lang and f'language: {target_lang}' in spec_content.lower():
                    relevant_playbooks.append(playbook_dir)

        # Limit to top 5 most relevant
        playbook_dirs = relevant_playbooks[:5]

    # Read relevant playbooks
    for playbook_dir in playbook_dirs[:10]:  # Max 10 playbooks
        spec_file = playbook_dir / 'spec.md'
        plan_file = playbook_dir / 'plan.md'

        if spec_file.exists():
            content.append(f"## Playbook: {playbook_dir.name}\n")
            content.append(spec_file.read_text())
            content.append("\n")

            # Include plan if available
            if plan_file.exists():
                content.append("### Technical Plan\n")
                # Read plan but skip YAML frontmatter
                plan_lines = plan_file.read_text().split('\n')
                in_frontmatter = False
                plan_content = []
                for line in plan_lines:
                    if line.strip() == '---':
                        if not in_frontmatter:
                            in_frontmatter = True
                            continue
                        else:
                            in_frontmatter = False
                            continue
                    if not in_frontmatter:
                        plan_content.append(line)
                content.append('\n'.join(plan_content))

            content.append("\n---\n")

    return ''.join(content)

def inject_playbook():
    """
    Inject playbook with dynamic pattern retrieval.

    ACE Enhancement: Reads from spec-kit playbooks with dynamic filtering,
    only injecting the most relevant patterns based on file context.
    """
    # Read hook input to get context
    try:
        input_data = json.load(sys.stdin)
        current_file = input_data.get('current_file', '')
    except:
        current_file = ''

    # Try spec-kit format first
    playbook_content = read_speckit_playbooks(current_file)
    source = 'specs/'

    # Fallback to legacy CLAUDE.md if specs/ doesn't exist
    if not playbook_content:
        if PLAYBOOK_PATH.exists():
            playbook_content = PLAYBOOK_PATH.read_text()
            source = 'CLAUDE.md'
        else:
            playbook_content = "# ACE Playbook\n\nLearning patterns..."
            source = 'default'

    # Additional dynamic retrieval from pattern-retrieval.py (if available)
    relevant_patterns = ""
    if current_file and source != 'specs/':
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
            'file': 'ACE Playbook',
            'content': playbook_content,
            'source': source,
            'dynamic': bool(relevant_patterns) or (source == 'specs/' and current_file),
            'preview': playbook_content[:500]
        }
    }

    print(json.dumps(output))

    if source == 'specs/':
        filtered_count = len([p for p in playbook_content.split('## Playbook:') if p.strip()])
        print(f"✅ Injected {filtered_count} spec-kit playbooks into agent context", file=sys.stderr)
    elif not relevant_patterns:
        print("✅ Injected full ACE playbook into agent context", file=sys.stderr)

if __name__ == '__main__':
    inject_playbook()
