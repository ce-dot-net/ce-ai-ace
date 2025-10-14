---
description: Show ACE pattern learning statistics and status
argument-hint:
allowed-tools: Bash
---

# ACE Status

Display comprehensive statistics about the ACE pattern learning system.

## Steps:

1. **Check database existence and run stats**:
   ```bash
   python3 scripts/ace-stats.py 2>/dev/null || echo "⚠️  No patterns learned yet. Start coding to see patterns!"
   ```

2. **The script will display**: Statistics about learned patterns, confidence levels, and domain breakdown

3. **If database doesn't exist**, explain that ACE needs to detect patterns first by editing Python/JS/TS files
