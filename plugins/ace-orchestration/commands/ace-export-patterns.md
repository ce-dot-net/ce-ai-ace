---
description: Export learned patterns to share across projects
---

Export your learned patterns to a JSON file for backup or cross-project sharing.

```bash
# Find plugin installation path
PLUGIN_PATH=$(find ~/.claude/plugins/marketplaces -name "ace-plugin-marketplace" -type d 2>/dev/null | head -1)

if [ -z "$PLUGIN_PATH" ]; then
  echo "❌ ACE plugin not found. Please install via: /plugin install ace-orchestration@ace-plugin-marketplace"
  exit 1
fi

# Export patterns
python3 "$PLUGIN_PATH/scripts/pattern-portability.py" export --output ./my-patterns.json
```

Exported patterns include:
- Pattern definitions and metadata
- Confidence scores and observations
- Insights and recommendations
- Evolution history
