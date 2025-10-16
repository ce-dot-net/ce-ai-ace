---
description: Export learned patterns to share across projects
allowed-tools: Bash
---

# ACE Export Patterns

Export your learned patterns to a JSON file for backup or cross-project sharing.

Exported patterns include:
- Pattern definitions and metadata
- Confidence scores and observations
- Insights and recommendations
- Evolution history

!```bash
# Locate ACE plugin
if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
  PLUGIN_PATH="$CLAUDE_PLUGIN_ROOT"
else
  PLUGIN_PATH=$(find ~/.claude/plugins/marketplaces -type d -name "ace-orchestration" 2>/dev/null | head -1)
fi

if [ -z "$PLUGIN_PATH" ]; then
  echo "❌ ACE plugin not found"
  exit 1
fi

# Export patterns
python3 "$PLUGIN_PATH/scripts/pattern-portability.py" export --output ./my-patterns.json
```
