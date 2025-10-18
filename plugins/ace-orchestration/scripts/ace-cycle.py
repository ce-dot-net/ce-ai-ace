#!/usr/bin/env python3
"""
ACE Cycle - Main orchestration script (TRUE ACE Research Paper Architecture)

Orchestrates the complete ACE cycle per the research paper:
1. Evidence Gathering (test results, execution feedback)
2. Pattern Discovery via Reflector Agent (LLM-based code analysis - NO pre-detection!)
3. Curation (deterministic algorithm: merge at 85% similarity, prune at 30% confidence)
4. Domain Discovery (periodic, agent-based taxonomy learning)
5. Playbook Update (CLAUDE.md generation with delta updates)

CRITICAL ARCHITECTURE CHANGE (v2.3.9):
- Removed hardcoded pattern detection (semantic_pattern_extractor.py)
- Reflector agent NOW DISCOVERS patterns by analyzing raw code
- This matches the TRUE ACE research paper architecture (Section 3, Figure 4)
- Generator → Trajectory → Reflector (discovers patterns) → Curator (merges/prunes)

ACE Phase 3+ Enhancements:
- Agent-based pattern discovery (not hardcoded keyword matching!)
- Semantic embeddings for pattern similarity (Claude → ChromaDB → Jaccard fallback)
- Delta-based CLAUDE.md updates (prevents context collapse)
- Multi-epoch offline training mode
- Bottom-up domain taxonomy discovery

Called by PostToolUse hook after Edit/Write operations.
"""

import json
import sys
import os
import re
import sqlite3
import subprocess
import fcntl
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
# Pattern Discovery - TRUE ACE Architecture (v2.3.9+)
# ============================================================================

# PATTERNS array REMOVED - no hardcoded pattern detection!
#
# ACE Research Paper Architecture (Section 3, Figure 4):
# 1. Generator produces code trajectories (raw code + execution)
# 2. Reflector agent DISCOVERS patterns by analyzing raw code via LLM
# 3. Curator merges/prunes discovered patterns deterministically
#
# This is the CORRECT implementation per the research paper.
# Previous semantic_pattern_extractor.py was wrong - it used hardcoded
# keywords ("stripe", "auth", "payment") which don't match this codebase.
#
# Now: Reflector agent reads code and discovers what patterns exist:
# - "subprocess module usage" - by seeing `import subprocess`
# - "pathlib operations" - by seeing `from pathlib import Path`
# - "SQLite database queries" - by seeing `sqlite3.connect()`
# - "JSON serialization" - by seeing `json.dumps()`
# etc.
#
# The agent outputs structured pattern definitions with insights and recommendations.

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

    Deterministic generation based on pattern_id hash to avoid collisions
    when multiple patterns are stored in same run (ACE paper: batch size of 1).
    """
    import hashlib

    # Extract domain prefix from pattern_id (e.g., "py-001" -> "py")
    prefix = pattern_id.split('-')[0] if '-' in pattern_id else domain[:3]

    # Generate deterministic number from pattern_id hash
    # This ensures each unique pattern_id gets a unique bullet_id
    hash_obj = hashlib.md5(pattern_id.encode())
    hash_int = int(hash_obj.hexdigest()[:8], 16)  # Use first 8 hex chars
    number = hash_int % 99999  # Keep it within 5 digits (00000-99998)

    # Format: [prefix-NNNNN]
    bullet_id = f"[{prefix}-{number:05d}]"
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
# Pattern Discovery (via Reflector Agent)
# ============================================================================
#
# ACE Research Paper Architecture:
# - Generator produces code trajectories
# - Reflector DISCOVERS patterns by analyzing raw code + execution feedback
# - Curator merges/prunes discovered patterns
#
# NO pre-detection step! Reflector does dynamic discovery via LLM analysis.

def _infer_language_from_file(file_path: str) -> str:
    """Infer programming language from file extension."""
    ext = Path(file_path).suffix
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.md': 'markdown',
        '.json': 'json'
    }
    return lang_map.get(ext, 'unknown')

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

def invoke_reflector_agent(code: str, evidence: Dict, file_path: str) -> Dict:
    """
    Invoke the reflector agent to DISCOVER patterns from raw code.

    TRUE ACE paper architecture: Reflector analyzes raw code trajectories
    and DISCOVERS what patterns exist - no pre-detection!

    This function coordinates with Claude to invoke the reflector agent.
    The workflow:
    1. Check if agent response already exists (cached from previous run)
    2. If not, output request to stderr for Claude to process
    3. Return cached patterns if available, empty list if not yet processed

    Args:
        code: Raw source code
        evidence: Execution feedback (test results, errors)
        file_path: File being analyzed

    Returns:
        Dict with discovered_patterns and insights
    """
    # Create response file path
    reflections_dir = PROJECT_ROOT / '.ace-memory' / 'reflections'
    reflections_dir.mkdir(parents=True, exist_ok=True)

    response_file = reflections_dir / f'{Path(file_path).name}.json'

    # Check if response already exists (cached from previous agent run)
    if response_file.exists():
        try:
            with open(response_file, 'r') as f:
                agent_output = json.load(f)
            return agent_output
        except Exception as e:
            print(f"⚠️  Error reading cached reflection: {e}", file=sys.stderr)

    # No response yet - prepare input for reflector (NO pre-detected patterns!)
    reflector_input = {
        'code': code[:2000],  # Include more code for pattern discovery
        'full_code_length': len(code),
        'evidence': {
            'testStatus': evidence.get('test_status', 'none'),
            'errorLogs': evidence.get('error_logs', '')[:300] if evidence.get('error_logs') else '',
            'hasTests': evidence.get('has_tests', False),
            'output': evidence.get('output', '')[:200] if evidence.get('output') else ''
        },
        'fileContext': file_path,
        'language': _infer_language_from_file(file_path)
    }

    try:
        # Output request to stderr for Claude to invoke agent via Task tool
        print(f"""
