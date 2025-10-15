#!/usr/bin/env python3
"""
Database migration script for ACE Phase 2

Adds missing fields to existing patterns.db:
- bullet_id TEXT UNIQUE NOT NULL
- helpful_count INTEGER DEFAULT 0
- harmful_count INTEGER DEFAULT 0

This script safely migrates existing databases without data loss.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / '.ace-memory' / 'patterns.db'
BACKUP_PATH = PROJECT_ROOT / '.ace-memory' / f'patterns.db.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def backup_database():
    """Create backup of existing database."""
    if not DB_PATH.exists():
        print("❌ No database found to migrate", file=sys.stderr)
        return False

    import shutil
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"✅ Backup created: {BACKUP_PATH}", file=sys.stderr)
    return True

def check_schema():
    """Check current schema for missing fields."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(patterns)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    missing = []
    if 'bullet_id' not in columns:
        missing.append('bullet_id')
    if 'helpful_count' not in columns:
        missing.append('helpful_count')
    if 'harmful_count' not in columns:
        missing.append('harmful_count')

    return missing

def generate_bullet_id(domain: str, pattern_id: str, index: int) -> str:
    """Generate bullet ID in ACE format."""
    prefix = pattern_id.split('-')[0] if '-' in pattern_id else domain[:3]
    return f"[{prefix}-{index:05d}]"

def migrate_database():
    """Perform database migration."""
    if not DB_PATH.exists():
        print("❌ No database to migrate", file=sys.stderr)
        return False

    # Check what needs to be added
    missing_fields = check_schema()
    if not missing_fields:
        print("✅ Database schema is already up to date!", file=sys.stderr)
        return True

    print(f"🔄 Migrating database (adding: {', '.join(missing_fields)})", file=sys.stderr)

    # Create backup
    if not backup_database():
        return False

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Add missing columns
        if 'bullet_id' in missing_fields:
            # Add column (temporarily allow NULL)
            cursor.execute('ALTER TABLE patterns ADD COLUMN bullet_id TEXT')

            # Generate bullet IDs for existing patterns
            cursor.execute('SELECT id, domain FROM patterns ORDER BY created_at')
            patterns = cursor.fetchall()

            for idx, (pattern_id, domain) in enumerate(patterns, 1):
                bullet_id = generate_bullet_id(domain, pattern_id, idx)
                cursor.execute('UPDATE patterns SET bullet_id = ? WHERE id = ?', (bullet_id, pattern_id))

            # Create unique index
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_bullet_id ON patterns(bullet_id)')
            print(f"  ✅ Added bullet_id (generated {len(patterns)} IDs)", file=sys.stderr)

        if 'helpful_count' in missing_fields:
            cursor.execute('ALTER TABLE patterns ADD COLUMN helpful_count INTEGER DEFAULT 0')
            cursor.execute('UPDATE patterns SET helpful_count = 0 WHERE helpful_count IS NULL')
            print("  ✅ Added helpful_count", file=sys.stderr)

        if 'harmful_count' in missing_fields:
            cursor.execute('ALTER TABLE patterns ADD COLUMN harmful_count INTEGER DEFAULT 0')
            cursor.execute('UPDATE patterns SET harmful_count = 0 WHERE harmful_count IS NULL')
            print("  ✅ Added harmful_count", file=sys.stderr)

        conn.commit()
        print("✅ Migration complete!", file=sys.stderr)
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        conn.rollback()

        # Restore backup
        import shutil
        shutil.copy2(BACKUP_PATH, DB_PATH)
        print(f"✅ Restored backup from {BACKUP_PATH}", file=sys.stderr)
        return False

    finally:
        conn.close()

def verify_migration():
    """Verify migration was successful."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check schema
    cursor.execute("PRAGMA table_info(patterns)")
    columns = {row[1] for row in cursor.fetchall()}

    required = {'bullet_id', 'helpful_count', 'harmful_count'}
    if not required.issubset(columns):
        print(f"❌ Verification failed! Missing: {required - columns}", file=sys.stderr)
        conn.close()
        return False

    # Check data
    cursor.execute('SELECT COUNT(*) FROM patterns WHERE bullet_id IS NULL')
    null_count = cursor.fetchone()[0]

    if null_count > 0:
        print(f"❌ Verification failed! {null_count} patterns have NULL bullet_id", file=sys.stderr)
        conn.close()
        return False

    cursor.execute('SELECT COUNT(*) FROM patterns')
    total = cursor.fetchone()[0]

    print(f"✅ Verification passed! {total} patterns migrated successfully", file=sys.stderr)
    conn.close()
    return True

if __name__ == '__main__':
    try:
        print("🔄 ACE Database Migration - Phase 2", file=sys.stderr)
        print("=" * 50, file=sys.stderr)

        if not migrate_database():
            sys.exit(1)

        if not verify_migration():
            sys.exit(1)

        print("=" * 50, file=sys.stderr)
        print("✅ Migration successful! Phase 2 database schema complete.", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"❌ Migration error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
