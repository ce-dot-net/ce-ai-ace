# Implementation Decisions & Rationale

## Why These Choices Were Made

### 1. Deterministic Curator (Not LLM-Based)

**Decision**: Curator uses pure algorithmic logic (string similarity), NO LLM calls

**Rationale**:
- ✅ Research explicitly states: "non-LLM merges"
- ✅ Reproducible results (no LLM variance)
- ✅ Much lower latency (no API call)
- ✅ Lower cost (no tokens consumed)
- ✅ Works offline

**Alternative Considered**: LLM-based curator
- ❌ Would be slower
- ❌ Would add variance
- ❌ Contradicts research

### 2. String Similarity (Not Embeddings)

**Decision**: Use `string-similarity` package for semantic matching

**Rationale**:
- ✅ Faster (no model loading)
- ✅ Sufficient for pattern names + short descriptions
- ✅ Research shows non-LLM methods work well
- ✅ Lightweight dependency

**Threshold**: 85% similarity (from research paper)
- Weighted: 60% name + 40% description

**Alternative Considered**: Embeddings (e.g., sentence-transformers)
- ❌ Would require model loading (~500MB)
- ❌ Slower
- ❌ Overkill for short text

### 3. Sequential-Thinking MCP for Reflection

**Decision**: Use sequential-thinking MCP (not simple prompt)

**Rationale**:
- ✅ Structured step-by-step reasoning
- ✅ Better insight quality than single prompt
- ✅ Aligns with research's reflective approach
- ✅ Fallback to test results if unavailable

**Alternative Considered**: Simple LLM prompt
- ❌ Less structured reasoning
- ❌ Lower quality insights

### 4. Incremental Delta Updates

**Decision**: Never rewrite entire playbook, only append/update bullets

**Rationale**:
- ✅ Prevents context collapse (key research finding)
- ✅ Preserves history
- ✅ Faster updates
- ✅ Git-friendly (smaller diffs)

**Alternative Considered**: Full rewrites
- ❌ Risk of context collapse (proven in research)
- ❌ Slower
- ❌ Can lose information

### 5. 20+ Predefined Patterns

**Decision**: Start with 20 patterns across Python, JS, TS

**Rationale**:
- ✅ Covers common languages
- ✅ Includes helpful + harmful patterns
- ✅ Extensible (users can add more)
- ✅ Provides immediate value

**Pattern Selection Criteria**:
- Common in real codebases
- Clear helpful/harmful distinction
- Detectable via regex
- Actionable recommendations

**Alternative Considered**: Learn patterns from scratch
- ❌ Would require much more data
- ❌ Slower to provide value
- ❌ More complex implementation

### 6. Regex-Based Detection

**Decision**: Use regex for pattern matching

**Rationale**:
- ✅ Fast (instant)
- ✅ Works offline
- ✅ No LLM calls needed
- ✅ Deterministic

**Alternative Considered**: AST parsing
- ❌ More complex
- ❌ Language-specific parsers needed
- ❌ Slower
- ✅ More accurate (but overkill for this use case)

### 7. Test Execution for Evidence

**Decision**: Run `npm test` to gather execution feedback

**Rationale**:
- ✅ Provides objective signal (pass/fail)
- ✅ Research emphasizes execution feedback
- ✅ Works without labeled data

**Timeout**: 10 seconds
- Prevents hanging on slow tests

**Alternative Considered**: Require manual labels
- ❌ More user effort
- ❌ Research shows execution feedback sufficient

### 8. PostToolUse Hook

**Decision**: Run ACE cycle after each tool use (code operation)

**Rationale**:
- ✅ Catches patterns immediately
- ✅ Fresh context for reflection
- ✅ Incremental learning

**Alternative Considered**: Batch processing
- ❌ Delays feedback
- ❌ Risk of forgetting context

### 9. SessionEnd Hook for Cleanup

**Decision**: Deduplicate and prune at session end

**Rationale**:
- ✅ One comprehensive cleanup pass
- ✅ More efficient than after each pattern
- ✅ Ensures final playbook is clean

**Alternative Considered**: Cleanup after each pattern
- ❌ More frequent, higher overhead
- ✅ But would keep playbook always clean

### 10. Confidence-Based Organization

**Decision**: Organize playbook by confidence (high/medium/anti-patterns)

