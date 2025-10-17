#!/usr/bin/env python3
"""
Offline Training Mode - ACE Research Paper Feature

Implements multi-epoch offline training as described in Section 4.1:
"ACE optimizes contexts both offline (e.g., system prompt optimization)
and online (e.g., test-time memory adaptation)"

Multi-epoch improves patterns by revisiting training data 5 times.
Adds +2.6% improvement according to Table 3 in the paper.
"""

import sys
import json
import sqlite3
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Import epoch-manager.py (with hyphen in filename)
import importlib.util
_spec = importlib.util.spec_from_file_location("epoch_manager", Path(__file__).parent / "epoch-manager.py")
_epoch_manager = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_epoch_manager)

start_epoch = _epoch_manager.start_epoch
complete_epoch = _epoch_manager.complete_epoch
track_pattern_evolution = _epoch_manager.track_pattern_evolution
cache_training_data = _epoch_manager.cache_training_data
get_training_data_for_epoch = _epoch_manager.get_training_data_for_epoch
MAX_EPOCHS = _epoch_manager.MAX_EPOCHS

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'
PLUGIN_ROOT = Path(__file__).parent.parent

def scan_codebase_for_training(source: str = 'all') -> List[Dict]:
    """
    Scan codebase for training examples.

    Args:
        source: 'all', 'git-history', 'test-files', 'specs-history', or path

    Returns:
        List of training examples
    """
    training_data = []

    if source == 'all' or source == 'test-files':
        # Scan test files
        test_patterns = ['**/*test*.py', '**/*test*.js', '**/*test*.ts', '**/*.spec.js', '**/*.spec.ts']
        for pattern in test_patterns:
            for file_path in PROJECT_ROOT.glob(pattern):
                if file_path.is_file() and file_path.stat().st_size < 100000:  # Skip huge files
                    try:
                        code = file_path.read_text()
                        training_data.append({
                            'file_path': str(file_path.relative_to(PROJECT_ROOT)),
                            'code': code,
                            'source': 'test-files'
                        })
                    except:
                        pass

    if source == 'all' or source == 'git-history':
        # Scan recent git commits
        try:
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H', '--max-count=50'],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT
            )
            commits = result.stdout.strip().split('\n')

            for commit in commits[:20]:  # Last 20 commits
                # Get changed files
                result = subprocess.run(
                    ['git', 'show', '--name-only', '--pretty=format:', commit],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )

                files = [f for f in result.stdout.strip().split('\n') if f]
                for file_rel in files[:5]:  # Max 5 files per commit
                    if any(file_rel.endswith(ext) for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']):
                        try:
                            result = subprocess.run(
                                ['git', 'show', f'{commit}:{file_rel}'],
                                capture_output=True,
                                text=True,
                                cwd=PROJECT_ROOT
                            )
                            code = result.stdout
                            if code and len(code) < 50000:
                                training_data.append({
                                    'file_path': file_rel,
                                    'code': code,
                                    'source': f'git-{commit[:7]}'
                                })
                        except:
                            pass
        except:
            print("⚠️  Git history scan failed", file=sys.stderr)

    if source == 'all' or source == 'specs-history':
        # Scan git history of specs/ folder for pattern evolution
        # ACE learns from ACE! (meta-learning)
        specs_dir = PROJECT_ROOT / 'specs'
        if specs_dir.exists():
            try:
                # Get commits that modified specs/
                result = subprocess.run(
                    ['git', 'log', '--pretty=format:%H', '--', 'specs/'],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT
                )
                commits = result.stdout.strip().split('\n')

                for commit in commits[:30]:  # Last 30 spec changes
                    # Get changed spec files
                    result = subprocess.run(
                        ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit],
                        capture_output=True,
                        text=True,
                        cwd=PROJECT_ROOT
                    )

                    files = [f for f in result.stdout.strip().split('\n') if f.startswith('specs/')]
                    for file_rel in files[:3]:  # Max 3 files per commit
                        if file_rel.endswith('.md'):
                            try:
                                result = subprocess.run(
                                    ['git', 'show', f'{commit}:{file_rel}'],
                                    capture_output=True,
                                    text=True,
                                    cwd=PROJECT_ROOT
                                )
                                content = result.stdout
                                if content and len(content) < 50000:
                                    training_data.append({
                                        'file_path': file_rel,
                                        'code': content,
                                        'source': f'specs-{commit[:7]}'
                                    })
                            except:
                                pass
            except:
                print("⚠️  specs/ history scan failed", file=sys.stderr)

    return training_data

