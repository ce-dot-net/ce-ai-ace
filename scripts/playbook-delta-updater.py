#!/usr/bin/env python3
"""
Delta-based CLAUDE.md updater - ACE Phase 3

Implements incremental delta updates as per ACE paper:
- NO full rewrites (prevents context collapse)
- Localized, structured changes only
- Track additions, updates, deletions
- Preserve existing content

ACE Paper: "Incremental updates only - Never full rewrites"
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

PROJECT_ROOT = Path.cwd()
PLAYBOOK_PATH = PROJECT_ROOT / 'CLAUDE.md'
PLAYBOOK_HISTORY = PROJECT_ROOT / '.ace-memory' / 'playbook-history.txt'

class PlaybookSection:
    """Represents a section of CLAUDE.md"""
    def __init__(self, title: str, level: int, content: str, bullets: List[str]):
        self.title = title
        self.level = level  # 1=##, 2=###
        self.content = content
        self.bullets = bullets  # [bullet_id, ...]

class PlaybookDelta:
    """Represents changes to apply to CLAUDE.md"""
    def __init__(self):
        self.additions = []      # (section, bullet_id, content)
        self.updates = []        # (section, bullet_id, old_content, new_content)
        self.deletions = []      # (section, bullet_id)
        self.metadata_changes = {}  # {'total_patterns': 5, ...}

def parse_existing_playbook() -> Dict[str, PlaybookSection]:
    """Parse existing CLAUDE.md into structured sections."""
    if not PLAYBOOK_PATH.exists():
        return {}

    content = PLAYBOOK_PATH.read_text()
    sections = {}

    # Split by ## headers
    pattern = r'^(#{2,3})\s+(.+?)$'
    lines = content.split('\n')

    current_section = None
    current_level = 0
    current_content = []
    current_bullets = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = PlaybookSection(
                    title=current_section,
                    level=current_level,
                    content='\n'.join(current_content),
                    bullets=current_bullets
                )

            # Start new section
            level = len(match.group(1))
            title = match.group(2).strip()
            current_section = title
            current_level = level
            current_content = []
            current_bullets = []

        else:
            current_content.append(line)

            # Extract bullet IDs
            bullet_match = re.match(r'\[(\w+-\d+)\]', line)
            if bullet_match:
                current_bullets.append(bullet_match.group(1))

    # Save last section
    if current_section:
        sections[current_section] = PlaybookSection(
            title=current_section,
            level=current_level,
            content='\n'.join(current_content),
            bullets=current_bullets
        )

    return sections

def extract_bullet_content(line: str) -> Tuple[Optional[str], str]:
    """
    Extract bullet_id and content from a line.

    Example:
    "[py-00001] helpful=5 harmful=1 :: **Use TypedDict**"
    Returns: ('py-00001', 'helpful=5 harmful=1 :: **Use TypedDict**')
    """
    match = re.match(r'\[(\w+-\d+)\]\s+(.+)', line)
    if match:
        return match.group(1), match.group(2)
    return None, line

def compute_delta(old_sections: Dict[str, PlaybookSection],
                  new_content: str) -> PlaybookDelta:
    """
    Compute delta between old and new playbook content.

    Returns:
        PlaybookDelta with additions, updates, deletions
    """
    delta = PlaybookDelta()

    # Parse new content into sections
    new_sections = {}
    lines = new_content.split('\n')

    pattern = r'^(#{2,3})\s+(.+?)$'
    current_section = None
    current_bullets = {}  # {bullet_id: full_line}

    for line in lines:
        match = re.match(pattern, line)
        if match:
            # Save previous section's bullets
            if current_section and current_bullets:
                new_sections[current_section] = current_bullets
                current_bullets = {}

            # Start new section
            title = match.group(2).strip()
            current_section = title

        else:
            # Extract bullet if present
            bullet_id, content = extract_bullet_content(line.strip())
            if bullet_id:
                current_bullets[bullet_id] = line

    # Save last section
    if current_section and current_bullets:
        new_sections[current_section] = current_bullets

    # Compare sections
    for section_title, new_bullets in new_sections.items():
        old_section = old_sections.get(section_title)

        if not old_section:
            # New section - add all bullets
            for bullet_id, content in new_bullets.items():
                delta.additions.append((section_title, bullet_id, content))
            continue

        # Get old bullets
        old_bullets = {}
        for line in old_section.content.split('\n'):
            bullet_id, _ = extract_bullet_content(line.strip())
            if bullet_id:
                old_bullets[bullet_id] = line

        # Find additions and updates
        for bullet_id, new_line in new_bullets.items():
            if bullet_id not in old_bullets:
                # Addition
                delta.additions.append((section_title, bullet_id, new_line))
            elif old_bullets[bullet_id] != new_line:
                # Update
                delta.updates.append((
                    section_title,
                    bullet_id,
                    old_bullets[bullet_id],
                    new_line
                ))

        # Find deletions
        for bullet_id in old_bullets:
            if bullet_id not in new_bullets:
                delta.deletions.append((section_title, bullet_id))

    return delta

def apply_delta(delta: PlaybookDelta) -> bool:
    """
    Apply delta to CLAUDE.md with surgical precision.

    Returns:
        True if changes were applied, False otherwise
    """
    if not PLAYBOOK_PATH.exists():
        print("⚠️  No CLAUDE.md to update", file=sys.stderr)
        return False

    content = PLAYBOOK_PATH.read_text()
    lines = content.split('\n')

    # Track changes
    changes_made = False

    # Apply updates (in-place replacements)
    for section, bullet_id, old_line, new_line in delta.updates:
        # Find and replace the line
        for i, line in enumerate(lines):
            if bullet_id in line and old_line.strip() in line:
                lines[i] = line.replace(old_line.strip(), new_line.strip())
                changes_made = True
                print(f"  ✏️  Updated [{bullet_id}] in section '{section}'", file=sys.stderr)
                break

    # Apply deletions
    for section, bullet_id in delta.deletions:
        # Find and remove the line
        new_lines = []
        for line in lines:
            if bullet_id not in line:
                new_lines.append(line)
            else:
                changes_made = True
                print(f"  🗑️  Deleted [{bullet_id}] from section '{section}'", file=sys.stderr)
        lines = new_lines

    # Apply additions (append to section)
    for section, bullet_id, new_line in delta.additions:
        # Find section
        section_pattern = rf'^#{2,3}\s+{re.escape(section)}'
        section_index = None

        for i, line in enumerate(lines):
            if re.match(section_pattern, line):
                section_index = i
                break

        if section_index is not None:
            # Find end of section (next ## or end of file)
            insert_index = section_index + 1
            for i in range(section_index + 1, len(lines)):
                if re.match(r'^#{2,3}\s+', lines[i]):
                    insert_index = i
                    break
                insert_index = i + 1

            # Insert before section end
            lines.insert(insert_index, new_line)
            changes_made = True
            print(f"  ✨ Added [{bullet_id}] to section '{section}'", file=sys.stderr)

    if changes_made:
        # Write updated content
        PLAYBOOK_PATH.write_text('\n'.join(lines))

        # Log to history
        log_delta_to_history(delta)

        return True

    return False

def log_delta_to_history(delta: PlaybookDelta):
    """Log delta changes to history file for auditing."""
    PLAYBOOK_HISTORY.parent.mkdir(parents=True, exist_ok=True)

    with open(PLAYBOOK_HISTORY, 'a') as f:
        f.write(f"\n--- Delta Applied: {datetime.now().isoformat()} ---\n")
        f.write(f"Additions: {len(delta.additions)}\n")
        f.write(f"Updates: {len(delta.updates)}\n")
        f.write(f"Deletions: {len(delta.deletions)}\n")

        if delta.additions:
            f.write("\nAdded:\n")
            for section, bullet_id, _ in delta.additions:
                f.write(f"  - [{bullet_id}] in '{section}'\n")

        if delta.updates:
            f.write("\nUpdated:\n")
            for section, bullet_id, _, _ in delta.updates:
                f.write(f"  - [{bullet_id}] in '{section}'\n")

        if delta.deletions:
            f.write("\nDeleted:\n")
            for section, bullet_id in delta.deletions:
                f.write(f"  - [{bullet_id}] from '{section}'\n")

def update_playbook_with_delta(new_content: str) -> bool:
    """
    Main entry point: Update CLAUDE.md with delta instead of full rewrite.

    Args:
        new_content: Full new playbook content (will be diffed)

    Returns:
        True if changes were applied
    """
    print("🔄 Computing playbook delta...", file=sys.stderr)

    # Parse existing playbook
    old_sections = parse_existing_playbook()

    if not old_sections:
        # No existing playbook - write full content (first time only)
        PLAYBOOK_PATH.write_text(new_content)
        print("✨ Created initial CLAUDE.md (full write)", file=sys.stderr)
        return True

    # Compute delta
    delta = compute_delta(old_sections, new_content)

    # Check if there are changes
    total_changes = len(delta.additions) + len(delta.updates) + len(delta.deletions)

    if total_changes == 0:
        print("✅ No changes to apply", file=sys.stderr)
        return False

    print(f"📊 Delta: +{len(delta.additions)} ~{len(delta.updates)} -{len(delta.deletions)}", file=sys.stderr)

    # Apply delta
    success = apply_delta(delta)

    if success:
        print("✅ Delta applied successfully", file=sys.stderr)
    else:
        print("⚠️  Failed to apply delta", file=sys.stderr)

    return success

if __name__ == '__main__':
    # Test with sample content
    sample = """## 🎯 STRATEGIES AND HARD RULES

[py-00001] helpful=5 harmful=1 :: **Use TypedDict**
Description here.

[py-00002] helpful=3 harmful=0 :: **Use dataclasses**
Description here.
"""

    success = update_playbook_with_delta(sample)
    sys.exit(0 if success else 1)
