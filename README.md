# ACE Plugin for Claude Code CLI

**Automatic Pattern Learning through Agentic Context Engineering**

Based on research from Stanford University, SambaNova Systems, and UC Berkeley ([arXiv:2510.04618v1](https://arxiv.org/abs/2510.04618))

---

## 🎯 What is ACE?

ACE (Agentic Context Engineering) is a Claude Code plugin that **automatically learns from your coding patterns** and builds a comprehensive, evolving playbook (`CLAUDE.md`) to improve your development workflow.

Instead of fine-tuning models or manually curating prompts, ACE:
- **Detects patterns** in your code automatically (Python, JavaScript, TypeScript)
- **Analyzes effectiveness** using test results and execution feedback
- **Curates knowledge** deterministically (research-backed 85% similarity threshold)
- **Grows a playbook** that evolves with your codebase

### Research-Backed Results
- **+10-17%** accuracy improvement on complex tasks
- **82-92%** latency reduction vs. traditional approaches
- **75-84%** cost reduction
- **Prevents context collapse** through incremental delta updates

---

## 🚀 Quick Start

### Installation

1. **Push this repo to GitHub** (if not already):
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/ce-ai-ace.git
   git push -u origin main
   ```

2. **Add marketplace in Claude Code**:
   ```bash
   /plugin marketplace add YOUR_USERNAME/ce-ai-ace
   ```

3. **Install the plugin**:
   ```bash
   /plugin install ace-orchestration@ace-plugin-marketplace
   ```

4. **Restart Claude Code** to activate

### Usage

The plugin works **100% automatically**:
1. Edit code in Python, JavaScript, or TypeScript
2. ACE detects patterns and analyzes effectiveness
3. Check `CLAUDE.md` to see your evolving playbook
4. Use `/ace-status` to view learning statistics

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

## ✨ Features

### Automatic Pattern Detection
20+ built-in patterns for Python, JavaScript, TypeScript:
- **Python**: TypedDict, dataclasses, f-strings, list comprehensions, context managers
- **JavaScript**: custom hooks, async/await, arrow functions, destructuring
- **TypeScript**: interfaces, type guards, union types
- **Anti-patterns**: bare except, var keyword, any type

### Intelligent Reflection
The **Reflector agent** analyzes:
- Was the pattern applied correctly?
- Did it contribute to success or failure?
- What specific insights can we learn?
- When should this pattern be used?

### Deterministic Curation
Research-proven algorithm (NO LLM variance):
- **85% similarity threshold** for merging patterns
- **30% confidence threshold** for pruning
- **10 minimum observations** before pruning
- Prevents context collapse through incremental updates

### Evolving Playbook
`CLAUDE.md` automatically updates with:
- High-confidence patterns (≥70%)
- Medium-confidence patterns (30-70%)
- Anti-patterns to avoid
- Specific, actionable insights
- Evidence-based recommendations

---

## 💡 Slash Commands

### `/ace-status`
View comprehensive learning statistics:
- Total patterns learned
- Success rates by domain
- Top confident patterns
- Patterns that may be pruned

### `/ace-patterns [domain] [min-confidence]`
List learned patterns with optional filtering:
```bash
/ace-patterns                    # All patterns
/ace-patterns python             # Only Python patterns
/ace-patterns javascript 0.7     # JS patterns with ≥70% confidence
```

### `/ace-force-reflect [file]`
Manually trigger reflection on a file:
```bash
/ace-force-reflect               # Analyze last edited file
/ace-force-reflect src/app.py    # Analyze specific file
```

### `/ace-clear --confirm`
Reset pattern database (with backup):
```bash
/ace-clear          # Show warning
/ace-clear --confirm # Actually reset
```

---

## 🔧 Configuration

The plugin works out-of-the-box with research-backed defaults:

- **Similarity threshold**: 0.85 (85%)
- **Prune threshold**: 0.30 (30%)
- **Minimum observations**: 10
- **Confidence threshold**: 0.70 (70% for "high confidence")

These are hardcoded in `scripts/ace-cycle.py` based on research findings. To customize, edit:
```python
SIMILARITY_THRESHOLD = 0.85  # 85% similarity for merging
PRUNE_THRESHOLD = 0.30       # 30% minimum confidence
MIN_OBSERVATIONS = 10        # Minimum observations before pruning
```

---

## 📁 Project Structure

```
ce-ai-ace/
├── .claude-plugin/
│   ├── plugin.json              # Plugin metadata
│   └── marketplace.json         # Marketplace config
├── agents/
│   └── reflector.md             # Reflector agent (markdown!)
├── commands/
│   ├── ace-status.md            # /ace-status command
│   ├── ace-patterns.md          # /ace-patterns command
│   ├── ace-clear.md             # /ace-clear command
│   └── ace-force-reflect.md     # /ace-force-reflect command
├── hooks/
│   └── hooks.json               # PostToolUse + SessionEnd hooks
├── scripts/
│   ├── ace-cycle.py             # Main ACE orchestration
│   ├── generate-playbook.py     # CLAUDE.md generator
│   ├── ace-stats.py             # Statistics utility
│   ├── ace-list-patterns.py     # Pattern listing utility
│   └── ace-session-end.py       # Session cleanup
├── docs/
│   └── ACE_RESEARCH.md          # Research paper summary
└── README.md                     # This file
```

**Note**: No `index.js` or JavaScript exports! Claude Code 2.0 plugins are purely declarative (markdown + JSON + Python scripts).

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

## 🐛 Troubleshooting

### Plugin not loading?
1. Check: `/plugin` - Should show ace-orchestration
2. Restart Claude Code
3. Check `.claude-plugin/plugin.json` exists

### No patterns detected?
- Plugin only detects: `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files
- Check console for "🔄 ACE: Starting reflection cycle..."
- If silent, hooks may not be registered

### CLAUDE.md not updating?
- Check `.ace-memory/` directory exists
- Run `/ace-status` to verify patterns are being learned
- Check for errors in Claude Code console

### Python script errors?
- Ensure Python 3.7+ is installed
- Scripts use only standard library (no pip install needed)

---

## 🤝 Contributing

Contributions welcome! Areas to improve:
1. **More patterns**: Add patterns for Go, Rust, C++, etc.
2. **Better reflection**: Integrate with better LLM reflection mechanisms
3. **Semantic embeddings**: Replace string similarity with embeddings
4. **Visualization**: Web UI for pattern analytics
5. **Team sharing**: Share playbooks across teams

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📚 Learn More

- **Research Paper**: https://arxiv.org/abs/2510.04618
- **ACE Research Summary**: [docs/ACE_RESEARCH.md](docs/ACE_RESEARCH.md)
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **Plugin Documentation**: https://docs.claude.com/en/docs/claude-code/plugins

---

**Built with Claude Code 2.0 • Powered by Sonnet 4.5 • Research from Stanford/SambaNova/UC Berkeley**

🚀 **Start coding and watch your playbook evolve!**