def batch_reflect_via_agent(code: str, file_path: str, language: str) -> List[Dict]:
    """
    Pattern discovery via agent invocation (interactive mode).

    TRUE ACE Architecture: Patterns are DISCOVERED by agents analyzing code,
    NOT matched against hardcoded keywords.

    This function outputs a request for Claude to invoke the domain-discoverer agent.
    The agent will analyze the code and discover domain taxonomy and patterns.

    Returns discovered patterns from agent analysis (empty until agent responds).
    """
    # Prepare agent invocation request
    request = {
        'code_snippet': code[:2000],  # First 2000 chars
        'full_code_length': len(code),
        'file_path': file_path,
        'language': language,
        'training_mode': 'offline'
    }

    print(f"""
🔬 ACE Domain Discovery Request (Offline Training)

File: {file_path} ({len(code)} chars, language: {language})

Please invoke the ace-orchestration:domain-discoverer agent to analyze this code
and discover domain taxonomy through bottom-up pattern analysis.

<domain_discovery_request>
{json.dumps(request, indent=2)}
</domain_discovery_request>

Use the Task tool to invoke the domain-discoverer agent with the data above.

The agent will:
1. Analyze the code to identify patterns (NO hardcoded keywords!)
2. Discover patterns from actual code evidence
3. Return patterns in database format

**CRITICAL**: Store results in .ace-memory/domains/{file_path}.json

Required JSON format:
{{
  "patterns": [
    {{
      "id": "unique-pattern-id",
      "name": "Pattern Name",
      "domain": "domain-name",
      "type": "positive",
      "description": "What this pattern does",
      "language": "{language}",
      "confidence": 0.0-1.0,
      "contributed_to": "success" | "failure" | "neutral"
    }}
  ]
}}
""", file=sys.stderr)

    # Write discovery request to queue for batch processing
    queue_dir = PROJECT_ROOT / '.ace-memory' / 'discovery-queue'
    queue_dir.mkdir(parents=True, exist_ok=True)

    # Create unique request ID from file path
    request_id = Path(file_path).stem + '-' + str(hash(file_path))[:8]
    request_file = queue_dir / f'{request_id}.request.json'
    response_file = queue_dir / f'{request_id}.response.json'

    # Write request
    with open(request_file, 'w') as f:
        json.dump(request, f, indent=2)

    # Check if response already exists (from previous run or agent)
    if response_file.exists():
        try:
            with open(response_file, 'r') as f:
                agent_output = json.load(f)
            return agent_output.get('patterns', [])
        except Exception as e:
            print(f"⚠️  Error reading response: {e}", file=sys.stderr)

    # No response yet - agent hasn't processed this request
    return []

