---
description: Import patterns from another project or backup
allowed-tools: Bash
---

# ACE Import Patterns

Import patterns from a previously exported JSON file.

Imported patterns will be merged with existing ones using ACE's deterministic curation algorithm.

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

# Import patterns
python3 "$PLUGIN_PATH/scripts/pattern-portability.py" import --input ./patterns.json
```
