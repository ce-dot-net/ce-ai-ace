# 🧪 ACE Plugin Consumer Test

**For testing the latest ACE plugin with slash command fixes**

Copy this entire prompt into your Claude Code CLI session in any project directory.

---

## 📋 COPY THIS ENTIRE BLOCK:

```
I want to test the ACE plugin (latest version with slash command fixes).

Help me verify all features work correctly:

## Step 1: Update Plugin

First, let's update to the latest version:

```bash
# Update the plugin to latest
/plugin update ace-orchestration@ace-plugin-marketplace

# Restart will be needed after update
```

After updating, please restart Claude Code, then continue.

## Step 2: Verify Installation

Check the plugin is installed and loaded:

```bash
/plugin
```

You should see "ace-orchestration" in the list.

## Step 3: Create Test Directory

Let's create a fresh test directory:

```bash
mkdir -p ~/ace-consumer-test
cd ~/ace-consumer-test
```

## Step 4: Create Test Python File

Create a file called `calculator.py` with patterns ACE should detect:

```python
from typing import TypedDict
from dataclasses import dataclass
from pathlib import Path

# Pattern 1: TypedDict for configs [py-001]
class CalculatorConfig(TypedDict):
    precision: int
    round_results: bool
    max_operations: int

# Pattern 2: Dataclass [py-002]
@dataclass
class Calculation:
    operation: str
    operands: list[float]
    result: float
    timestamp: str

# Pattern 3: Context manager [py-004]
def save_history(history_path: Path, calculations: list[Calculation]):
    with open(history_path, 'w') as f:
        for calc in calculations:
            f.write(f"{calc.operation}: {calc.result}\n")

# Pattern 4: F-strings [py-005]
def format_result(calc: Calculation) -> str:
    return f"Operation: {calc.operation} = {calc.result}"

# Pattern 5: List comprehension [py-006]
def get_large_results(calcs: list[Calculation], threshold: float) -> list[float]:
    return [c.result for c in calcs if c.result > threshold]

# Pattern 6: Pathlib [py-007]
history_file = Path.home() / ".calculator" / "history.log"

# Anti-pattern 7: Bare except [py-003] - should be flagged!
def divide(a: float, b: float) -> float:
    try:
        return a / b
    except:  # BAD: catches everything including KeyboardInterrupt
        return 0.0
```

After creating this file, wait 3-5 seconds for ACE to automatically detect patterns.

## Step 5: Test Slash Commands (Self-Contained)

Now test the slash commands that should work WITHOUT CLAUDE_PLUGIN_ROOT:

### Test 1: Status Command
```bash
/ace-status
```

**Expected output**:
```
🎯 ACE Pattern Learning Status

📊 Overall Statistics:
   • Total Patterns: 7
   • High Confidence (≥70%): 0
   • Medium Confidence (30-70%): 0
   • Low Confidence (<30%): 7

🔥 Top Patterns:
   • Use TypedDict for configs: 0.0% (1 obs)
   • Use dataclasses for data structures: 0.0% (1 obs)
   ...
```

### Test 2: List All Patterns
```bash
/ace-patterns
```

**Expected output**: All 7 patterns listed with details

### Test 3: Filter by Domain
```bash
/ace-patterns python
```

**Expected output**: Only Python patterns (all 7 in this case)

### Test 4: Filter by Confidence
```bash
/ace-patterns python 0.5
```

**Expected output**: Only patterns with ≥50% confidence (none initially)

## Step 6: Verify Phase 3-5 Features

### Check Delta Updates (Phase 3)
Look for console output showing:
```
🔄 Computing playbook delta...
📊 Delta: +7 ~0 -0
  ✨ Added [py-00001] to section 'STRATEGIES AND HARD RULES'
  ...
