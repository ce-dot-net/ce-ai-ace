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

## Steps:

Execute the following in a single bash command:

```bash
# Determine file to analyze
if [ -z "$1" ]; then
  file=$(git diff --name-only HEAD | head -1)
else
  file="$1"
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

4. **Show progress**:
   ```
   🔄 ACE Force Reflection

   📄 Analyzing: path/to/file.py

   Step 1/5: Detecting patterns...
   🔍 Found: 3 patterns (py-001, py-003, py-007)

   Step 2/5: Gathering evidence...
   🧪 Running tests...
   ✅ Tests passed

   Step 3/5: Invoking Reflector agent...
   🤔 Analyzing pattern effectiveness...
   💡 Reflection complete

   Step 4/5: Curating patterns...
   🔀 Merged: py-001 (87% similar to existing)
   ✨ Created: py-007 (new unique pattern)

   Step 5/5: Updating playbook...
   📖 CLAUDE.md updated

   ✅ ACE cycle complete!

   📊 View results: /ace-patterns
   📈 Check stats: /ace-status
   ```

5. **Handle errors gracefully** with troubleshooting hints