🔬 ACE Pattern Discovery Request

Analyzing {file_path} ({len(code)} chars). Please invoke the reflector agent to DISCOVER patterns.

<pattern_discovery_request>
{json.dumps(reflector_input, indent=2)}
</pattern_discovery_request>

Use the Task tool to invoke ace-orchestration:reflector agent with the data above.

CRITICAL: The agent must DISCOVER patterns by analyzing the raw code, not match predefined patterns!

The agent should:
1. Read and analyze the code
2. Identify what coding patterns are present (e.g., "subprocess usage", "SQLite queries", "pathlib operations", "JSON handling", "uvx commands", "ChromaDB calls")
3. For each discovered pattern, determine:
   - Pattern name and description
   - Whether it contributed to success, failure, or neutral outcome (based on test results)
   - Confidence level (0.0-1.0)
   - Specific insights with evidence from the code
   - Recommendations for when to use/avoid

Expected output format (JSON):
{{
  "discovered_patterns": [
    {{
      "id": "discovered-subprocess-usage",
      "name": "subprocess module usage",
      "description": "Uses Python subprocess module for running external commands",
      "domain": "python-stdlib",
      "type": "helpful",
      "applied_correctly": true,
      "contributed_to": "success",
      "confidence": 0.9,
      "insight": "Code uses subprocess.run() with capture_output=True for safe command execution",
      "recommendation": "Continue using subprocess.run() with explicit parameters for reliability"
    }}
  ],
  "meta_insights": ["Discovered 5 patterns via code analysis"]
}}