✅ Delta applied successfully
```

**NOT** full CLAUDE.md rewrites!

### Check Semantic Embeddings (Phase 3)
```bash
ls -lh .ace-memory/
```

**Expected**: `embeddings-cache.json` file created (~29KB) after pattern merging occurs

### Check CLAUDE.md Bulletized Structure
```bash
cat CLAUDE.md | head -50
```

**Expected**: Patterns with bullet IDs like `[py-00001]`, `[py-00002]`, etc.

### Check Database Schema (Phase 2+)
```bash
sqlite3 .ace-memory/patterns.db "PRAGMA table_info(patterns)"
```

**Expected columns**:
- `bullet_id` (TEXT)
- `helpful_count` (INTEGER)
- `harmful_count` (INTEGER)
- All Phase 1-2 columns

### Check Epochs Table (Phase 4)
```bash
sqlite3 .ace-memory/patterns.db "SELECT name FROM sqlite_master WHERE type='table'"
```

**Expected tables**: `patterns`, `epochs`

## Step 7: Test Force Reflection

Manually trigger reflection on the file:

```bash
/ace-force-reflect calculator.py
```

**Expected**: ACE cycle runs again, patterns re-analyzed

## Step 8: Verify All Patterns Detected

Query the database:

```bash
sqlite3 .ace-memory/patterns.db "SELECT bullet_id, name, confidence, observations FROM patterns ORDER BY bullet_id"
```

**Expected output**:
```
[py-00001]|Use TypedDict for configs|0.0|1
[py-00002]|Use dataclasses for data structures|0.0|1
[py-00003]|Avoid bare except|0.0|1
[py-00004]|Use context managers for file operations|0.0|1
[py-00005]|Use f-strings for formatting|0.0|1
[py-00006]|Use list comprehensions|0.0|1
[py-00007]|Use pathlib over os.path|0.0|1
```

## Step 9: Test Pattern Evolution

Edit the file to trigger more observations:

```bash
echo "
# Another f-string example
print(f'Calculator ready with {len(history)} entries')
" >> calculator.py
```

Wait 3-5 seconds, then check:

```bash
/ace-status
```

**Expected**: Observation count increased for relevant patterns

## Step 10: Final Verification

Show me all the outputs from steps 5-9 so I can verify:

✅ Slash commands work from any directory (no CLAUDE_PLUGIN_ROOT needed)
✅ Delta updates working (no full rewrites)
✅ Semantic embeddings cache created
✅ Bulletized structure with IDs
✅ All 7 patterns detected
✅ Database has Phase 2-4 schema
✅ Hooks triggering automatically
✅ Force reflection works

```

---

## ✅ Success Criteria

After running all steps, you should see:

### Console Output
- ✅ ACE cycle runs automatically after file creation
- ✅ Delta updates: `🔄 Computing playbook delta...`
- ✅ No full CLAUDE.md rewrites
- ✅ Pattern detection: `🔍 Detected 7 pattern(s)`

### Slash Commands
- ✅ `/ace-status` works and shows 7 patterns
- ✅ `/ace-patterns` lists all patterns
- ✅ `/ace-patterns python` filters correctly
- ✅ `/ace-force-reflect` triggers reflection

### Files Created
- ✅ `.ace-memory/patterns.db` (SQLite database)
- ✅ `.ace-memory/embeddings-cache.json` (after similarity checks)
- ✅ `CLAUDE.md` (bulletized playbook)

### Database Schema
- ✅ `patterns` table with `bullet_id`, `helpful_count`, `harmful_count`
- ✅ `epochs` table exists

---

## 🐛 Troubleshooting

### Issue: Slash commands not found
**Solution**: You need to update the plugin first:
```bash
/plugin update ace-orchestration@ace-plugin-marketplace
```

### Issue: "No such table: patterns"
**Solution**: Database created on first pattern detection. If missing, try:
```bash
# Create .ace-memory directory
mkdir -p .ace-memory

# ACE will create database on next file edit
echo "# trigger" >> calculator.py
```

### Issue: No ACE cycle output
**Solution**: Make sure you're editing Python/JS/TS files. Try:
```bash
# Manually trigger
/ace-force-reflect calculator.py
```

### Issue: Embeddings cache not created
**Solution**: Normal on first run. Cache is created when similar patterns are compared (during merging). Try creating another file with similar patterns.

---

## 📊 What This Tests

This comprehensive test verifies:

1. ✅ **Plugin installation** - Latest version installed
2. ✅ **Pattern detection** - All 7 patterns found
3. ✅ **Database storage** - Phase 2-4 schema complete
4. ✅ **Slash commands** - Self-contained, no path dependencies
5. ✅ **Delta updates** - Incremental CLAUDE.md changes (Phase 3)
6. ✅ **Semantic embeddings** - Cache system working (Phase 3)
7. ✅ **Multi-epoch** - Epochs table created (Phase 4)
8. ✅ **Bulletized structure** - Pattern IDs generated (Phase 2)
9. ✅ **Hooks** - PostToolUse triggers automatically
10. ✅ **Force reflection** - Manual triggering works

---

## 🎯 Key Improvements Tested

### Slash Command Fix (Latest)
- **Before**: Commands required `CLAUDE_PLUGIN_ROOT`, failed from user directories
- **After**: Self-contained Python code, works from any directory
- **Files**: `commands/ace-status.md`, `commands/ace-patterns.md`

### Delta Updates (Phase 3)
- **Before**: Full CLAUDE.md rewrites caused context collapse
- **After**: Surgical delta updates (append, update, delete only changed lines)
- **File**: `scripts/playbook-delta-updater.py`

### Semantic Embeddings (Phase 3)
- **Before**: String similarity (Jaccard on words)
- **After**: Cosine similarity on sentence embeddings (85% threshold)
- **File**: `scripts/embeddings_engine.py`

---

**Run this test and show me ALL the outputs!** 🧪
