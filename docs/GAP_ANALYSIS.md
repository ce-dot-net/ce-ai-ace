# ACE Plugin - Comprehensive Gap Analysis

*Based on ACE Research Paper (arXiv:2510.04618v1) and Serena MCP Integration*

---

## ✅ Phase 2 Verification

**Status: COMPLETE** ✅

- [x] Bulletized structure with IDs (`[py-00001]`)
- [x] Helpful/harmful counters in database
- [x] Database migration successful
- [x] ACE sections in CLAUDE.md
- [x] generate-playbook.py updated

**Verification**:
```bash
$ sqlite3 .ace-memory/patterns.db "SELECT bullet_id, helpful_count, harmful_count FROM patterns LIMIT 1"
[py-00001]|0|0
```

---

## 🚨 CRITICAL GAPS

### 1. **CLAUDE.md Full Rewrites (Violates ACE Paper)**

**Issue**: Our `generate-playbook.py` does full rewrites:
```python
PLAYBOOK_PATH.write_text(content)  # FULL REWRITE!
```

**ACE Paper Says**:
> "Incremental updates only - Never full rewrites"
> "Prevents context collapse through localized, structured changes"

**Impact**: HIGH
- Context collapse risk (especially with long playbooks)
- Inefficient (rewrites entire file)
- Loses fine-grained tracking

**Solution**: Implement delta-based CLAUDE.md updates
- Track changes (additions, updates, deletions)
- Apply surgical edits to existing file
- Keep version history

---

### 2. **String Similarity vs. Semantic Embeddings**

**Issue**: Using Jaccard similarity for deduplication:
```python
def jaccard(s1: str, s2: str) -> float:
    words1 = set(s1.split())
    words2 = set(s2.split())
    # ...
```

**ACE Paper Says**:
> "Uses semantic embeddings (not just string matching)"
> "Deduplicate with cosine similarity > 0.85 on sentence embeddings"

**Impact**: MEDIUM
- Less accurate pattern matching
- May miss similar patterns with different wording
- May keep duplicate patterns

**Solution**: Use embeddings for semantic similarity
- OpenAI embeddings API
- Sentence-transformers library
- Or dedicated Embeddings MCP

---

### 3. **No Multi-Epoch Training (Phase 4)**

**Issue**: Not implemented

**ACE Paper Says**:
> "Max offline epochs: 5"
> "Multi-epoch adds +2.6% improvement"

**Impact**: MEDIUM
- Missing performance gains
- Can't revisit training data
- No pattern evolution tracking

**Solution**: Implement Phase 4
- Add epochs table to database
- Track pattern evolution across epochs
- Offline training mode (max 5 epochs)

---

### 4. **No Serena Integration (Phase 5)**

**Issue**: Not using Serena's symbolic tools

**Available Serena Tools**:
- `find_symbol` - Symbol-level pattern detection
- `find_referencing_symbols` - Track pattern usage
- `get_symbols_overview` - File-level analysis
- `write_memory` / `read_memory` - Knowledge storage

**Impact**: HIGH
- Using regex instead of AST-based detection
- No symbolic code location tracking
- No automatic fix suggestions

**Solution**: Implement Phase 5
- Use `find_symbol` for pattern detection
- Use `find_referencing_symbols` for usage tracking
- Store ACE insights in Serena memories
- Use symbolic editing for suggestions

---

## ⚠️ MISSING HOOKS

**Current Hooks**:
- ✅ PostToolUse (Edit|Write) → ace-cycle.py
- ✅ SessionEnd → ace-session-end.py

**Missing Hooks** (Should Add):

### 1. **AgentStart Hook**
**Purpose**: Inject CLAUDE.md into agent context
**Why**: Ensure agents use ACE playbook
**Implementation**:
```json
{
  "AgentStart": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/inject-playbook.py"
    }]
  }]
}
```

### 2. **AgentEnd Hook**
**Purpose**: Analyze agent output for patterns
**Why**: Learn from agent behavior (meta-learning)
**Implementation**:
```json
{
  "AgentEnd": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/analyze-agent-output.py"
    }]
  }]
}
```

### 3. **PreToolUse Hook**
**Purpose**: Validate patterns before code is written
**Why**: Prevent anti-patterns proactively
**Implementation**:
```json
{
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-patterns.py"
    }]
  }]
}
```

---