Store the analysis results in: {response_file}
""", file=sys.stderr)

        # No response yet - return empty (will be filled on subsequent run after Claude processes)
        return {
            'discovered_patterns': [],
            'meta_insights': ['Waiting for agent-based pattern discovery']
        }

    except Exception as e:
        print(f"⚠️  Reflector request failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # No fallback - ACE paper acknowledges this as a limitation
        return {
            'discovered_patterns': [],
            'meta_insights': ['Pattern discovery failed - no analysis available']
        }


def reflect(code: str, evidence: Dict, file_path: str, max_rounds: int = MAX_REFINEMENT_ROUNDS) -> Dict:
    """
    Invoke reflector agent with iterative refinement.

    TRUE ACE architecture: Pass raw code to Reflector for pattern DISCOVERY.
    No pre-detected patterns - the agent discovers what patterns exist!

    The reflector can refine its insights across multiple rounds for higher quality.
    Implements the ACE paper's "Iterative Refinement" mechanism (Figure 4).

    Args:
        code: Raw source code
        evidence: Execution feedback (test results, errors)
        file_path: File being analyzed
        max_rounds: Maximum refinement rounds

    Returns:
        Dict with discovered_patterns and insights
    """
    # First round of reflection - DISCOVER patterns from raw code
    reflection = invoke_reflector_agent(code, evidence, file_path)

    # Iterative refinement: provide previous insights and ask for improvement
    # This is the ACE "Reflector → Insights → Iterative Refinement" loop
    for round_num in range(1, max_rounds):
        # Invoke reflector with feedback from previous round
        refined = invoke_reflector_agent_with_feedback(
            code=code,
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
    # Changed from 'patterns_analyzed' to 'discovered_patterns' per new architecture
    old_patterns = old_insights.get('discovered_patterns', [])
    new_patterns = new_insights.get('discovered_patterns', [])

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
    evidence: Dict,
    file_path: str,
    previous_insights: Dict,
    round_num: int
) -> Dict:
    """
    Invoke reflector with feedback from previous round for refinement.

    TRUE ACE architecture: No pre-detected patterns! Agent refines its own discoveries.

    This implements multi-round iterative refinement as described in ACE paper
    (max 5 refinement rounds per research paper Section 4).

    This function coordinates with Claude to invoke the reflector-prompt agent.
    The workflow:
    1. Check if agent response already exists (cached from previous run)
    2. If not, output request to stderr for Claude to process
    3. Return cached refined patterns if available, previous insights if not yet processed

    Each round provides the previous insights and asks the agent to:
    1. Identify weaknesses in previous analysis
    2. Provide more specific evidence
    3. Improve recommendations
    4. Discover additional patterns that were initially missed
    """
    # Create response file path for this refinement round
    reflections_dir = PROJECT_ROOT / '.ace-memory' / 'reflections'
    reflections_dir.mkdir(parents=True, exist_ok=True)

    response_file = reflections_dir / f'{Path(file_path).name}_round{round_num}.json'

    # Check if response already exists (cached from previous agent run)
    if response_file.exists():
        try:
            with open(response_file, 'r') as f:
                agent_output = json.load(f)
            return agent_output
        except Exception as e:
            print(f"⚠️  Error reading cached refinement: {e}", file=sys.stderr)

    # No response yet - prepare enhanced input with previous insights (NO pre-detected patterns!)
    reflector_input = {
        'code': code[:1000],  # Truncate code for display
        'evidence': {
            'testStatus': evidence.get('test_status', 'none'),
            'errorLogs': evidence.get('error_logs', '')[:200] if evidence.get('error_logs') else '',
            'hasTests': evidence.get('has_tests', False)
        },
        'fileContext': file_path,
        'previousInsights': {
            'discovered_patterns': [
                {
                    'id': p.get('id'),
                    'name': p.get('name'),
                    'insight': p.get('insight'),
                    'recommendation': p.get('recommendation'),
                    'confidence': p.get('confidence')
                }
                for p in previous_insights.get('discovered_patterns', [])
            ]
        },
        'roundNumber': round_num,
        'refinementPrompt': (
            f"REFINEMENT ROUND {round_num}: Review your previous analysis and improve it.\n\n"
            "Previously discovered patterns:\n" +
            "\n".join([
                f"- {p.get('id', 'unknown')}: {p.get('insight', 'N/A')}"
                for p in previous_insights.get('discovered_patterns', [])
            ]) +
            "\n\nImprovement tasks:\n"
            "1. Add more specific evidence from the code\n"
            "2. Make recommendations more actionable\n"
            "3. Identify edge cases or limitations you initially missed\n"
            "4. Discover additional patterns you might have missed\n"
            "5. Increase confidence if justified by code evidence\n\n"
            "Output improved insights that are more detailed and confident than before."
        )
    }

    try:
        # Output request to stderr for Claude to invoke agent via Task tool
        print(f"""
🔬 ACE Reflector Refinement Request (Round {round_num})

Refinement round {round_num} for {file_path}. Please invoke the reflector agent to refine previous insights.

<reflector_refinement_request>
{json.dumps(reflector_input, indent=2)}
</reflector_refinement_request>

Use the Task tool to invoke ace-orchestration:reflector-prompt agent with the refinement data above.
The agent will refine the previous insights by:
1. Adding more specific evidence from the code
2. Making recommendations more actionable
3. Identifying edge cases or limitations initially missed
4. Increasing confidence if justified by code evidence

Expected output format (JSON):
- discovered_patterns: List of REFINED discovered patterns (should be more detailed than previous round)
  - id: Pattern identifier (e.g., "discovered-subprocess-usage")
  - name: Pattern name
  - description: Pattern description
  - domain: Domain (e.g., "python-stdlib", "api-usage")
  - type: "helpful"/"harmful"/"neutral"
  - applied_correctly: true/false
  - contributed_to: "success"/"failure"/"neutral"
  - confidence: 0.0-1.0 (may increase if more evidence found)
  - insight: MORE SPECIFIC observation with concrete evidence from code
  - recommendation: MORE ACTIONABLE guidance with examples

