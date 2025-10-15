---
description: Import patterns from another project or backup
---

Import patterns from a previously exported JSON file.

```bash
# Find plugin installation path
PLUGIN_PATH=$(find ~/.claude/plugins/marketplaces -name "ace-plugin-marketplace" -type d 2>/dev/null | head -1)

if [ -z "$PLUGIN_PATH" ]; then
  echo "❌ ACE plugin not found. Please install via: /plugin install ace-orchestration@ace-plugin-marketplace"
  exit 1
fi

# Import patterns
python3 "$PLUGIN_PATH/plugins/ace-orchestration/scripts/pattern-portability.py" import --input ./patterns.json
```

Imported patterns will be merged with existing ones using ACE's deterministic curation algorithm.