def run_offline_training(epochs: int = MAX_EPOCHS, source: str = 'all', verbose: bool = True):
    """
    Run offline training for multiple epochs.

    Args:
        epochs: Number of epochs (default: 5 from paper)
        source: Training data source
        verbose: Print progress
    """
    if verbose:
        print(f"\n🚀 ACE Offline Training")
        print(f"=" * 60)
        print(f"Epochs: {epochs}")
        print(f"Source: {source}")
        print()

    # Initialize database with all tables (patterns, insights, observations)
    # Import ace-cycle.py to get init_database
    _ace_spec = importlib.util.spec_from_file_location("ace_cycle", Path(__file__).parent / "ace-cycle.py")
    _ace_cycle = importlib.util.module_from_spec(_ace_spec)
    _ace_spec.loader.exec_module(_ace_cycle)
    _ace_cycle.init_database()

    # Scan for training data
    if verbose:
        print("📂 Scanning codebase for training examples...")

    training_data = scan_codebase_for_training(source)

    if not training_data:
        print("❌ No training data found", file=sys.stderr)
        return

    if verbose:
        print(f"✅ Found {len(training_data)} training examples\n")

    # Run epochs
    for epoch_num in range(1, epochs + 1):
        if verbose:
            print(f"\n{'='*60}")
            print(f"📚 Epoch {epoch_num}/{epochs}")
            print(f"{'='*60}\n")

        # Start epoch
        epoch_id = start_epoch()

        # Get patterns before
        patterns_before = get_all_patterns()
        avg_conf_before = sum(p.get('confidence', 0) for p in patterns_before) / max(len(patterns_before), 1)

        patterns_processed = 0
        patterns_refined = 0

        # Import ace-cycle.py functions
        _ace_spec = importlib.util.spec_from_file_location("ace_cycle", Path(__file__).parent / "ace-cycle.py")
        _ace_cycle = importlib.util.module_from_spec(_ace_spec)
        _ace_spec.loader.exec_module(_ace_cycle)

        reflect = _ace_cycle.reflect
        curate = _ace_cycle.curate
        merge_patterns = _ace_cycle.merge_patterns
        store_pattern = _ace_cycle.store_pattern
        _infer_language_from_file = _ace_cycle._infer_language_from_file

        # Process each training example
        for idx, example in enumerate(training_data):
            if verbose and (idx + 1) % 10 == 0:
                print(f"  Processing {idx + 1}/{len(training_data)}...", file=sys.stderr)

            # BATCH MODE: Attempt agent-based discovery
            # TRUE ACE requires agent analysis, not hardcoded patterns
            language = _infer_language_from_file(example['file_path'])
            discovered = batch_reflect_via_agent(example['code'], example['file_path'], language)

            if verbose and discovered:
                print(f"  📊 Discovered {len(discovered)} patterns in {example['file_path']}", file=sys.stderr)

            if not discovered:
                continue

            patterns_processed += len(discovered)

            # Curate each discovered pattern
            existing_patterns = get_all_patterns()

            for pattern_def in discovered:
                pattern_id = pattern_def.get('id')
                if not pattern_id:
                    continue

                # Check if pattern exists
                existing = next((p for p in existing_patterns if p['id'] == pattern_id), None)
                conf_before = existing['confidence'] if existing else 0.0

                # Prepare new observation from discovered pattern
                new_pattern = {
                    'id': pattern_def.get('id'),
                    'name': pattern_def.get('name', 'Unknown pattern'),
                    'domain': pattern_def.get('domain', 'general'),
                    'type': pattern_def.get('type', 'neutral'),
                    'description': pattern_def.get('description', ''),
                    'language': pattern_def.get('language', _infer_language_from_file(example['file_path'])),
                    'observations': 1,
                    'successes': 1 if pattern_def.get('contributed_to') == 'success' else 0,
                    'failures': 1 if pattern_def.get('contributed_to') == 'failure' else 0,
                    'neutrals': 1 if pattern_def.get('contributed_to') == 'neutral' else 0,
                    'confidence': pattern_def.get('confidence', 0.0),
                    'last_seen': datetime.now().isoformat()
                }

                if existing:
                    # Merge with existing
                    merged = merge_patterns(existing, new_pattern)
                    merged['confidence'] = merged['successes'] / max(merged['observations'], 1)
                    store_pattern(merged)

                    conf_after = merged['confidence']
                    if abs(conf_after - conf_before) > 0.01:
                        patterns_refined += 1

                    # Track evolution
                    track_pattern_evolution(
                        pattern_id=pattern_id,
                        epoch_number=epoch_id,
                        confidence_before=conf_before,
                        confidence_after=conf_after,
                        observations_added=1,
                        refinement_applied=True
                    )
                else:
                    # Create new
                    new_pattern['confidence'] = new_pattern['successes'] / max(new_pattern['observations'], 1)
                    new_pattern['created_at'] = datetime.now().isoformat()
                    store_pattern(new_pattern)
                    patterns_refined += 1

            # Cache for future epochs (OUTSIDE pattern loop!)
            if discovered:
                cache_training_data(
                    file_path=example['file_path'],
                    code=example['code'],
                    patterns_detected=[p['id'] for p in discovered],
                    test_status='passed'
                )

        # Get patterns after
        patterns_after = get_all_patterns()
        avg_conf_after = sum(p.get('confidence', 0) for p in patterns_after) / max(len(patterns_after), 1)

        # Complete epoch
        complete_epoch(epoch_id, {
            'patterns_processed': patterns_processed,
            'patterns_refined': patterns_refined,
            'avg_confidence_before': avg_conf_before,
            'avg_confidence_after': avg_conf_after
        })

        if verbose:
            print(f"\n  ✅ Epoch {epoch_num} complete:")
            print(f"     Patterns processed: {patterns_processed}")
            print(f"     Patterns refined: {patterns_refined}")
            print(f"     Avg confidence: {avg_conf_before:.2%} → {avg_conf_after:.2%}")

            improvement = avg_conf_after - avg_conf_before
            if improvement > 0:
                print(f"     Improvement: +{improvement:.2%} 📈")

    # Check for pending discovery requests
    queue_dir = PROJECT_ROOT / '.ace-memory' / 'discovery-queue'
    if queue_dir.exists():
        pending_requests = list(queue_dir.glob('*.request.json'))
        if pending_requests:
            print(f"\n{'='*60}")
            print(f"⏸️  OFFLINE TRAINING PAUSED")
            print(f"{'='*60}\n")
            print(f"Found {len(pending_requests)} pending pattern discovery requests.")
            print(f"\nPlease process these requests by invoking the domain-discoverer agent:")
            print(f"\n  Location: {queue_dir}/")
            print(f"\nFor each *.request.json file:")
            print(f"  1. Read the request")
            print(f"  2. Invoke domain-discoverer agent with the code")
            print(f"  3. Save agent output as *.response.json (same filename)")
            print(f"\nAfter processing all requests, re-run: /ace-train-offline")
            print(f"\nThe training will resume and use the discovered patterns.\n")
            return

    # Generate final playbook
    if verbose:
        print(f"\n{'='*60}")
        print("📝 Generating final playbook...")

    subprocess.run([
        'python3',
        str(PLUGIN_ROOT / 'scripts' / 'generate-playbook.py')
    ], check=False)

    if verbose:
        print("✅ Offline training complete!\n")

def get_all_patterns() -> List[Dict]:
    """Get all patterns from database."""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM patterns')
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='ACE Offline Training - Multi-epoch pattern learning'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=MAX_EPOCHS,
        help=f'Number of training epochs (default: {MAX_EPOCHS})'
    )
    parser.add_argument(
        '--source',
        choices=['all', 'git-history', 'test-files', 'specs-history'],
        default='all',
        help='Training data source (specs-history = learn from committed playbooks)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )

    args = parser.parse_args()

    run_offline_training(
        epochs=args.epochs,
        source=args.source,
        verbose=not args.quiet
    )

if __name__ == '__main__':
    main()