## 🔌 MISSING STATE-OF-THE-ART MCPs

### 1. **Embeddings MCP** (CRITICAL)

**Purpose**: Semantic similarity for deduplication
**Why**: ACE paper uses sentence embeddings
**Current**: Jaccard string similarity
**Should Use**:
- OpenAI embeddings API
- Sentence-transformers (local)
- Dedicated embeddings MCP

**Example**:
```python
from openai import OpenAI

client = OpenAI()
embedding = client.embeddings.create(
    input="Use TypedDict for configs",
    model="text-embedding-3-small"
)
```

### 2. **Sequential-Thinking MCP**

**Purpose**: Structured reasoning for Reflector
**Why**: Better quality insights
**Status**: Mentioned but not actively used
**Should Use**: For multi-round iterative refinement

### 3. **Test Runner MCP**

**Purpose**: Robust test execution
**Why**: Support multiple frameworks
**Current**: Only `npm test`
**Should Support**:
- Python: pytest, unittest, nose
- JavaScript: jest, mocha, ava
- TypeScript: ts-jest
- Go: go test
- Rust: cargo test

### 4. **Code Analysis MCP (Nice-to-have)**

**Purpose**: AST-based pattern detection
**Why**: Better than regex
**Alternative**: Use tree-sitter
**Example**:
```python
from tree_sitter import Language, Parser
parser = Parser()
tree = parser.parse(code)
# Find patterns in AST
```

---

## 📊 SPECIFIC IMPLEMENTATION GAPS

### 1. **Reflector Iterative Refinement**

**Status**: Infrastructure exists, not fully implemented

**Code Location**: `ace-cycle.py:617-650`
```python
def reflect(code, patterns, evidence, file_path, max_rounds=5):
    # First round
    reflection = invoke_reflector_agent(...)

    # Iterative refinement (TODO)
    for round_num in range(1, max_rounds):
        # Not implemented - breaks after round 1
        break
```

**Fix**: Implement `invoke_reflector_agent_with_feedback()`

### 2. **Evidence Gathering Limited**

**Current**: Only tries `npm test`
```python
subprocess.run(['npm', 'test'], ...)
```

**Should Support**:
- Python: pytest, unittest
- Multiple test commands
- API call feedback
- Execution logs

### 3. **Pruning Not Lazy**

**ACE Paper**: "Lazy prune when context too large"
```python
if len(context) > MAX_CONTEXT_SIZE:
    prune_low_confidence()
```

**Current**: Prunes during pattern detection
```python
if new_pattern.get('observations', 0) >= MIN_OBSERVATIONS:
    if confidence < PRUNE_THRESHOLD:
        # prune
```

**Should**: Prune proactively based on context size

### 4. **No Bullet Metadata Display**

**ACE Paper Bullet Format**:
```
[py-00001] helpful=5 harmful=1 domain=python-typing obs=6 success_rate=0.83
```

**Current Display**:
```
[py-00001] helpful=0 harmful=0 :: **Use TypedDict**
```

**Missing**:
- Success rate
- Observations count
- Domain

---

## 🎯 SERENA INTEGRATION OPPORTUNITIES

### 1. **Symbol-Level Pattern Detection**

**Current**: Regex on raw code
```python
re.search(pattern['regex'], code)
```

**With Serena**:
```python
# Find all functions using TypedDict
symbols = find_symbol(
    name_path="Config",
    include_kinds=[5],  # Class
    relative_path="src/"
)
# Check if they inherit from TypedDict
```

**Benefit**: AST-aware, more accurate

### 2. **Reference Tracking**

**Current**: Not tracking where patterns are used

**With Serena**:
```python
# Track all usages of a pattern
references = find_referencing_symbols(
    name_path="Config",
    relative_path="src/config.py"
)
# See everywhere this pattern is applied
```

**Benefit**: Understand pattern adoption

### 3. **Serena Memories for ACE**

**Current**: SQLite database only

**With Serena**:
```python
# Store ACE insight
write_memory(
    memory_name="ACE_Insights",
    content=f"""
# Pattern: {pattern['name']}

**Confidence**: {confidence}
**Observations**: {observations}
**Latest Insight**: {insight}
"""
)
```

**Benefit**: Searchable, shareable, versioned

### 4. **Symbolic Editing Suggestions**

**Current**: No automatic fixes