**Rationale**:
- ✅ Users prioritize high-confidence patterns
- ✅ Clear visual hierarchy
- ✅ Medium patterns flagged as "verify first"

**Threshold**: 70% for high-confidence
- Based on research benchmarks

**Alternative Considered**: Flat list
- ❌ Harder to prioritize
- ❌ Less actionable

### 11. MCP Integration

**Decision**: Use MCP (Model Context Protocol) for storage + reflection

**Rationale**:
- ✅ Persistent storage (memory-bank)
- ✅ Structured LLM calls (sequential-thinking)
- ✅ Modular architecture
- ✅ Aligns with Claude Code ecosystem

**Alternative Considered**: Local JSON files
- ❌ Would need custom persistence logic
- ❌ Less integrated with Claude Code

### 12. Jest for Testing

**Decision**: Use Jest testing framework

**Rationale**:
- ✅ Popular, well-documented
- ✅ Easy to set up
- ✅ Good test organization

**Coverage**:
- Pattern detection logic
- Curator algorithm (critical)
- Edge cases (0 observations, high similarity, etc.)

### 13. Comprehensive Documentation

**Decision**: Create README, QUICKSTART, research summary, usage guide

**Rationale**:
- ✅ Users understand what/why/how
- ✅ Reference for future development
- ✅ Onboarding for contributors

**Files Created**:
- README.md - Full documentation
- QUICKSTART.md - Step-by-step setup
- docs/ACE_RESEARCH.md - Research summary
- (Now) Serena memories - Implementation details

### 14. Git from Start

**Decision**: Initialize git repository immediately

**Rationale**:
- ✅ Version control from day 1
- ✅ Track changes during development
- ✅ Ready to push to GitHub

**Commit Message Structure**:
- What was built
- Research basis
- Key features
- Performance expectations

## Key Tradeoffs

### 1. Regex vs. AST Parsing
- **Chose**: Regex
- **Tradeoff**: Less accurate, but much faster and simpler

### 2. Predefined vs. Learned Patterns
- **Chose**: Predefined (20+)
- **Tradeoff**: Limited initially, but provides immediate value

### 3. Immediate vs. Batched Updates
- **Chose**: Immediate (after each edit)
- **Tradeoff**: More frequent operations, but fresher learning

### 4. String Similarity vs. Embeddings
- **Chose**: String similarity
- **Tradeoff**: Less sophisticated, but much faster and lighter

## Validation Against Research

✅ **Three-role architecture**: Generator, Reflector, Curator - ✅ Implemented
✅ **Incremental delta updates**: Never full rewrites - ✅ Implemented
✅ **Deterministic curator**: No LLM variance - ✅ Implemented
✅ **Grow-and-refine**: Append, update, deduplicate, prune - ✅ Implemented
✅ **85% similarity threshold**: From research - ✅ Implemented
✅ **30% prune threshold**: From research - ✅ Implemented
✅ **Execution feedback**: Test results - ✅ Implemented
✅ **Comprehensive playbooks**: Not concise summaries - ✅ Implemented

## Future Improvements Considered

### 1. AST-Based Detection
- More accurate pattern matching
- Language-specific parsers
- **Tradeoff**: Much more complex

### 2. Pattern Discovery
- Learn new patterns from code
- Beyond predefined set
- **Tradeoff**: Requires more data, more complex

### 3. Multi-Model Support
- Support Go, Rust, C++, etc.
- **Tradeoff**: Need pattern definitions per language

### 4. Visual Dashboard
- Web UI for pattern analytics
- **Tradeoff**: Additional complexity

### 5. Team Collaboration
- Shared playbooks across team
- Pattern voting/rating
- **Tradeoff**: Requires backend infrastructure

### 6. IDE Integration
- Real-time pattern highlighting
- Inline recommendations
- **Tradeoff**: IDE-specific implementations needed

## Conclusion

Every decision was made based on:
1. ✅ **Research findings** (arXiv:2510.04618v1)
2. ✅ **Practical constraints** (latency, cost, complexity)
3. ✅ **User experience** (immediate value, easy setup)
4. ✅ **Extensibility** (users can add patterns, customize)

The result: A **production-ready plugin** that faithfully implements ACE research with practical engineering choices.
