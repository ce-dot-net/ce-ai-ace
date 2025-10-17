---
description: Manually trigger ACE reflection cycle on current file
argument-hint: [file-path]
allowed-tools: Read, Bash, Task
---

# ACE Force Reflect

Manually trigger the ACE reflection cycle on a specific file.

Normally, ACE runs automatically after code changes. Use this command to:
- Re-analyze a file with updated patterns
- Test the ACE system
- Get immediate feedback on patterns

## Usage:
- `/ace-force-reflect` - Analyze most recently edited file
- `/ace-force-reflect path/to/file.py` - Analyze specific file

```bash
# Determine file to analyze
if [ -z "$ARGUMENTS" ]; then
  file=$(git diff --name-only HEAD | head -1)
else
  file="$ARGUMENTS"
fi

# Validate file exists
if [ -z "$file" ] || [ ! -f "$file" ]; then
  echo "❌ No file specified or file not found"
  exit 1
fi

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

# Trigger ACE cycle
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 "$PLUGIN_PATH/scripts/ace-cycle.py" "$file" --force
```
