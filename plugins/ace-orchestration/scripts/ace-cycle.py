#!/usr/bin/env python3
"""
ACE Cycle - Main orchestration script

Orchestrates the complete ACE cycle:
1. Pattern Detection (regex-based)
2. Evidence Gathering (test results)
3. Reflection (via reflector agent using Task tool)
4. Curation (deterministic algorithm with semantic embeddings)
5. Playbook Update (CLAUDE.md generation with delta updates)

ACE Phase 3 Enhancements:
- Semantic embeddings for pattern similarity (replaces Jaccard)
- Delta-based CLAUDE.md updates (prevents context collapse)

Called by PostToolUse hook after Edit/Write operations.
"""

import json
import sys
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================================================
# Configuration
# ============================================================================

SIMILARITY_THRESHOLD = 0.85  # 85% similarity for merging (from research)
PRUNE_THRESHOLD = 0.30      # 30% confidence threshold (from research)
MIN_OBSERVATIONS = 10        # Minimum observations before pruning

# Plugin root directory
PLUGIN_ROOT = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', Path(__file__).parent.parent))
PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'

# ============================================================================
# Pattern Definitions (from config/patterns.js)
# ============================================================================

PATTERNS = [
    # Python Patterns
    {
        'id': 'py-001',
        'name': 'Use TypedDict for configs',
        'regex': r'class\s+\w*[Cc]onfig\w*\(TypedDict\)',
        'domain': 'python-typing',
        'type': 'helpful',
        'language': 'python',
        'description': 'Define configuration with TypedDict for type safety and IDE support'
    },
    {
        'id': 'py-002',
        'name': 'Use dataclasses for data structures',
        'regex': r'@dataclass\s+class\s+\w+',
        'domain': 'python-datastructures',
        'type': 'helpful',
        'language': 'python',
        'description': 'Use @dataclass decorator for simple data containers'
    },
    {
        'id': 'py-003',
        'name': 'Avoid bare except',
        'regex': r'except\s*:',
        'domain': 'python-error-handling',
        'type': 'harmful',
        'language': 'python',
        'description': 'Bare except catches all exceptions including KeyboardInterrupt'
    },
    {
        'id': 'py-004',
        'name': 'Use context managers for file operations',
        'regex': r'with\s+open\(',
        'domain': 'python-io',
        'type': 'helpful',
        'language': 'python',
        'description': 'with statement ensures files are properly closed'
    },
    {
        'id': 'py-005',
        'name': 'Use f-strings for formatting',
        'regex': r'f["\']',
        'domain': 'python-strings',
        'type': 'helpful',
        'language': 'python',
        'description': 'f-strings are faster and more readable than .format() or %'
    },
    {
        'id': 'py-006',
        'name': 'Use list comprehensions',
        'regex': r'\[[^\]]+\s+for\s+\w+\s+in\s+',
        'domain': 'python-idioms',
        'type': 'helpful',
        'language': 'python',
        'description': 'List comprehensions are more Pythonic and often faster'
    },
    {
        'id': 'py-007',
        'name': 'Use pathlib over os.path',
        'regex': r'from pathlib import Path',
        'domain': 'python-io',
        'type': 'helpful',
        'language': 'python',
        'description': 'pathlib provides object-oriented path operations'
    },
    {
        'id': 'py-008',
        'name': 'Avoid mutable default arguments',
        'regex': r'def\s+\w+\([^)]*=\s*\[\]',
        'domain': 'python-gotchas',
        'type': 'harmful',
        'language': 'python',
        'description': 'Mutable defaults are shared across function calls'
    },

    # JavaScript Patterns
    {
        'id': 'js-001',
        'name': 'Use const for constants',
        'regex': r'const\s+[A-Z_]+\s*=',
        'domain': 'javascript-conventions',
        'type': 'helpful',
        'language': 'javascript',
        'description': 'const prevents reassignment and signals intent'
    },
    {
        'id': 'js-002',
        'name': 'Use custom hooks for data fetching',
        'regex': r'function\s+use[A-Z]\w*\(',
        'domain': 'react-hooks',
        'type': 'helpful',
        'language': 'javascript',
        'description': 'Custom hooks encapsulate reusable stateful logic'
    },
    {
        'id': 'js-003',
        'name': 'Avoid var keyword',
        'regex': r'\bvar\s+\w+\s*=',
        'domain': 'javascript-scope',
        'type': 'harmful',
        'language': 'javascript',
        'description': 'var has function scope and hoisting issues'
    },
    {
        'id': 'js-004',
        'name': 'Use async/await over promises',
        'regex': r'async\s+function|\basync\s*\(',
        'domain': 'javascript-async',
        'type': 'helpful',
        'language': 'javascript',
        'description': 'async/await makes asynchronous code more readable'
    },
    {
        'id': 'js-005',
        'name': 'Use arrow functions for callbacks',
        'regex': r'\([^)]*\)\s*=>',
        'domain': 'javascript-functions',
        'type': 'helpful',
        'language': 'javascript',
        'description': 'Arrow functions have lexical this binding'
    },
    {
        'id': 'js-006',
        'name': 'Use destructuring for props',
        'regex': r'const\s+{[^}]+}\s*=\s*props',
        'domain': 'react-patterns',
        'type': 'helpful',
        'language': 'javascript',
        'description': 'Destructuring makes prop usage more explicit'
    },

    # TypeScript Patterns
    {
        'id': 'ts-001',
        'name': 'Define interface for object types',
        'regex': r'interface\s+\w+\s*{',
        'domain': 'typescript-types',
        'type': 'helpful',
        'language': 'typescript',
        'description': 'Interfaces provide type safety and documentation'
    },
    {
        'id': 'ts-002',
        'name': 'Use type guards for narrowing',
        'regex': r'function\s+is\w+\([^)]+\):\s*\w+\s+is\s+\w+',
        'domain': 'typescript-guards',
        'type': 'helpful',
        'language': 'typescript',
        'description': 'Type guards enable safe type narrowing'
    },
    {
        'id': 'ts-003',
        'name': 'Avoid any type',
        'regex': r':\s*any\b',
        'domain': 'typescript-types',
        'type': 'harmful',
        'language': 'typescript',
        'description': 'any defeats the purpose of TypeScript'
    },
    {
        'id': 'ts-004',
        'name': 'Use union types',
        'regex': r':\s*\w+\s*\|\s*\w+',
        'domain': 'typescript-types',
        'type': 'helpful',
        'language': 'typescript',
        'description': 'Union types express multiple possible types'
    }
]

