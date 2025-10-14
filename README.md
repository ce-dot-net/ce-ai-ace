# ACE Orchestration Plugin for Claude Code CLI

**Automatic pattern learning through Agentic Context Engineering (ACE)**

Based on research from Stanford University, SambaNova Systems, and UC Berkeley
📄 Paper: [arXiv:2510.04618v1](https://arxiv.org/abs/2510.04618)

---

## 🎯 What is ACE?

ACE is a framework that improves LLM performance by **evolving contexts** instead of fine-tuning weights. This plugin implements the full ACE cycle for Claude Code CLI, automatically learning from your coding patterns and building a comprehensive playbook in `CLAUDE.md`.

### Key Results from Research
- **+10.6%** improvement on agent tasks
- **+8.6%** on domain-specific reasoning
- **86.9%** reduction in adaptation latency
- **75-84%** reduction in token costs

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ce-ai-ace.git
cd ce-ai-ace

# Install dependencies
npm install

# Optional: Install MCP servers for full functionality
npm run install-mcps
```

### Usage

1. **Activate the plugin** in Claude Code CLI
2. **Start coding** as you normally would
3. **Check `CLAUDE.md`** after each session for learned patterns

That's it! The plugin works automatically in the background.

---

## 🏗️ How It Works

### The ACE Cycle

```
┌─────────────┐
│  You Code   │ (Generator)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Detect Patterns │ (20+ predefined patterns)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Gather Tests   │ (Execution feedback)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Reflect 🤔    │ (Sequential-thinking MCP)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Curate 🔀     │ (Deterministic merging)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Update Playbook │ (CLAUDE.md)
└─────────────────┘
```

### Three Roles

1. **Generator** - You + Claude Code (existing workflow)
2. **Reflector** - LLM via `sequential-thinking` MCP
3. **Curator** - Deterministic algorithm (85% similarity threshold)

---

## 📋 Features

### Pattern Detection
- ✅ **20+ predefined patterns** across Python, JavaScript, TypeScript
- ✅ **Regex-based detection** (fast, no LLM calls)
- ✅ **Automatic language detection** from file extensions

### Pattern Categories
- **Helpful patterns**: TypedDict, async/await, custom hooks, etc.
- **Harmful patterns**: Bare except, var declarations, direct state mutation

### Intelligent Curation
- ✅ **85% similarity threshold** for merging patterns
- ✅ **30% confidence threshold** for pruning (after 10 observations)
- ✅ **Semantic deduplication** using string similarity
- ✅ **No LLM guessing** - pure deterministic algorithm

### Evolving Playbook
- ✅ **Incremental delta updates** (prevents context collapse)
- ✅ **Confidence-based organization** (high/medium/anti-patterns)
- ✅ **Comprehensive insights** (not concise summaries)
- ✅ **Specific recommendations** based on real usage

---

## 🔧 Configuration

Edit `plugin.json` to customize:

```json
{
  "configuration": {
    "similarityThreshold": 0.85,    // Merge threshold (0-1)
    "pruneThreshold": 0.3,          // Prune below 30% confidence
    "minObservations": 10,          // Observations before pruning
    "confidenceThreshold": 0.7,     // High-confidence classification
    "maxPatternsInPlaybook": 50,    // Max patterns to display
    "enableReflection": true,       // Use sequential-thinking MCP
    "logLevel": "info"              // Logging verbosity
  }
}
```

---

## 📊 Pattern Examples

### Python Patterns
- **py-001**: Use TypedDict for configs
- **py-002**: Validate API responses
- **py-003**: Avoid bare except (harmful)
- **py-004**: Use context managers for files
- **py-005**: Use asyncio.gather for parallel requests

### JavaScript Patterns
- **js-001**: Wrap fetch in try-catch
- **js-002**: Use custom hooks for data fetching
- **js-003**: Avoid direct state mutation (harmful)
- **js-004**: Use const for immutable values

### TypeScript Patterns
- **ts-001**: Use interface for object shapes
- **ts-002**: Use type guards
- **ts-003**: Use generics for reusable functions
- **ts-004**: Avoid any type (harmful)

---

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test suite
npm test patternDetector.test.js
npm test curator.test.js
```

---

## 📁 Project Structure

```
ce-ai-ace/
├── config/
│   └── patterns.js              # Pattern definitions
├── lib/
│   ├── patternDetector.js       # Detection engine
│   ├── curator.js               # Deterministic merging
│   ├── ace-utils.js             # MCP communication
│   └── generatePlaybook.js      # CLAUDE.md generator
├── agents/
│   └── reflector-prompt.md      # Reflection prompt
├── hooks/
│   ├── postToolUse.js           # Main ACE cycle
│   └── sessionEnd.js            # Session cleanup
├── tests/
│   ├── patternDetector.test.js
│   └── curator.test.js
├── index.js                     # Plugin entry point
├── plugin.json                  # Plugin manifest
└── package.json
```

---

## 🔬 Research Background

This plugin implements the ACE framework from:

**"Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models"**

*Qizheng Zhang¹, Changran Hu², Shubhangi Upasani², et al.*

¹Stanford University, ²SambaNova Systems, ³UC Berkeley

### Key Innovations

1. **Incremental Delta Updates**: Small, structured changes prevent context collapse
2. **Grow-and-Refine**: Append new, update existing, prune low-confidence
3. **Deterministic Curation**: Algorithmic merging (no LLM variance)
4. **Comprehensive Playbooks**: Dense context > concise summaries

### Results
- AppWorld benchmark: 59.4% (matches top production agent using smaller model)
- Financial reasoning: +8.6% over baselines
- Latency: 82-92% reduction
- Cost: 75-84% reduction

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional pattern definitions
- Support for more languages (Go, Rust, etc.)
- Enhanced reflection prompts
- Performance optimizations

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **Research Paper**: https://arxiv.org/abs/2510.04618
- **Claude Code**: https://claude.com/claude-code
- **Issues**: https://github.com/YOUR_USERNAME/ce-ai-ace/issues

---

## 🙏 Acknowledgments

Built on the groundbreaking ACE research from:
- Stanford University
- SambaNova Systems
- UC Berkeley

Special thanks to the Claude Code team at Anthropic for creating an extensible plugin system.

---

**Happy coding! Watch your CLAUDE.md evolve! 🚀**
