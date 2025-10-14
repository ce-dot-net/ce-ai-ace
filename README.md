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

1. **Add the ACE marketplace in Claude Code**:
   ```bash
   /plugin marketplace add ce-dot-net/ce-ai-ace
   ```

2. **Install the plugin**:
   ```bash
   /plugin install ace-orchestration@ace-plugin-marketplace
   ```

3. **Restart Claude Code** to activate

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
│  You Code   │ (Generator: You + Claude Code)
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
┌─────────────────────────────┐
│   Reflect 🤔                │
│ (LLM-based Reflector Agent) │
│ • Analyze pattern effectiveness
│ • Extract specific insights
│ • Iterative refinement (max 5 rounds)
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────┐
│   Curate 🔀     │
│ • Deterministic merging (85% similarity)
│ • Generate bullet IDs: [py-00001]
│ • Track helpful/harmful counts
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│ Update Playbook (CLAUDE.md) │
│ • Bulletized structure
│ • ACE sections (STRATEGIES, CODE SNIPPETS, etc.)
│ • Incremental delta updates
└─────────────────────────────┘
```

### Three Roles (ACE Framework)

1. **Generator** - You + Claude Code (existing workflow)
2. **Reflector** - Dedicated LLM agent that analyzes patterns for effectiveness
   - Structured JSON input/output
   - Iterative refinement support (max 5 rounds)
   - Evidence-based insights with specific recommendations
3. **Curator** - Deterministic algorithm (85% similarity threshold)
   - Bulletized structure with IDs: `[domain-NNNNN]`
   - Incremental delta updates (append, update, prune)
   - Tracks helpful/harmful counts per pattern

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
├── .serena/
│   ├── memories/                # Serena MCP knowledge storage (gitignored)
│   └── project.yml              # Serena project configuration
├── agents/
│   ├── reflector.md             # Reflector agent (markdown!)
│   └── reflector-prompt.md      # Reflector prompt template
├── commands/
│   ├── ace-status.md            # /ace-status command
│   ├── ace-patterns.md          # /ace-patterns command
│   ├── ace-clear.md             # /ace-clear command
│   └── ace-force-reflect.md     # /ace-force-reflect command
├── hooks/
│   └── hooks.json               # All 5 hooks (AgentStart, AgentEnd, PreToolUse, PostToolUse, SessionEnd)
├── scripts/
│   ├── ace-cycle.py             # Main ACE orchestration
│   ├── generate-playbook.py     # CLAUDE.md generator
│   ├── playbook-delta-updater.py # Delta update engine
│   ├── embeddings_engine.py     # Semantic embeddings
│   ├── epoch-manager.py         # Multi-epoch training
│   ├── serena-pattern-detector.py # Hybrid AST+regex detection
│   ├── inject-playbook.py       # AgentStart hook
│   ├── analyze-agent-output.py  # AgentEnd hook
│   ├── validate-patterns.py     # PreToolUse hook
│   ├── ace-stats.py             # Statistics utility
│   ├── ace-list-patterns.py     # Pattern listing utility
│   ├── ace-session-end.py       # Session cleanup
│   └── migrate-database.py      # Database migration
├── docs/
│   ├── ACE_RESEARCH.md          # Research paper summary
│   ├── GAP_ANALYSIS.md          # Comprehensive gap analysis
│   └── PHASES_3_5_COMPLETE.md   # Phase 3-5 implementation details
├── tests/
│   ├── test-phase-3-5.py        # Automated test suite
│   ├── MANUAL_TEST.md           # Manual test guide
│   └── TEST_PROMPT.md           # Ready-to-use test prompt
├── CLAUDE.md                     # Auto-generated playbook (gitignored)
└── README.md                     # This file
```

**Important Notes**:
- No `index.js` or JavaScript exports! Claude Code 2.0 plugins are purely declarative (markdown + JSON + Python scripts)
- `CLAUDE.md` is auto-generated by the plugin and should not be manually edited
- `.serena/memories/` stores MCP-based project knowledge (excluded from git)

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

### Serena MCP integration
This plugin uses Serena MCP for knowledge management:
- `.serena/memories/` stores architectural decisions and learning context
- `.serena/project.yml` defines project metadata
- Serena memories are excluded from git (see `.gitignore`)
- To view memories: check `.serena/memories/*.md` files

### Python script errors?
- Ensure Python 3.7+ is installed
- Most scripts use only standard library
- For embeddings: `pip install sentence-transformers` (optional, improves accuracy)

---

## 🆕 Phase 3-5 Features (Latest)

### Phase 3: Delta Updates & Semantic Embeddings ✅
- **Incremental CLAUDE.md updates**: No more full rewrites! Surgical delta updates prevent context collapse
- **Semantic embeddings**: Multi-backend system (OpenAI API, local sentence-transformers, enhanced fallback)
- **Embeddings cache**: Fast lookups with automatic caching (`.ace-memory/embeddings-cache.json`)
- **Research-compliant similarity**: 85% cosine similarity threshold on sentence embeddings

### Phase 4: Multi-Epoch Training ✅
- **Offline training mode**: Revisit cached training data across up to 5 epochs
- **Pattern evolution tracking**: See how patterns improve over time
- **Epoch management**: `python3 scripts/epoch-manager.py start|complete|stats`
- **Training cache**: Automatically stores code/patterns for offline learning

### Phase 5: Serena Integration ✅
- **Hybrid pattern detection**: AST-aware (Serena) + regex (fallback)
- **Symbol-level analysis**: Uses `find_symbol` for accurate detection
- **Reference tracking**: Track pattern usage with `find_referencing_symbols`
- **Serena memories**: Store ACE insights in searchable Serena format

### Complete Hook Lifecycle ✅
- **AgentStart**: Inject CLAUDE.md into agent contexts automatically
- **PreToolUse**: Validate patterns before code is written
- **PostToolUse**: Run ACE cycle after Edit/Write operations
- **AgentEnd**: Analyze agent output for meta-learning
- **SessionEnd**: Cleanup and final playbook generation

**Test the new features**: See `tests/TEST_PROMPT.md` for a comprehensive test scenario!

---

## 🤝 Contributing

Contributions welcome! Areas to improve:
1. **More patterns**: Add patterns for Go, Rust, C++, etc.
2. **Better reflection**: Implement full multi-round iterative refinement
3. **Visualization**: Web UI for pattern analytics
4. **Team sharing**: Share playbooks across teams
5. **Advanced Serena integration**: Full symbolic editing and auto-fixes

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