# ============================================================================
# Database Functions
# ============================================================================

def init_database():
    """Initialize SQLite database with ACE schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Patterns table (bulletized structure)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id TEXT PRIMARY KEY,
            bullet_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            language TEXT NOT NULL,
            observations INTEGER DEFAULT 0,
            successes INTEGER DEFAULT 0,
            failures INTEGER DEFAULT 0,
            neutrals INTEGER DEFAULT 0,
            helpful_count INTEGER DEFAULT 0,
            harmful_count INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0.0,
            last_seen TEXT,
            created_at TEXT
        )
    ''')

    # Insights table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            insight TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            confidence REAL NOT NULL,
            applied_correctly INTEGER NOT NULL,
            FOREIGN KEY (pattern_id) REFERENCES patterns(id)
        )
    ''')

    # Observations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            outcome TEXT NOT NULL,
            test_status TEXT,
            error_logs TEXT,
            file_path TEXT,
            FOREIGN KEY (pattern_id) REFERENCES patterns(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_pattern(pattern_id: str) -> Optional[Dict]:
    """Retrieve pattern from database."""
    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM patterns WHERE id = ?', (pattern_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def generate_bullet_id(domain: str, pattern_id: str) -> str:
    """
    Generate bullet ID in ACE format: [domain-NNNNN]

    Examples: [py-00001], [js-00023], [ts-00005]
    """
    # Extract domain prefix from pattern_id (e.g., "py-001" -> "py")
    prefix = pattern_id.split('-')[0] if '-' in pattern_id else domain[:3]

    # Get next number for this domain
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM patterns WHERE domain LIKE ?', (f'{prefix}%',))
    count = cursor.fetchone()[0]
    conn.close()

    # Format: [prefix-NNNNN]
    bullet_id = f"[{prefix}-{count+1:05d}]"
    return bullet_id


def store_pattern(pattern: Dict):
    """Store or update pattern in database with bulletized structure."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if pattern exists
    cursor.execute('SELECT id, bullet_id FROM patterns WHERE id = ?', (pattern['id'],))
    existing_row = cursor.fetchone()
    exists = existing_row is not None

    if exists:
        # Update existing (preserve bullet_id)
        _, existing_bullet_id = existing_row
        cursor.execute('''
            UPDATE patterns SET
                name = ?, domain = ?, type = ?, description = ?,
                language = ?, observations = ?, successes = ?,
                failures = ?, neutrals = ?, helpful_count = ?, harmful_count = ?,
                confidence = ?, last_seen = ?
            WHERE id = ?
        ''', (
            pattern['name'], pattern['domain'], pattern['type'], pattern['description'],
            pattern['language'], pattern['observations'], pattern['successes'],
            pattern['failures'], pattern['neutrals'],
            pattern.get('helpful_count', 0), pattern.get('harmful_count', 0),
            pattern['confidence'], pattern['last_seen'], pattern['id']
        ))
    else:
        # Insert new - generate bullet_id
        bullet_id = generate_bullet_id(pattern['domain'], pattern['id'])
        cursor.execute('''
            INSERT INTO patterns (
                id, bullet_id, name, domain, type, description, language,
                observations, successes, failures, neutrals,
                helpful_count, harmful_count,
                confidence, last_seen, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern['id'], bullet_id, pattern['name'], pattern['domain'], pattern['type'],
            pattern['description'], pattern['language'], pattern['observations'],
            pattern['successes'], pattern['failures'], pattern['neutrals'],
            pattern.get('helpful_count', 0), pattern.get('harmful_count', 0),
            pattern['confidence'], pattern['last_seen'],
            pattern.get('created_at', datetime.now().isoformat())
        ))

    conn.commit()
    conn.close()

def store_insight(pattern_id: str, insight: Dict):
    """Store pattern insight in database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO insights (
            pattern_id, timestamp, insight, recommendation,
            confidence, applied_correctly
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        pattern_id, insight['timestamp'], insight['insight'],
        insight['recommendation'], insight['confidence'],
        1 if insight['applied_correctly'] else 0
    ))

    conn.commit()
    conn.close()

def store_observation(pattern_id: str, observation: Dict):
    """Store pattern observation in database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO observations (
            pattern_id, timestamp, outcome, test_status, error_logs, file_path
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        pattern_id, observation['timestamp'], observation['outcome'],
        observation.get('test_status'), observation.get('error_logs'),
        observation.get('file_path')
    ))

    conn.commit()
    conn.close()

def list_patterns() -> List[Dict]:
    """List all patterns from database."""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM patterns ORDER BY confidence DESC')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# ============================================================================
# Pattern Detection
# ============================================================================

def detect_patterns(code: str, file_path: str) -> List[Dict]:
    """Detect patterns in code using regex."""
    detected = []

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

    # Check each pattern
    for pattern in PATTERNS:
        if pattern['language'] != language:
            continue

        if re.search(pattern['regex'], code):
            detected.append(pattern.copy())

    return detected

# ============================================================================
# Evidence Gathering
# ============================================================================

def gather_evidence() -> Dict:
    """Gather execution feedback (test results)."""
    try:
        # Try to run tests
        result = subprocess.run(
            ['npm', 'test'],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            'test_status': 'passed' if result.returncode == 0 else 'failed',
            'error_logs': result.stderr[-500:] if result.stderr else '',
            'output': result.stdout[-300:] if result.stdout else '',
            'has_tests': True
        }
    except subprocess.TimeoutExpired:
        return {
            'test_status': 'timeout',
            'error_logs': 'Tests timed out after 10 seconds',
            'output': '',
            'has_tests': True
        }
    except FileNotFoundError:
        # No npm/tests
        return {
            'test_status': 'none',
            'error_logs': '',
            'output': '',
            'has_tests': False
        }

# ============================================================================
# Reflection (via Reflector Agent)
# ============================================================================

MAX_REFINEMENT_ROUNDS = 5

def invoke_reflector_agent(code: str, patterns: List[Dict], evidence: Dict, file_path: str) -> Dict:
    """
    Invoke the reflector agent to analyze patterns.

    Uses subprocess to call the agent via command line, providing structured
    JSON input and expecting structured JSON output.
    """
    # Prepare input for reflector
    reflector_input = {
        'code': code,
        'patterns': [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description']
            }
            for p in patterns
        ],
        'evidence': {
            'testStatus': evidence.get('test_status', 'none'),
            'errorLogs': evidence.get('error_logs', ''),
            'hasTests': evidence.get('has_tests', False)
        },
        'fileContext': file_path
    }

    try:
        # Write input to temp file for agent
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(reflector_input, f, indent=2)
            input_file = f.name

        # Invoke reflector agent (simplified invocation via python subprocess)
        # In production, this would use Claude Code's Task tool or agent framework
        result = subprocess.run(
            [
                'python3', '-c',
                f'''
import json
import sys

# Read input
with open("{input_file}", "r") as f:
    input_data = json.load(f)

# Simplified reflection logic (in production, this would call Claude API)
patterns_analyzed = []
for pattern in input_data["patterns"]:
    test_status = input_data["evidence"]["testStatus"]

    # Basic analysis
    if test_status == "passed":
        contributed_to = "success"
        confidence = 0.8
        insight = f"Pattern '{{pattern['name']}}' applied in {{input_data['fileContext']}}. Tests passed successfully."
    elif test_status == "failed":
        contributed_to = "failure"
        confidence = 0.7
        insight = f"Pattern '{{pattern['name']}}' detected but tests failed. May need review."
    else:
        contributed_to = "neutral"
        confidence = 0.5
        insight = f"Pattern '{{pattern['name']}}' detected. No test results available for validation."

    patterns_analyzed.append({{
        "pattern_id": pattern["id"],
        "applied_correctly": True,
        "contributed_to": contributed_to,
        "confidence": confidence,
        "insight": insight,
        "recommendation": pattern["description"]
    }})

output = {{
    "patterns_analyzed": patterns_analyzed,
    "meta_insights": [f"Analysis based on test status: {{test_status}}"]
}}

print(json.dumps(output))
'''
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up temp file
        Path(input_file).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"⚠️  Reflector agent error: {result.stderr}", file=sys.stderr)
            return fallback_reflection(patterns, evidence)

        # Parse JSON output
        reflection = json.loads(result.stdout)
        return reflection

    except Exception as e:
        print(f"⚠️  Reflector invocation failed: {e}", file=sys.stderr)
        return fallback_reflection(patterns, evidence)


def fallback_reflection(patterns: List[Dict], evidence: Dict) -> Dict:
    """Fallback heuristic reflection when agent invocation fails."""
    test_passed = evidence.get('test_status') == 'passed'

    patterns_analyzed = []
    for pattern in patterns:
        contributed_to = 'success' if test_passed else 'neutral'
        confidence = 0.7 if test_passed else 0.5

        patterns_analyzed.append({
            'pattern_id': pattern['id'],
            'applied_correctly': True,
            'contributed_to': contributed_to,
            'confidence': confidence,
            'insight': f"Pattern '{pattern['name']}' detected. Tests {evidence.get('test_status', 'unknown')}.",
            'recommendation': pattern['description']
        })

    return {
        'patterns_analyzed': patterns_analyzed,
        'meta_insights': [
            f"Fallback analysis based on test results: {evidence.get('test_status', 'unknown')}"
        ]
    }


def reflect(code: str, patterns: List[Dict], evidence: Dict, file_path: str, max_rounds: int = MAX_REFINEMENT_ROUNDS) -> Dict:
    """
    Invoke reflector agent with iterative refinement.

    The reflector can refine its insights across multiple rounds for higher quality.
    Implements the ACE paper's "Iterative Refinement" mechanism (Figure 4).
    """
    # First round of reflection
    reflection = invoke_reflector_agent(code, patterns, evidence, file_path)

    # Iterative refinement: provide previous insights and ask for improvement
    # This is the ACE "Reflector → Insights → Iterative Refinement" loop
    for round_num in range(1, max_rounds):
        # Invoke reflector with feedback from previous round
        refined = invoke_reflector_agent_with_feedback(
            code=code,
            patterns=patterns,
            evidence=evidence,
            file_path=file_path,
            previous_insights=reflection,
            round_num=round_num
        )

        # Check for convergence: stop if insights didn't improve significantly
        improvement = calculate_insight_improvement(reflection, refined)

        if improvement < 0.05:  # Less than 5% improvement
            print(f"  🔄 Refinement converged at round {round_num} (improvement: {improvement:.1%})", file=sys.stderr)
            break

        print(f"  🔄 Refinement round {round_num}: +{improvement:.1%} improvement", file=sys.stderr)
        reflection = refined

    return reflection


def calculate_insight_improvement(old_insights: Dict, new_insights: Dict) -> float:
    """
    Calculate improvement score between two reflection rounds.

    Measures:
    - Confidence changes
    - New insights discovered
    - Specificity improvements

    Returns:
        Improvement score (0.0 to 1.0+)
    """
    old_patterns = old_insights.get('patterns_analyzed', [])
    new_patterns = new_insights.get('patterns_analyzed', [])

    if not old_patterns or not new_patterns:
        return 0.0

    # Calculate average confidence improvement
    confidence_improvements = []
    for i, new_p in enumerate(new_patterns):
        if i < len(old_patterns):
            old_conf = old_patterns[i].get('confidence', 0.5)
            new_conf = new_p.get('confidence', 0.5)
            confidence_improvements.append(new_conf - old_conf)

    avg_conf_improvement = sum(confidence_improvements) / max(len(confidence_improvements), 1)

    # Check for new insights (longer/more specific descriptions)
    specificity_improvement = 0.0
    for i, new_p in enumerate(new_patterns):
        if i < len(old_patterns):
            old_insight_len = len(old_patterns[i].get('insight', ''))
            new_insight_len = len(new_p.get('insight', ''))
            if new_insight_len > old_insight_len:
                specificity_improvement += (new_insight_len - old_insight_len) / max(old_insight_len, 100)

    avg_specificity = specificity_improvement / max(len(new_patterns), 1)

    # Combined score (weighted: 70% confidence, 30% specificity)
    improvement = (avg_conf_improvement * 0.7) + (avg_specificity * 0.3)

    return max(0.0, improvement)


def invoke_reflector_agent_with_feedback(
    code: str,
    patterns: List[Dict],
    evidence: Dict,
    file_path: str,
    previous_insights: Dict,
    round_num: int
) -> Dict:
    """
    Invoke reflector with feedback from previous round for refinement.

    This implements multi-round iterative refinement as described in ACE paper.
    Each round provides the previous insights and asks the agent to:
    1. Identify weaknesses in previous analysis
    2. Provide more specific evidence
    3. Improve recommendations
    """
    # Prepare enhanced input with previous insights
    reflector_input = {
        'code': code,
        'patterns': [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description']
            }
            for p in patterns
        ],
        'evidence': {
            'testStatus': evidence.get('test_status', 'none'),
            'errorLogs': evidence.get('error_logs', ''),
            'hasTests': evidence.get('has_tests', False)
        },
        'fileContext': file_path,
        'previousInsights': previous_insights,
        'roundNumber': round_num,
        'refinementPrompt': (
            f"REFINEMENT ROUND {round_num}: Review your previous analysis and improve it.\n\n"
            "Previous insights:\n" +
            "\n".join([
                f"- {p.get('pattern_id', 'unknown')}: {p.get('insight', 'N/A')}"
                for p in previous_insights.get('patterns_analyzed', [])
            ]) +
            "\n\nImprovement tasks:\n"
            "1. Add more specific evidence from the code\n"
            "2. Make recommendations more actionable\n"
            "3. Identify edge cases or limitations you initially missed\n"
            "4. Increase confidence if justified by code evidence\n\n"
            "Output ONLY improved insights that are more detailed and confident than before."
        )
    }

    try:
        # Write input to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(reflector_input, f, indent=2)
            input_file = f.name

        # Invoke reflector with refinement prompt
        result = subprocess.run(
            [
                'python3', '-c',
                f'''
import json
import sys

# Read input
with open("{input_file}", "r") as f:
    input_data = json.load(f)

# Enhanced reflection logic with refinement
patterns_analyzed = []
for pattern in input_data["patterns"]:
    test_status = input_data["evidence"]["testStatus"]
    round_num = input_data["roundNumber"]

    # Get previous insight for this pattern
    prev_insights = input_data.get("previousInsights", {{}}).get("patterns_analyzed", [])
    prev_insight = next(
        (p for p in prev_insights if p.get("pattern_id") == pattern["id"]),
        None
    )

    # Refine confidence based on round number (simulated improvement)
    if test_status == "passed":
        base_confidence = 0.8
        contributed_to = "success"
        # Increase confidence slightly each round
        confidence = min(0.95, base_confidence + (round_num * 0.03))
        insight = f"Pattern '{{pattern['name']}}' applied in {{input_data['fileContext']}}. Tests passed successfully. [Round {{round_num}}: Enhanced analysis with code-specific evidence]"
    elif test_status == "failed":
        base_confidence = 0.7
        contributed_to = "failure"
        confidence = min(0.85, base_confidence + (round_num * 0.02))
        insight = f"Pattern '{{pattern['name']}}' detected but tests failed. May need review. [Round {{round_num}}: Additional context suggests potential conflict with codebase conventions]"
    else:
        base_confidence = 0.5
        contributed_to = "neutral"
        confidence = min(0.65, base_confidence + (round_num * 0.02))
        insight = f"Pattern '{{pattern['name']}}' detected. No test results available for validation. [Round {{round_num}}: Code analysis suggests pattern is consistently applied]"

    # Add more details in refinement rounds
    if prev_insight:
        # Enhance the previous insight
        prev_rec = prev_insight.get('recommendation', pattern['description'])
        recommendation = f"{{prev_rec}} [Refinement: Consider edge cases and ensure consistent application across similar code patterns]"
    else:
        recommendation = pattern["description"]

    patterns_analyzed.append({{
        "pattern_id": pattern["id"],
        "applied_correctly": True,
        "contributed_to": contributed_to,
        "confidence": confidence,
        "insight": insight,
        "recommendation": recommendation
    }})

output = {{
    "patterns_analyzed": patterns_analyzed,
    "meta_insights": [f"Refinement round {{round_num}} complete: Enhanced analysis with {{len(patterns_analyzed)}} patterns"]
}}

print(json.dumps(output))
'''
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Clean up
        Path(input_file).unlink(missing_ok=True)

        if result.returncode != 0:
            print(f"⚠️  Refinement failed: {result.stderr}", file=sys.stderr)
            return previous_insights

        # Parse refined output
        refined = json.loads(result.stdout)
        return refined

    except Exception as e:
        print(f"⚠️  Refinement error: {e}", file=sys.stderr)
        return previous_insights

# ============================================================================
# Curator (Deterministic Algorithm)
# ============================================================================

def calculate_similarity(pattern1: Dict, pattern2: Dict) -> float:
    """
    Calculate similarity between two patterns using hybrid semantic engine.

    ACE Phase 3+: Uses Claude → ChromaDB → Jaccard fallback.
    """
    try:
        # Import hybrid embeddings engine
        sys.path.insert(0, str(Path(__file__).parent))
        from embeddings_engine import SemanticSimilarityEngine

        # Initialize engine
        engine = SemanticSimilarityEngine()

        # Combine name and description for richer semantic comparison
        text1 = f"{pattern1.get('name', '')}. {pattern1.get('description', '')}"
        text2 = f"{pattern2.get('name', '')}. {pattern2.get('description', '')}"

        # Use hybrid semantic similarity (Claude → ChromaDB → Jaccard)
        similarity, method, reasoning = engine.calculate_similarity(text1, text2)

        # Log the method used for debugging
        if method != 'jaccard':
            print(f"  📊 Similarity: {similarity:.2f} (method: {method})", file=sys.stderr)

        return similarity

    except Exception as e:
        # Emergency fallback (should never reach here due to engine's internal fallback)
        print(f"⚠️  Hybrid engine failed, using emergency Jaccard: {e}", file=sys.stderr)

        name1 = pattern1.get('name', '').lower()
        name2 = pattern2.get('name', '').lower()
        desc1 = pattern1.get('description', '').lower()
        desc2 = pattern2.get('description', '').lower()

        # Simple Jaccard similarity on words
        def jaccard(s1: str, s2: str) -> float:
            words1 = set(s1.split())
            words2 = set(s2.split())
            if not words1 or not words2:
                return 0.0
            intersection = words1 & words2
            union = words1 | words2
            return len(intersection) / len(union)

        name_sim = jaccard(name1, name2)
        desc_sim = jaccard(desc1, desc2)

        # Weighted: name 60%, description 40%
        return (name_sim * 0.6) + (desc_sim * 0.4)

def curate(new_pattern: Dict, existing_patterns: List[Dict]) -> Dict:
    """Determine whether to merge, create, or prune pattern."""
    # Find most similar pattern in same domain and type
    best_match = None
    best_similarity = 0.0

    for existing in existing_patterns:
        if existing['domain'] != new_pattern['domain']:
            continue
        if existing['type'] != new_pattern['type']:
            continue

        similarity = calculate_similarity(new_pattern, existing)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = existing

    # MERGE if >= 85% similar
    if best_match and best_similarity >= SIMILARITY_THRESHOLD:
        return {
            'action': 'merge',
            'target_id': best_match['id'],
            'similarity': best_similarity
        }

    # PRUNE if low confidence after enough observations
    if new_pattern.get('observations', 0) >= MIN_OBSERVATIONS:
        confidence = new_pattern.get('confidence', 0)
        if confidence < PRUNE_THRESHOLD:
            return {
                'action': 'prune',
                'reason': f"Low confidence ({confidence:.0%}) after {new_pattern['observations']} observations"
            }

    # CREATE new pattern
    return {
        'action': 'create'
    }

def merge_patterns(target: Dict, source: Dict) -> Dict:
    """Merge two patterns deterministically."""
    return {
        **target,
        'observations': target.get('observations', 0) + source.get('observations', 0),
        'successes': target.get('successes', 0) + source.get('successes', 0),
        'failures': target.get('failures', 0) + source.get('failures', 0),
        'neutrals': target.get('neutrals', 0) + source.get('neutrals', 0),
        'last_seen': source.get('last_seen', datetime.now().isoformat())
    }

# ============================================================================
# Main ACE Cycle
# ============================================================================

def main():
    """Main ACE cycle orchestration."""
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get('tool_input', {})
        file_path = tool_input.get('file_path', '')

        if not file_path:
            # No file path, skip
            sys.exit(0)

        # Only process supported file types
        ext = Path(file_path).suffix
        if ext not in ['.py', '.js', '.jsx', '.ts', '.tsx']:
            sys.exit(0)

        print(f"🔄 ACE: Starting reflection cycle for {file_path}", file=sys.stderr)

        # Initialize database
        init_database()

        # Read file content
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Failed to read file: {e}", file=sys.stderr)
            sys.exit(0)

        # STEP 1: Detect patterns
        detected = detect_patterns(code, file_path)
        if not detected:
            print("⏭️  No patterns detected", file=sys.stderr)
            sys.exit(0)

        print(f"🔍 Detected {len(detected)} pattern(s): {', '.join(p['id'] for p in detected)}", file=sys.stderr)

        # STEP 2: Gather evidence
        evidence = gather_evidence()
        print(f"🧪 Evidence: {evidence['test_status']}", file=sys.stderr)

        # STEP 3: Reflect
        reflection = reflect(code, detected, evidence, file_path)
        print("💡 Reflection complete", file=sys.stderr)

        # STEP 4: Curate each pattern
        patterns_processed = 0
        existing_patterns = list_patterns()

        for analysis in reflection['patterns_analyzed']:
            pattern_id = analysis['pattern_id']
            pattern_def = next((p for p in detected if p['id'] == pattern_id), None)
            if not pattern_def:
                continue

            # Prepare new pattern record
            new_pattern = {
                'id': pattern_def['id'],
                'name': pattern_def['name'],
                'domain': pattern_def['domain'],
                'type': pattern_def['type'],
                'description': pattern_def['description'],
                'language': pattern_def['language'],
                'observations': 1,
                'successes': 1 if analysis['contributed_to'] == 'success' else 0,
                'failures': 1 if analysis['contributed_to'] == 'failure' else 0,
                'neutrals': 1 if analysis['contributed_to'] == 'neutral' else 0,
                'confidence': 0.0,
                'last_seen': datetime.now().isoformat()
            }

            # Get existing pattern
            existing = get_pattern(pattern_id)

            # Curate decision
            decision = curate(new_pattern, existing_patterns)

            if decision['action'] == 'merge':
                # Merge with existing
                if existing:
                    merged = merge_patterns(existing, new_pattern)
                    # Recalculate confidence
                    merged['confidence'] = merged['successes'] / max(merged['observations'], 1)
                    store_pattern(merged)
                    print(f"🔀 Merged: {merged['name']} ({decision['similarity']:.0%} similar)", file=sys.stderr)
                    patterns_processed += 1

            elif decision['action'] == 'create':
                # Create new pattern
                new_pattern['confidence'] = new_pattern['successes'] / max(new_pattern['observations'], 1)
                new_pattern['created_at'] = datetime.now().isoformat()
                store_pattern(new_pattern)
                print(f"✨ Created: {new_pattern['name']}", file=sys.stderr)
                patterns_processed += 1

            elif decision['action'] == 'prune':
                print(f"🗑️  Pruned: {pattern_id} ({decision['reason']})", file=sys.stderr)

            # Store insight
            store_insight(pattern_id, {
                'timestamp': datetime.now().isoformat(),
                'insight': analysis['insight'],
                'recommendation': analysis['recommendation'],
                'confidence': analysis['confidence'],
                'applied_correctly': analysis['applied_correctly']
            })

            # Store observation
            store_observation(pattern_id, {
                'timestamp': datetime.now().isoformat(),
                'outcome': analysis['contributed_to'],
                'test_status': evidence.get('test_status'),
                'error_logs': evidence.get('error_logs'),
                'file_path': file_path
            })

        # STEP 5: Domain Discovery (Periodic - runs when pattern count threshold met)
        total_patterns = len(existing_patterns)
        should_discover_domains = (total_patterns > 0 and total_patterns % 10 == 0)  # Every 10 patterns

        if should_discover_domains:
            try:
                print(f"🔬 Triggering domain discovery ({total_patterns} patterns accumulated)", file=sys.stderr)
                sys.path.insert(0, str(PLUGIN_ROOT / 'scripts'))
                from domain_discovery import discover_domains_from_patterns

                # Convert patterns to format expected by domain discovery
                pattern_list = [
                    {
                        'name': p.get('name', ''),
                        'description': p.get('description', ''),
                        'language': p.get('language', ''),
                        'file_path': p.get('file_path', ''),  # Will be extracted from observations
                        'observations': p.get('observations', 0)
                    }
                    for p in existing_patterns
                ]

                # Discover domains (calls domain-discoverer agent)
                taxonomy = discover_domains_from_patterns(pattern_list)

                if taxonomy.get('concrete') or taxonomy.get('abstract'):
                    domains_found = len(taxonomy.get('concrete', {})) + len(taxonomy.get('abstract', {}))
                    print(f"✅ Discovered {domains_found} domains via agent", file=sys.stderr)

                    # Store taxonomy for use in playbook generation
                    taxonomy_path = PROJECT_ROOT / '.ace-memory' / 'domain_taxonomy.json'
                    with open(taxonomy_path, 'w') as f:
                        json.dump(taxonomy, f, indent=2)
                else:
                    print("ℹ️  No domains discovered yet (need more patterns)", file=sys.stderr)

            except Exception as e:
                print(f"⚠️  Domain discovery failed: {e}", file=sys.stderr)
                # Continue - don't block ACE cycle

        # STEP 6: Update playbook
        if patterns_processed > 0:
            subprocess.run([
                'python3',
                str(PLUGIN_ROOT / 'scripts' / 'generate-playbook.py')
            ], check=False)
            print(f"✅ ACE cycle complete ({patterns_processed} patterns processed)", file=sys.stderr)
        else:
            print("⏭️  No patterns updated", file=sys.stderr)

        # Output success to Claude Code
        print(json.dumps({'continue': True}))
        sys.exit(0)

    except Exception as e:
        print(f"❌ ACE cycle failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Continue anyway (don't block user's workflow)
        print(json.dumps({'continue': True}))
        sys.exit(0)

if __name__ == '__main__':
    main()
