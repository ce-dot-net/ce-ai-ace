---
description: Show ACE pattern learning statistics and status
argument-hint:
allowed-tools: Read, Bash
---

# ACE Status

Display comprehensive statistics about the ACE pattern learning system.

## Steps:

1. **Check database existence**:
   - Look for `.ace-memory/patterns.db`
   - If missing, report that ACE hasn't learned patterns yet

2. **Query pattern statistics** (run Python script):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ace-stats.py
   ```

3. **Display results** in this format:

```
🎯 ACE Pattern Learning Status

📊 Overall Statistics:
   • Total Patterns: N
   • High Confidence (≥70%): N patterns
   • Medium Confidence (30-70%): N patterns
   • Low Confidence (<30%): N patterns
   • Total Observations: N
   • Overall Success Rate: X.X%

📈 By Domain:
   • python-typing: N patterns (avg confidence: X.X%)
   • javascript-react: N patterns (avg confidence: X.X%)
   • typescript-types: N patterns (avg confidence: X.X%)
   [... etc ...]

🔥 Top 5 Most Confident Patterns:
   1. [pattern name] - X.X% confidence (N observations)
   2. [pattern name] - X.X% confidence (N observations)
   [... etc ...]

📉 Low Confidence Patterns (may be pruned):
   • [pattern name] - X.X% confidence (N observations)
   [... etc ...]

⏰ Last Updated: [timestamp from CLAUDE.md]

💡 Tip: Use /ace-patterns to see detailed pattern list
```

4. **If errors occur**, show friendly message with troubleshooting steps
