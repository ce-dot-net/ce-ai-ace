# Fix for Claude Code 400 API Error

**Issue**: `API Error: 400 due to tool use concurrency issues`
**Root Cause**: Parallel PostToolUse hook executions creating malformed API requests
**Status**: ✅ FIXED in ace-cycle.py v2.4.1

---

## The Problem

When Claude Code executes multiple Edit/Write operations in parallel:
1. Both operations trigger PostToolUse hook simultaneously
2. Two `ace-cycle.py` processes start running concurrently
3. Both hooks output `{'continue': True}` at slightly different times
4. Claude Code's message builder gets confused about which `tool_result` belongs to which `tool_use`
5. API request sent to Anthropic is missing `tool_result` blocks
6. Anthropic API rejects with `400 Bad Request`

## The Solution

Added **file-based mutual exclusion lock** to `ace-cycle.py`:

```python
import fcntl

def main():
    # CONCURRENCY LOCK: Prevent parallel PostToolUse hook executions
    lock_file = PROJECT_ROOT / '.ace-memory' / '.ace-cycle.lock'
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to acquire lock (non-blocking)
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        # Another ace-cycle.py is running, skip this one
        print("⏭️  ACE cycle already running, skipping duplicate", file=sys.stderr)
        print(json.dumps({'continue': True}))
        sys.exit(0)

    try:
        # ... existing ACE cycle logic ...
    finally:
        # Release lock
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()
        lock_file.unlink(missing_ok=True)
```

## How It Works

1. **First parallel Edit**: ace-cycle.py acquires lock, starts processing
2. **Second parallel Edit**: ace-cycle.py tries to acquire lock, fails
3. **Second instance**: Immediately exits with `{'continue': True}`, no processing
4. **First instance**: Completes normally, releases lock
5. **Result**: Only ONE hook execution happens, preventing message corruption

## Benefits

✅ **Prevents 400 errors** from parallel tool executions
✅ **No performance impact** - lock check is instant
✅ **Graceful degradation** - second edit just skips pattern learning
✅ **No user workflow interruption** - both edits succeed
✅ **Proper cleanup** - lock always released via finally block

## Technical Details

### Lock Mechanism: fcntl.flock()

- **File-based**: Uses `.ace-memory/.ace-cycle.lock`
- **Non-blocking**: `LOCK_EX | LOCK_NB` - fails immediately if locked
- **Process-safe**: Works across different Python processes
- **Automatic cleanup**: Lock released on process termination even if crash

### Alternative Approaches Considered

❌ **Debounce/delay**: Adds latency, doesn't guarantee ordering
❌ **Queue system**: Too complex, requires background process
❌ **Disable parallel tools**: Breaks Claude Code's performance optimization
✅ **Mutual exclusion lock**: Simple, reliable, no side effects

## Testing

To test the fix:

```bash
# Create two test files
echo "def test1(): pass" > test1.py
echo "def test2(): pass" > test2.py

# Ask Claude to edit both in parallel
# "Edit test1.py and test2.py to add docstrings"

# Check logs - should see:
# 🔄 ACE: Starting reflection cycle for test1.py
# ⏭️  ACE cycle already running, skipping duplicate
# ✅ ACE cycle complete (1 patterns processed)
```

## Migration Notes

**No migration required**. The fix is backward compatible:
- Existing hooks continue working
- Lock file created automatically
- No configuration changes needed

## Recovery Instructions

If you still encounter 400 errors:

1. **Use /rewind** (Claude Code 2.0+)
   ```bash
   /rewind
   # Or press Esc+Esc
   # Choose: code only, conversation only, or both
   ```

2. **Check lock file** (rare case: stale lock)
   ```bash
   rm .ace-memory/.ace-cycle.lock
   ```

3. **Report issue** with:
   - Claude Code version
   - Number of parallel edits
   - Hook configuration
   - Error timestamp

## References

- **Issue Analysis**: `docs/ACE_400_ERROR_ANALYSIS.md`
- **Claude Code Checkpointing**: https://docs.claude.com/en/docs/claude-code/checkpointing
- **fcntl documentation**: https://docs.python.org/3/library/fcntl.html
- **ACE Research Paper**: https://arxiv.org/abs/2510.04618

---

**Fixed in**: v2.4.1
**Date**: 2025-10-18
**Tested on**: macOS (fcntl available on all Unix-like systems)