**With Serena**:
```python
# Detect anti-pattern
if pattern['type'] == 'harmful':
    # Suggest symbolic fix
    replace_symbol_body(
        name_path="process_data",
        relative_path="src/utils.py",
        body="# Fixed version without bare except"
    )
```

**Benefit**: Actionable feedback

---

## 🔄 CLAUDE.MD INJECTION PROBLEM

**Issue**: CLAUDE.md is generated but not injected

**Current**:
1. generate-playbook.py writes CLAUDE.md ✅
2. Claude Code reads it on startup ✅
3. BUT: Full rewrites (not delta updates) ❌
4. BUT: Not injected into agent contexts ❌

**ACE Paper Says**:
> "Contexts are evolving playbooks injected into generation"

**Solution**:
1. Implement delta-based updates (no full rewrites)
2. Add AgentStart hook to inject CLAUDE.md
3. Use Claude Code's context injection mechanism

**Claude Code Context Injection**:
```json
{
  "context": {
    "files": ["CLAUDE.md"],
    "inject_into": ["all_agents"]
  }
}
```

---

## 📈 IMPLEMENTATION PRIORITY

### Phase 3 (CRITICAL)
- [ ] Fix CLAUDE.md full rewrites → delta updates
- [ ] Implement semantic embeddings for deduplication
- [ ] Add Embeddings MCP or OpenAI embeddings
- [ ] Fix lazy pruning mechanism

### Phase 4 (HIGH)
- [ ] Multi-epoch training support
- [ ] Epoch tracking in database
- [ ] Offline training mode
- [ ] Pattern evolution tracking

### Phase 5 (HIGH)
- [ ] Serena symbolic pattern detection
- [ ] Reference tracking with `find_referencing_symbols`
- [ ] Store ACE insights in Serena memories
- [ ] Symbolic editing suggestions

### Missing Hooks (MEDIUM)
- [ ] AgentStart hook (inject CLAUDE.md)
- [ ] AgentEnd hook (analyze agent output)
- [ ] PreToolUse hook (validate patterns)

### Evidence Gathering (MEDIUM)
- [ ] Support multiple test frameworks
- [ ] Add API call feedback
- [ ] Better execution log parsing

### Reflector (LOW)
- [ ] Implement iterative refinement fully
- [ ] Use Sequential-Thinking MCP

---

## 🎓 ACE PAPER COMPLIANCE CHECKLIST

| Feature | ACE Paper | Our Plugin | Status |
|---------|-----------|------------|--------|
| Three roles | ✅ | ✅ | COMPLETE |
| Bulletized structure | ✅ | ✅ | COMPLETE |
| Incremental delta updates | ✅ | ❌ | **CRITICAL GAP** |
| Semantic embeddings | ✅ | ❌ | **CRITICAL GAP** |
| 85% similarity threshold | ✅ | ✅ | COMPLETE |
| 30% prune threshold | ✅ | ✅ | COMPLETE |
| Lazy pruning | ✅ | ⚠️ | PARTIAL |
| Execution feedback | ✅ | ⚠️ | PARTIAL |
| Multi-epoch training | ✅ | ❌ | **MISSING** |
| Iterative refinement | ✅ | ⚠️ | PARTIAL |
| Comprehensive playbooks | ✅ | ✅ | COMPLETE |
| Deterministic curator | ✅ | ✅ | COMPLETE |

**Overall Compliance**: 7/12 Complete, 3/12 Partial, 2/12 Missing

---

## 🚀 NEXT STEPS

1. **Fix CLAUDE.md delta updates** (CRITICAL)
2. **Add Embeddings MCP** (CRITICAL)
3. **Implement Phase 5 (Serena integration)** (HIGH)
4. **Implement Phase 4 (Multi-epoch)** (HIGH)
5. **Add missing hooks** (MEDIUM)
6. **Improve evidence gathering** (MEDIUM)

---

## 💡 KEY TAKEAWAYS

1. **Phase 2 is complete** ✅ (database migrated)
2. **CRITICAL: We're doing full rewrites** (violates ACE paper)
3. **Need semantic embeddings** (paper requirement)
4. **Serena integration missing** (major opportunity)
5. **Multi-epoch not implemented** (Phase 4)
6. **Missing hooks for agent injection**

---

**Next Action**: Fix CLAUDE.md delta updates (most critical gap)