Store the refined analysis results in: {response_file}
""", file=sys.stderr)

        # No response yet - return previous insights unchanged (will be refined on subsequent run after Claude processes)
        return previous_insights

    except Exception as e:
        print(f"⚠️  Reflector refinement request failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # No fallback - return previous insights unchanged
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
    # CONCURRENCY LOCK: Prevent parallel PostToolUse hook executions
    # This fixes the 400 API error caused by simultaneous hook runs
    lock_file = PROJECT_ROOT / '.ace-memory' / '.ace-cycle.lock'
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to acquire lock (non-blocking)
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        # Another ace-cycle.py is running, skip this one
        print("⏭️  ACE cycle already running, skipping duplicate", file=sys.stderr)
        print(json.dumps({'continue': True}))
        sys.exit(0)

    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get('tool_input', {})
        file_path = tool_input.get('file_path', '')

        if not file_path:
            # No file path, skip
            print(json.dumps({'continue': True}))
            sys.exit(0)

        # Only process supported file types
        ext = Path(file_path).suffix
        if ext not in ['.py', '.js', '.jsx', '.ts', '.tsx']:
            print(json.dumps({'continue': True}))
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

        # STEP 1: Gather evidence
        evidence = gather_evidence()
        print(f"🧪 Evidence: {evidence['test_status']}", file=sys.stderr)

        # STEP 2: Reflect - DISCOVER patterns from raw code (TRUE ACE architecture!)
        reflection = reflect(code, evidence, file_path)
        print("💡 Pattern discovery complete", file=sys.stderr)

        # Check if patterns were discovered
        discovered = reflection.get('discovered_patterns', [])
        if not discovered:
            print("⏭️  No patterns discovered (graceful degradation - Curator can still process existing patterns)", file=sys.stderr)
            # Continue to Curator even without new patterns (ACE paper: graceful degradation)
            # Curator can still merge/prune existing patterns based on feedback
            # This respects ACE paper's acknowledged limitation (Appendix B)
        else:
            print(f"🔍 Discovered {len(discovered)} pattern(s): {', '.join(p['id'] for p in discovered)}", file=sys.stderr)

        # STEP 3: Curate each discovered pattern
        patterns_processed = 0
        existing_patterns = list_patterns()

        for pattern_def in discovered:
            # Pattern definition already contains all fields from agent discovery
            pattern_id = pattern_def.get('id')
            if not pattern_id:
                continue

            # Prepare new pattern record from discovered pattern
            new_pattern = {
                'id': pattern_def.get('id'),
                'name': pattern_def.get('name', 'Unknown pattern'),
                'domain': pattern_def.get('domain', 'general'),
                'type': pattern_def.get('type', 'neutral'),
                'description': pattern_def.get('description', ''),
                'language': pattern_def.get('language', _infer_language_from_file(file_path)),
                'observations': 1,
                'successes': 1 if pattern_def.get('contributed_to') == 'success' else 0,
                'failures': 1 if pattern_def.get('contributed_to') == 'failure' else 0,
                'neutrals': 1 if pattern_def.get('contributed_to') == 'neutral' else 0,
                'confidence': pattern_def.get('confidence', 0.0),
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
                    # Recalculate confidence with feedback (TRUE ACE architecture!)
                    # Formula: (successes + helpful) / (observations + helpful + harmful)
                    helpful = merged.get('helpful_count', 0)
                    harmful = merged.get('harmful_count', 0)
                    numerator = merged['successes'] + helpful
                    denominator = merged['observations'] + helpful + harmful
                    merged['confidence'] = numerator / max(denominator, 1)

                    store_pattern(merged)
                    print(f"🔀 Merged: {merged['name']} ({decision['similarity']:.0%} similar)", file=sys.stderr)
                    patterns_processed += 1

            elif decision['action'] == 'create':
                # Create new pattern
                # Initial confidence (no feedback yet)
                new_pattern['confidence'] = new_pattern['successes'] / max(new_pattern['observations'], 1)
                new_pattern['created_at'] = datetime.now().isoformat()
                store_pattern(new_pattern)
                print(f"✨ Created: {new_pattern['name']}", file=sys.stderr)
                patterns_processed += 1

            elif decision['action'] == 'prune':
                print(f"🗑️  Pruned: {pattern_id} ({decision['reason']})", file=sys.stderr)

            # Store insight (from discovered pattern)
            store_insight(pattern_id, {
                'timestamp': datetime.now().isoformat(),
                'insight': pattern_def.get('insight', ''),
                'recommendation': pattern_def.get('recommendation', ''),
                'confidence': pattern_def.get('confidence', 0.0),
                'applied_correctly': pattern_def.get('applied_correctly', True)
            })

            # Store observation (from discovered pattern)
            store_observation(pattern_id, {
                'timestamp': datetime.now().isoformat(),
                'outcome': pattern_def.get('contributed_to', 'neutral'),
                'test_status': evidence.get('test_status'),
                'error_logs': evidence.get('error_logs'),
                'file_path': file_path
            })

        # STEP 4: Domain Discovery (Periodic - runs when pattern count threshold met)
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

        # STEP 5: Update playbook
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

    except Exception as e:
        print(f"❌ ACE cycle failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Continue anyway (don't block user's workflow)
        print(json.dumps({'continue': True}))

    finally:
        # Release lock
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            lock_file.unlink(missing_ok=True)
        except:
            pass  # Lock cleanup failure is non-critical

    sys.exit(0)

if __name__ == '__main__':
    main()
