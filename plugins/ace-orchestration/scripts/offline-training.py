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
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Try to import Claude Agent SDK for automatic agent invocation
# NOTE: SDK only works for EXTERNAL automation, not when running from within Claude Code
try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    # Check if running from within Claude Code (via slash command)
    # If so, disable SDK to avoid trying to spawn nested Claude processes
    import os
    if os.environ.get('CLAUDECODE') or os.environ.get('CLAUDE_CODE_ENTRYPOINT'):
        SDK_AVAILABLE = False
        print("ℹ️  Running from within Claude Code - using manual agent invocation", file=sys.stderr)
    else:
        SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("⚠️  Claude Agent SDK not available. Install with: pip install claude-agent-sdk", file=sys.stderr)
    print("    Falling back to manual agent invocation workflow.", file=sys.stderr)

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
    Pattern discovery via Claude Code agent invocation.

    TRUE ACE Architecture: Patterns are DISCOVERED by agents analyzing code,
    NOT matched against hardcoded keywords.

    This function coordinates with Claude to invoke the domain-discoverer agent.
    The workflow:
    1. Check if agent response already exists (cached from previous run)
    2. If not, output request to stderr for Claude to process
    3. Return cached patterns if available, empty list if not yet processed

    Returns discovered patterns from agent analysis (empty until Claude processes request).
    """
    # Create unique request ID from file path (deterministic hash)
    queue_dir = PROJECT_ROOT / '.ace-memory' / 'discovery-queue'
    queue_dir.mkdir(parents=True, exist_ok=True)

    hash_obj = hashlib.md5(file_path.encode())
    request_id = Path(file_path).stem + '-' + hash_obj.hexdigest()[:8]
    request_file = queue_dir / f'{request_id}.request.json'
    response_file = queue_dir / f'{request_id}.response.json'

    # Check if response already exists (cached from previous agent run)
    if response_file.exists():
        try:
            with open(response_file, 'r') as f:
                agent_output = json.load(f)

            # Convert domain-discoverer agent response format to pattern list
            # Agent returns: {concrete: {...}, abstract: {...}, principles: {...}}
            # We need to convert to: [{id, name, domain, description, confidence}, ...]
            patterns = []

            # Process concrete domains
            for domain_id, domain_data in agent_output.get('concrete', {}).items():
                for pattern_name in domain_data.get('patterns', []):
                    # Generate deterministic ID from pattern content (not loop index!)
                    pattern_hash = hashlib.md5(f"{domain_id}:{pattern_name}".encode()).hexdigest()[:5]
                    patterns.append({
                        'id': f"{domain_id}-{pattern_hash}",
                        'name': pattern_name,
                        'domain': domain_id,
                        'type': 'helpful',
                        'description': domain_data.get('description', ''),
                        'confidence': domain_data.get('confidence', 0.5),
                        'language': language
                    })

            # Process abstract patterns
            for pattern_id, pattern_data in agent_output.get('abstract', {}).items():
                # Abstract pattern IDs already unique from agent
                patterns.append({
                    'id': f"abstract-{pattern_id}",
                    'name': pattern_id,
                    'domain': 'abstract-patterns',
                    'type': 'helpful',
                    'description': pattern_data.get('description', ''),
                    'confidence': pattern_data.get('confidence', 0.5),
                    'language': language
                })

            # Process principles
            for principle_id, principle_data in agent_output.get('principles', {}).items():
                # Principle IDs already unique from agent
                patterns.append({
                    'id': f"principle-{principle_id}",
                    'name': principle_id,
                    'domain': 'principles',
                    'type': 'helpful',
                    'description': principle_data.get('description', ''),
                    'confidence': principle_data.get('confidence', 0.5),
                    'language': language
                })

            return patterns
        except Exception as e:
            print(f"⚠️  Error reading cached response: {e}", file=sys.stderr)

    # No response yet - write request for Claude to process
    if not request_file.exists():
        request = {
            'code_snippet': code[:2000],  # First 2000 chars for context
            'full_code_length': len(code),
            'file_path': file_path,
            'language': language,
            'training_mode': 'offline',
            'request_id': request_id
        }

        with open(request_file, 'w') as f:
            json.dump(request, f, indent=2)

        # Try to invoke agent automatically using Claude Agent SDK
        if SDK_AVAILABLE:
            try:
                print(f"""
🔬 ACE Domain Discovery Request

File: {file_path} ({len(code)} chars, language: {language})
Request ID: {request_id}

Invoking domain-discoverer agent via Claude Agent SDK...
""", file=sys.stderr)

                # Use SDK to invoke the agent
                agent_response = asyncio.run(invoke_agent_via_sdk(request_file, response_file, file_path, code, language))

                if agent_response:
                    print(f"✅ Agent response received and saved", file=sys.stderr)
                    # Response was saved, recursive call will read it
                    return batch_reflect_via_agent(code, file_path, language)
                else:
                    print(f"⚠️  Agent invocation failed, request saved for manual processing", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  SDK agent invocation error: {e}", file=sys.stderr)
                print(f"    Falling back to manual workflow", file=sys.stderr)

        # Fallback: Output request to stderr for manual Claude processing
        if not SDK_AVAILABLE or True:  # Always show this for now
            print(f"""
📝 Request saved to: {request_file}
💡 Invoke manually: Use Task tool with ace-orchestration:domain-discoverer
   Or install SDK: pip install claude-agent-sdk
""", file=sys.stderr)

    # No response yet - return empty (will be filled on subsequent run after Claude processes)
    return []

async def invoke_agent_via_sdk(request_file: Path, response_file: Path, file_path: str, code: str, language: str) -> bool:
    """
    Invoke domain-discoverer agent using Claude Agent SDK.

    Uses the Task tool to invoke the domain-discoverer agent programmatically.

    Returns True if successful, False otherwise.
    """
    try:
        # Build the agent invocation prompt
        # Note: This uses the Task tool to invoke the domain-discoverer agent
        agent_prompt = f"""Use the Task tool to invoke the domain-discoverer agent with the following task:

Read the request file at {request_file} and discover coding patterns.

The file contains {language} code from {file_path} ({len(code)} characters).

Analyze the code and discover:
1. Concrete domains (specific APIs, imports, patterns)
2. Abstract patterns (architectural approaches)
3. Principles (best practices)

Save your JSON response to: {response_file}

The response must follow this format:
{{
  "concrete": {{"domain-id": {{"description": "...", "confidence": 0.9}}}},
  "abstract": {{"pattern-id": {{"description": "...", "confidence": 0.8}}}},
  "principles": {{"principle-id": {{"description": "...", "confidence": 0.7}}}}
}}"""

        # Configure SDK options - allow Task tool for agent invocation
        options = ClaudeAgentOptions(
            allowed_tools=["Task", "Read", "Write"],
            permission_mode="acceptEdits",
            cwd=str(PROJECT_ROOT)
        )

        # Invoke via SDK streaming mode (recommended per docs)
        async for message in query(prompt=agent_prompt, options=options):
            # Messages stream back - wait for completion
            pass

        # Check if response file was created
        return response_file.exists()

    except Exception as e:
        print(f"SDK invocation failed: {e}", file=sys.stderr)
        return False

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
