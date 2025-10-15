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

1. **Determine file to analyze**:
   - If $1 provided: use that file path
   - Otherwise: use last edited file from git
   ```bash
   if [ -z "$1" ]; then
     file=$(git diff --name-only HEAD | head -1)
   else
     file="$1"
   fi
   ```

2. **Validate file exists**:
   - Check file exists
   - Check file is supported (.py, .js, .jsx, .ts, .tsx)
   - Show error if invalid

3. **Trigger ACE cycle** (find script path dynamically):
   ```bash
   PLUGIN_DIR=$(find ~/.claude/plugins/marketplaces -name "ce-ai-ace*" -o -name "*ace-orchestration*" 2>/dev/null | head -1)

   if [ -z "$PLUGIN_DIR" ]; then
     echo "❌ ACE plugin directory not found. Cannot trigger reflection."
     exit 1
   fi

   python3 "$PLUGIN_DIR/scripts/ace-cycle.py" "$file" --force
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
