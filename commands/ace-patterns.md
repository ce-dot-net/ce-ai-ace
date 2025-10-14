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

## Steps:

1. **Run pattern list script**:
   ```bash
   python3 scripts/ace-list-patterns.py "$1" "$2" 2>/dev/null || echo "⚠️  No patterns learned yet. Start coding to detect patterns!"
   ```

2. **The script will display**: List of patterns grouped by confidence level with details

3. **If no patterns exist yet**, explain that ACE learns patterns automatically as you code
