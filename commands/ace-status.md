---
description: Show ACE pattern learning statistics and status
argument-hint:
allowed-tools: Bash
---

# ACE Status

Display comprehensive statistics about the ACE pattern learning system.

## Steps:

1. **Run stats from current directory**:
   ```bash
   if [ -f .ace-memory/patterns.db ]; then
     python3 -c "
import sqlite3
from pathlib import Path

db = Path('.ace-memory/patterns.db')
conn = sqlite3.connect(str(db))
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM patterns')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence >= 0.7')
high = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence >= 0.3 AND confidence < 0.7')
med = cursor.fetchone()[0]

cursor.execute('SELECT name, confidence, observations FROM patterns ORDER BY confidence DESC LIMIT 5')
patterns = cursor.fetchall()

print('🎯 ACE Pattern Learning Status')
print()
print(f'📊 Overall Statistics:')
print(f'   • Total Patterns: {total}')
print(f'   • High Confidence (≥70%): {high}')
print(f'   • Medium Confidence (30-70%): {med}')
print(f'   • Low Confidence (<30%): {total - high - med}')
print()
print('🔥 Top Patterns:')
for name, conf, obs in patterns:
    print(f'   • {name}: {conf*100:.1f}% ({obs} obs)')

conn.close()
"
   else
     echo "⚠️  No patterns learned yet. Start coding to see patterns!"
   fi
   ```

2. **Display statistics** from the patterns database in the current project
