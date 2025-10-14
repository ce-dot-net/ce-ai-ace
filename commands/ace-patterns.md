---
description: List learned patterns with filtering options
argument-hint: [domain] [min-confidence]
allowed-tools: Read, Bash, Grep
---

# ACE Patterns

Display learned patterns with optional filtering.

## Usage:
- `/ace-patterns` - Show all patterns
- `/ace-patterns python` - Show only Python patterns
- `/ace-patterns javascript 0.7` - Show JavaScript patterns with ≥70% confidence

## Steps:

1. **Parse arguments**:
   - $1 = domain filter (optional): python, javascript, typescript, etc.
   - $2 = minimum confidence (optional): 0.0-1.0

2. **Query database** (find script path dynamically):
   ```bash
   PLUGIN_DIR=$(find ~/.claude/plugins/marketplaces -name "ce-ai-ace*" -o -name "*ace-orchestration*" 2>/dev/null | head -1)

   if [ -z "$PLUGIN_DIR" ]; then
     echo "⚠️  ACE plugin directory not found. Using direct database query..."
   else
     python3 "$PLUGIN_DIR/scripts/ace-list-patterns.py" "$1" "$2"
   fi
   ```

3. **Display results** grouped by confidence:

```
🎯 ACE Learned Patterns

## 🟢 High Confidence (≥70%)

### [Pattern Name]
**ID**: py-001
**Domain**: python-typing
**Language**: Python
**Confidence**: 85.0% (17/20 successes)
**Observations**: 20

**Description**: Use TypedDict for type-safe configuration objects

💡 **Latest Insights**:
- [2025-10-14] TypedDict caught config typo at line 23, preventing runtime error
- [2025-10-13] IDE autocomplete improved developer experience

📋 **Recommendation**:
Use TypedDict for config objects with 3+ fields where type safety prevents common typos.

---

[... more patterns ...]

## 🟡 Medium Confidence (30-70%)

[... similar format ...]

## 🔴 Low Confidence (<30%)

[... similar format ...]
```

4. **If no patterns match**, show helpful message
5. **Add footer** with commands: `/ace-status`, `/ace-clear`, `/ace-force-reflect`
