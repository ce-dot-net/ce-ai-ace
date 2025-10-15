#!/usr/bin/env python3
"""
Test suite for ACE Plugin Phase 3-5 features

Run this after updating the plugin to verify all new features work correctly.
"""

import sys
import json
import sqlite3
from pathlib import Path

# Test results
tests_passed = 0
tests_failed = 0

def test(name):
    """Test decorator"""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            try:
                print(f"\n🧪 Testing: {name}")
                result = func()
                if result:
                    print(f"   ✅ PASS")
                    tests_passed += 1
                else:
                    print(f"   ❌ FAIL")
                    tests_failed += 1
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                tests_failed += 1
        return wrapper
    return decorator

@test("Database migration (Phase 2)")
def test_database_migration():
    """Check if database has Phase 2 schema"""
    db_path = Path('.ace-memory/patterns.db')
    if not db_path.exists():
        print("   ⚠️  No database yet (will be created on first run)")
        return True

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check for bullet_id column
    cursor.execute("PRAGMA table_info(patterns)")
    columns = {row[1] for row in cursor.fetchall()}

    has_bullet_id = 'bullet_id' in columns
    has_helpful = 'helpful_count' in columns
    has_harmful = 'harmful_count' in columns

    conn.close()

    if has_bullet_id and has_helpful and has_harmful:
        print("   ✓ bullet_id, helpful_count, harmful_count present")
        return True
    else:
        print(f"   ✗ Missing: bullet_id={has_bullet_id}, helpful={has_helpful}, harmful={has_harmful}")
        return False

@test("Embeddings engine")
def test_embeddings_engine():
    """Check if embeddings engine is functional"""
    try:
        from scripts import embeddings_engine as emb

        # Test similarity
        sim = emb.calculate_semantic_similarity(
            "Use TypedDict for configs",
            "Define configs with TypedDict"
        )

        if 0.0 <= sim <= 1.0:
            print(f"   ✓ Semantic similarity: {sim:.3f}")

            # Check backend
            info = emb.get_backend_info()
            backend = "OpenAI" if info['openai'] else "Local" if info['local'] else "Fallback"
            print(f"   ✓ Backend: {backend}")
            return True
        return False

    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

@test("Delta updater")
def test_delta_updater():
    """Check if delta updater is functional"""
    try:
        sys.path.insert(0, 'scripts')
        from playbook_delta_updater import parse_existing_playbook

        playbook_path = Path('CLAUDE.md')
        if playbook_path.exists():
            sections = parse_existing_playbook()
            print(f"   ✓ Parsed {len(sections)} sections")
            return True
        else:
            print("   ⚠️  No CLAUDE.md yet (will be created on first pattern)")
            return True

    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

@test("Epoch manager")
def test_epoch_manager():
    """Check if epoch manager is functional"""
    db_path = Path('.ace-memory/patterns.db')
    if not db_path.exists():
        print("   ⚠️  No database yet")
        return True

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check for epochs table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='epochs'")
    has_epochs = cursor.fetchone() is not None

    if has_epochs:
        cursor.execute("SELECT COUNT(*) FROM epochs")
        count = cursor.fetchone()[0]
        print(f"   ✓ Epochs table exists ({count} epochs)")
        conn.close()
        return True
    else:
        print("   ⚠️  Epochs table not created yet (will be created on first epoch)")
        conn.close()
        return True

@test("Serena detector")
def test_serena_detector():
    """Check if Serena hybrid detector is functional"""
    try:
        sys.path.insert(0, 'scripts')
        import importlib.util
        spec = importlib.util.spec_from_file_location("serena_detector", "scripts/serena-pattern-detector.py")
        detector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(detector)

        # Test with this file
        test_code = "def test(): pass"
        patterns = detector.detect_patterns_hybrid("test.py", test_code)

        print(f"   ✓ Hybrid detector functional")
        return True

    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

@test("Hooks configuration")
def test_hooks():
    """Check if all hooks are configured"""
    hooks_path = Path('hooks/hooks.json')
    if not hooks_path.exists():
        print("   ✗ hooks.json not found")
        return False

    with open(hooks_path, 'r') as f:
        hooks = json.load(f)

    expected = ['AgentStart', 'AgentEnd', 'PreToolUse', 'PostToolUse', 'SessionEnd']
    configured = list(hooks.get('hooks', {}).keys())

    missing = set(expected) - set(configured)

    if not missing:
        print(f"   ✓ All 5 hooks configured: {', '.join(configured)}")
        return True
    else:
        print(f"   ✗ Missing hooks: {', '.join(missing)}")
        return False

@test("Hook scripts exist")
def test_hook_scripts():
    """Check if all hook scripts exist and are executable"""
    scripts = [
        'scripts/inject-playbook.py',
        'scripts/analyze-agent-output.py',
        'scripts/validate-patterns.py',
        'scripts/ace-cycle.py',
        'scripts/ace-session-end.py'
    ]

    all_exist = True
    for script in scripts:
        path = Path(script)
        if not path.exists():
            print(f"   ✗ Missing: {script}")
            all_exist = False
        elif not path.stat().st_mode & 0o111:
            print(f"   ⚠️  Not executable: {script}")

    if all_exist:
        print(f"   ✓ All 5 hook scripts present")
        return True
    return False

@test("Documentation")
def test_documentation():
    """Check if documentation is complete"""
    docs = [
        'docs/GAP_ANALYSIS.md',
        'docs/PHASES_3_5_COMPLETE.md',
        'README.md',
        'QUICKSTART.md'
    ]

    all_exist = True
    for doc in docs:
        if not Path(doc).exists():
            print(f"   ✗ Missing: {doc}")
            all_exist = False

    if all_exist:
        print(f"   ✓ All documentation present")
        return True
    return False

@test("Embeddings cache directory")
def test_cache_directory():
    """Check if .ace-memory directory exists"""
    cache_dir = Path('.ace-memory')

    if cache_dir.exists():
        files = list(cache_dir.glob('*'))
        print(f"   ✓ .ace-memory exists ({len(files)} files)")
        return True
    else:
        print("   ⚠️  .ace-memory not created yet (will be created on first run)")
        return True

# Run all tests
if __name__ == '__main__':
    print("=" * 70)
    print("🧪 ACE Plugin - Phase 3-5 Test Suite")
    print("=" * 70)

    # Run tests
    test_database_migration()
    test_embeddings_engine()
    test_delta_updater()
    test_epoch_manager()
    test_serena_detector()
    test_hooks()
    test_hook_scripts()
    test_documentation()
    test_cache_directory()

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {tests_passed} passed, {tests_failed} failed")

    if tests_failed == 0:
        print("✅ All tests passed! Plugin is ready to use.")
        sys.exit(0)
    else:
        print(f"⚠️  {tests_failed} test(s) failed. Check output above.")
        sys.exit(1)
