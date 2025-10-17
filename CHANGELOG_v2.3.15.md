# ACE v2.3.15 Release Notes

## Critical Fix: Removed Hardcoded Patterns from Offline Training

**Release Date**: 2025-10-17

### 🔧 Bug Fixes

#### Offline Training Architecture Correction

**Issue**: v2.3.14's offline training inadvertently introduced hardcoded pattern matching (regex-based) instead of using agent-based pattern discovery, violating the TRUE ACE architecture from the research paper.

**Root Cause**: Attempted to make offline training "fully automated" by adding `batch_reflect()` function with hardcoded regex patterns for imports, APIs, and architectural patterns.

**Fix**: Removed all hardcoded patterns and restored agent-based discovery:

1. **Removed Hardcoded Patterns**:
   - Deleted `batch_reflect()` with regex patterns for Python, JavaScript, TypeScript
   - No more hardcoded import/API/architecture detection
   - Eliminated keyword matching (e.g., "requests.", "fetch(", "async def")

2. **Restored Agent-Based Discovery**:
   - Offline training now outputs agent invocation requests
   - Uses domain-discoverer agent for pattern discovery
   - Maintains TRUE ACE architecture: patterns discovered by analyzing code, not matching keywords

3. **Documentation Updates**:
   - Updated `/ace-train-offline` command to clarify interactive mode requirement
   - Added `allowed-tools: Task` to command frontmatter
   - Documented that Claude must invoke agents during offline training

### 📚 Research Paper Compliance

Per ACE research paper (arXiv:2510.04618v1):

> "Reflector proposes new bullets based on recent code and test outcomes"

Patterns MUST be discovered by agents analyzing code, NOT by matching predefined keywords.

**What This Means**:

- ✅ **Correct**: Agent reads code → identifies patterns → returns discoveries
- ❌ **Wrong**: Script matches regex → creates pattern objects → stores in database

### 🎯 Offline Training Usage

Offline training now works as follows:

1. Run `/ace-train-offline` command
2. Script outputs agent invocation requests to stderr
3. Claude (you) invokes domain-discoverer agent via Task tool
4. Agent analyzes code and discovers patterns
5. Patterns stored in database
6. Process repeats for all training files across 5 epochs

**Example Flow**:

```
Script: "Please invoke domain-discoverer agent with this code..."
Claude: [Uses Task tool to invoke ace-orchestration:domain-discoverer]
Agent: [Analyzes code, discovers patterns, returns results]
Script: [Stores discovered patterns in database]
```

### 🔄 Architecture Clarification

**Two Modes of Operation**:

1. **Interactive Mode** (via hooks):
   - PostEdit/PostWrite hooks trigger ACE cycle
   - Claude invokes agents via Task tool
   - Full agent-based pattern discovery
   - ✅ Implements TRUE ACE architecture

2. **Batch Mode** (offline training):
   - Requires interactive agent invocation
   - Claude must respond to agent requests
   - Cannot be fully automated without LLM API integration
   - ✅ Also implements TRUE ACE architecture

**Why No Full Automation?**:

True offline training as described in the research paper likely used automated LLM API calls for pattern discovery. Implementing this would require:

- LLM API client (OpenAI, Anthropic, etc.)
- API key management
- Async LLM invocation infrastructure

For now, offline training uses Claude Code's interactive agent invocation, maintaining architectural correctness while being practical for the plugin environment.

### 📝 Files Changed

1. **plugins/ace-orchestration/scripts/offline-training.py**:
   - Removed `batch_reflect()` function with hardcoded patterns
   - Added `batch_reflect_via_agent()` that outputs agent invocation requests
   - Updated comments to clarify TRUE ACE requirements

2. **plugins/ace-orchestration/commands/ace-train-offline.md**:
   - Added `Task` to allowed-tools
   - Documented interactive agent invocation requirement
   - Clarified TRUE ACE architecture expectations

3. **Version bumps**:
   - plugin.json: 2.3.14 → 2.3.15
   - marketplace.json: 2.3.14 → 2.3.15

### 🙏 Acknowledgments

Thanks to the user for catching this violation of TRUE ACE architecture and ensuring we maintain compliance with the research paper.

### 📖 Related Documentation

- ACE Research Paper: arXiv:2510.04618v1
- [ACE_TRUE_ARCHITECTURE.md](docs/ACE_TRUE_ARCHITECTURE.md)
- [ACE_TESTING_GUIDE.md](docs/ACE_TESTING_GUIDE.md)

---

**Previous Version**: v2.3.14 (simplified command patterns)
**Next Steps**: Consider implementing automated LLM API integration for true batch-mode offline training
