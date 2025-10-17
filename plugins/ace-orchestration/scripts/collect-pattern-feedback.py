#!/usr/bin/env python3
"""
Pattern Feedback Collection - Generator Feedback Loop

Implements ACE research paper's Generator feedback mechanism:
"The Generator highlights which bullets were useful or misleading"

This script:
1. Reads CLAUDE.md playbook (contains bullets with IDs)
2. Asks Claude which bullets were helpful/harmful during task execution
3. Updates helpful_count and harmful_count in database
4. Enables pattern self-improvement over time

Called by: PostTaskCompletion.sh hook
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'
PLAYBOOK_PATH = PROJECT_ROOT / 'CLAUDE.md'

def extract_bullet_ids_from_playbook() -> list:
    """
    Extract all bullet IDs from CLAUDE.md playbook.

    Example:
        [py-00001] Use subprocess.run() with timeout
        [js-00023] Prefer async/await over promises

    Returns:
        List of bullet IDs: ['py-00001', 'js-00023']
    """
    if not PLAYBOOK_PATH.exists():
        return []

    import re
    content = PLAYBOOK_PATH.read_text()

    # Match [domain-NNNNN] pattern
    pattern = r'\[([a-z]+-\d{5})\]'
    matches = re.findall(pattern, content)

    return matches

def request_pattern_feedback() -> dict:
    """
    Request pattern feedback from Claude via stderr output.

    This outputs a request asking Claude to tag which patterns
    from CLAUDE.md were helpful/harmful during the last task.

    Returns:
        Empty dict (actual feedback would come from agent invocation)
    """
    bullet_ids = extract_bullet_ids_from_playbook()

    if not bullet_ids:
        return {'helpful': [], 'harmful': [], 'neutral': []}

    print(f"""
🔄 ACE Generator Feedback Request

Task completed. Please provide feedback on which patterns from CLAUDE.md helped or hurt.

<pattern_feedback_request>
{{
  "available_bullets": {json.dumps(bullet_ids)},
  "playbook_path": "{PLAYBOOK_PATH}",
  "task": "The task you just completed"
}}
</pattern_feedback_request>

OPTIONAL: Invoke feedback-collector agent to analyze CLAUDE.md usage.

The agent should output JSON:
{{
  "helpful_bullets": ["py-00001", "js-00023"],
  "harmful_bullets": ["py-00042"],
  "neutral_bullets": ["ts-00015"],
  "reasoning": "Explanation of which patterns helped/hurt and why"
}}

Feedback will increment helpful_count/harmful_count for pattern self-improvement.

To provide feedback manually, create: .ace-memory/feedback.json
""", file=sys.stderr)

    # Check for manual feedback file
    feedback_file = PROJECT_ROOT / '.ace-memory' / 'feedback.json'
    if feedback_file.exists():
        try:
            with open(feedback_file) as f:
                feedback = json.load(f)
            # Delete feedback file after reading
            feedback_file.unlink()
            return feedback
        except Exception as e:
            print(f"⚠️  Failed to read feedback file: {e}", file=sys.stderr)

    return {'helpful': [], 'harmful': [], 'neutral': []}

def update_pattern_feedback(feedback: dict):
    """
    Update helpful_count and harmful_count in database.

    Args:
        feedback: Dict with 'helpful', 'harmful', 'neutral' bullet ID lists
    """
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Update helpful bullets
    for bullet_id in feedback.get('helpful', []):
        cursor.execute('''
            UPDATE patterns
            SET helpful_count = helpful_count + 1,
                last_seen = ?
            WHERE bullet_id = ?
        ''', (datetime.now().isoformat(), f'[{bullet_id}]'))

    # Update harmful bullets
    for bullet_id in feedback.get('harmful', []):
        cursor.execute('''
            UPDATE patterns
            SET harmful_count = harmful_count + 1,
                last_seen = ?
            WHERE bullet_id = ?
        ''', (datetime.now().isoformat(), f'[{bullet_id}]'))

    # Neutral bullets - just update last_seen
    for bullet_id in feedback.get('neutral', []):
        cursor.execute('''
            UPDATE patterns
            SET last_seen = ?
            WHERE bullet_id = ?
        ''', (datetime.now().isoformat(), f'[{bullet_id}]'))

    conn.commit()

    # Log updates
    helpful_count = len(feedback.get('helpful', []))
    harmful_count = len(feedback.get('harmful', []))

    if helpful_count > 0 or harmful_count > 0:
        print(f"✅ Pattern feedback recorded: +{helpful_count} helpful, +{harmful_count} harmful", file=sys.stderr)

    conn.close()

def recalculate_confidence_scores():
    """
    Recalculate confidence scores incorporating feedback.

    New formula:
        confidence = (successes + helpful_count) / (observations + helpful_count + harmful_count)

    This combines:
    - Observation-based confidence (from test results)
    - Usage-based feedback (from Generator tagging)
    """
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Get all patterns
    cursor.execute('SELECT id, successes, observations, helpful_count, harmful_count FROM patterns')
    patterns = cursor.fetchall()

    for row in patterns:
        pattern_id, successes, observations, helpful, harmful = row

        # New confidence formula
        numerator = successes + helpful
        denominator = observations + helpful + harmful

        new_confidence = numerator / max(denominator, 1)

        # Update confidence
        cursor.execute('''
            UPDATE patterns
            SET confidence = ?
            WHERE id = ?
        ''', (new_confidence, pattern_id))

    conn.commit()
    conn.close()

    print("📊 Confidence scores recalculated with feedback", file=sys.stderr)

def main():
    """Main entry point."""
    try:
        # Read stdin (hook input - not used for now)
        # input_data = json.load(sys.stdin)

        # Request feedback from Claude
        feedback = request_pattern_feedback()

        # Update database if feedback provided
        if feedback.get('helpful') or feedback.get('harmful'):
            update_pattern_feedback(feedback)
            recalculate_confidence_scores()

            # Regenerate playbook with updated confidence scores
            import subprocess
            plugin_root = Path(__file__).parent.parent
            subprocess.run([
                'python3',
                str(plugin_root / 'scripts' / 'generate-playbook.py')
            ], check=False)

            print("✨ Playbook updated with feedback", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Pattern feedback collection failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == '__main__':
    main()
