---
description: List learned patterns with filtering options
argument-hint: [domain] [min-confidence]
allowed-tools: Bash
---

# ACE Patterns

Display learned patterns with optional filtering.

## Usage:
- `/ace-patterns` - Show all patterns
- `/ace-patterns python` - Show only Python patterns
- `/ace-patterns javascript 0.7` - Show JavaScript patterns with ≥70% confidence

!```bash
if [ -f .ace-memory/patterns.db ]; then
  python3 -c "
import sqlite3
import sys
from pathlib import Path

domain = sys.argv[1] if len(sys.argv) > 1 else None
min_conf = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0

db = Path('.ace-memory/patterns.db')
conn = sqlite3.connect(str(db))
cursor = conn.cursor()

query = 'SELECT name, domain, language, confidence, observations FROM patterns WHERE confidence >= ?'
params = [min_conf]

if domain:
    query += ' AND (domain LIKE ? OR language LIKE ?)'
    params.extend([f'%{domain}%', f'%{domain}%'])

query += ' ORDER BY confidence DESC, observations DESC'

cursor.execute(query, params)
patterns = cursor.fetchall()

if patterns:
    print('🎯 ACE Learned Patterns')
    print()
    for name, dom, lang, conf, obs in patterns:
        print(f'• {name}')
        print(f'  Domain: {dom} | Language: {lang}')
        print(f'  Confidence: {conf*100:.1f}% ({obs} observations)')
        print()
else:
    print('⚠️  No patterns match your filter criteria')

conn.close()
" "$1" "$2"
else
  echo "⚠️  No patterns learned yet. Start coding to detect patterns!"
fi
```
