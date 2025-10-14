#!/usr/bin/env python3
"""
Dynamic Pattern Retrieval - Context-Aware Playbook Injection

Implements ACE paper Section 3.1:
"Fine-grained retrieval, so the Generator can focus on the most pertinent knowledge"

Retrieves relevant patterns based on:
- File type (Python vs JS vs TS)
- Domain (async, typing, error-handling)
- Recent success rate
- Current task context
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

def get_relevant_patterns(
    file_path: str,
    task_domains: Optional[List[str]] = None,
    min_confidence: float = 0.3,
    max_patterns: int = 10
) -> List[Dict]:
    """
    Retrieve patterns relevant to current context.

    Args:
        file_path: Path to file being worked on
        task_domains: Relevant domains (e.g., ['async', 'error-handling'])
        min_confidence: Minimum confidence threshold
        max_patterns: Maximum patterns to return

    Returns:
        List of relevant patterns, ranked by relevance
    """
    if not DB_PATH.exists():
        return []

    # Determine language from file extension
    ext = Path(file_path).suffix
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript'
    }
    language = lang_map.get(ext)

    if not language:
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    query = '''
        SELECT *,
            (confidence * 0.5 +
             CAST(helpful_count AS REAL) / NULLIF(helpful_count + harmful_count, 0) * 0.3 +
             CAST(successes AS REAL) / NULLIF(observations, 0) * 0.2) as relevance_score
        FROM patterns
        WHERE language = ?
          AND confidence >= ?
          AND type = 'helpful'
    '''
    params = [language, min_confidence]

    # Add domain filtering if specified
    if task_domains:
        domain_conditions = ' OR '.join(['domain LIKE ?' for _ in task_domains])
        query += f' AND ({domain_conditions})'
        params.extend([f'%{domain}%' for domain in task_domains])

    query += ' ORDER BY relevance_score DESC LIMIT ?'
    params.append(max_patterns)

    cursor.execute(query, params)
    patterns = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return patterns

def format_patterns_for_injection(patterns: List[Dict]) -> str:
    """
    Format patterns for injection into Generator context.

    Returns markdown-formatted playbook section.
    """
    if not patterns:
        return ""

    lines = [
        "## 🎯 Relevant Patterns for This File\n",
        "*Auto-selected based on file type, domain, and confidence*\n"
    ]

    for pattern in patterns:
        confidence_pct = pattern['confidence'] * 100
        obs = pattern['observations']

        lines.append(f"\n### {pattern['name']}")
        lines.append(f"**Confidence:** {confidence_pct:.0f}% ({obs} observations)")
        lines.append(f"**Domain:** {pattern['domain']}")
        lines.append(f"\n{pattern['description']}\n")

        # Get latest insight
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT insight, recommendation FROM insights
            WHERE pattern_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (pattern['id'],))

        insight_row = cursor.fetchone()
        conn.close()

        if insight_row:
            lines.append(f"**Latest Insight:** {insight_row['insight']}")
            lines.append(f"**Recommendation:** {insight_row['recommendation']}")

    return '\n'.join(lines)

def inject_for_file(file_path: str) -> str:
    """
    Generate context injection for a specific file.

    Returns:
        Markdown text to inject into Generator context
    """
    # Infer domains from file path
    task_domains = []

    # Check for common patterns in path
    path_lower = file_path.lower()
    if 'test' in path_lower:
        task_domains.append('testing')
    if 'async' in path_lower or 'promise' in path_lower:
        task_domains.append('async')
    if 'api' in path_lower or 'endpoint' in path_lower:
        task_domains.append('api')
    if 'error' in path_lower or 'exception' in path_lower:
        task_domains.append('error-handling')
    if 'type' in path_lower or 'interface' in path_lower:
        task_domains.append('typing')

    # Get relevant patterns
    patterns = get_relevant_patterns(
        file_path=file_path,
        task_domains=task_domains if task_domains else None,
        min_confidence=0.5,  # Only show medium+ confidence
        max_patterns=5  # Top 5 most relevant
    )

    return format_patterns_for_injection(patterns)

def main():
    """CLI for testing pattern retrieval."""
    import argparse

    parser = argparse.ArgumentParser(description='ACE Dynamic Pattern Retrieval')
    parser.add_argument('file_path', help='File path to get patterns for')
    parser.add_argument('--domains', nargs='*', help='Task domains')
    parser.add_argument('--min-confidence', type=float, default=0.3)
    parser.add_argument('--max-patterns', type=int, default=10)

    args = parser.parse_args()

    patterns = get_relevant_patterns(
        file_path=args.file_path,
        task_domains=args.domains,
        min_confidence=args.min_confidence,
        max_patterns=args.max_patterns
    )

    print(f"Found {len(patterns)} relevant patterns:\n")
    for i, p in enumerate(patterns, 1):
        print(f"{i}. [{p['id']}] {p['name']}")
        print(f"   Confidence: {p['confidence']:.0%} | Domain: {p['domain']}")
        print()

if __name__ == '__main__':
    main()
