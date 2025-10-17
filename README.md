# ACE Plugin for Claude Code CLI

![Version](https://img.shields.io/badge/version-2.3.26-blue) ![License](https://img.shields.io/badge/license-MIT-green) [![Research](https://img.shields.io/badge/arXiv-2510.04618-red)](https://arxiv.org/abs/2510.04618)

**Automatic Pattern Learning through Agentic Context Engineering**

Based on research from Stanford University, SambaNova Systems, and UC Berkeley ([arXiv:2510.04618v1](https://arxiv.org/abs/2510.04618))

---

## 🎯 What is ACE?

ACE (Agentic Context Engineering) is a Claude Code plugin that **automatically learns from your coding patterns** and builds a comprehensive, evolving playbook (`CLAUDE.md`) to improve your development workflow.

Instead of fine-tuning models or manually curating prompts, ACE:
- **Discovers patterns** through agent-based analysis (Python, JavaScript, TypeScript)
- **Learns from feedback** through Generator helpful/harmful tagging
- **Self-improves** patterns based on actual usage effectiveness
- **Curates knowledge** deterministically (research-backed 85% similarity threshold)
- **Grows a playbook** that evolves with your codebase

### Research-Backed Results
- **+17%** improvement on agent benchmarks (AppWorld: 42.4% → 59.4%)
- **+8.6%** improvement on domain-specific tasks (Finance)
- **86.9%** lower adaptation latency vs. existing methods
- **83.6%** token cost reduction ($17.7 → $2.9)
- **Prevents context collapse** through incremental delta updates

### ✅ 100% Research Paper Coverage
This implementation covers **all core ACE features** from the research paper (arXiv:2510.04618):
- Three-role architecture (Generator/Reflector/Curator)
- **Full iterative refinement** (up to 5 rounds with convergence detection)
- Incremental delta updates with grow-and-refine mechanism
- Semantic embeddings with 85% similarity threshold
- Multi-epoch offline training
- Dynamic pattern retrieval
- Convergence detection
- Pattern export/import for cross-project learning
- Lazy pruning for context management

---

## 🚀 Quick Start

### Prerequisites

**uvx** (Python package runner) must be installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew (macOS)
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**That's it!** No Python packages needed - uvx handles everything.

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

**That's it!** The plugin automatically:
- ✅ Installs required MCPs (ChromaDB, Serena) via uvx
- ✅ **Smart Serena detection** - Uses global Serena if installed, otherwise uses bundled version
- ✅ Installs all Python dependencies (chromadb, sentence-transformers, scikit-learn)
- ✅ Sets up hooks (all 5 lifecycle hooks)
- ✅ Creates `.ace-memory/` directory
- ✅ Initializes pattern database

**No manual `install.sh` required!** MCPs and all dependencies are auto-managed via uvx.

**🔧 Smart Serena Detection (NEW in v2.3.0)**
ACE intelligently handles Serena MCP:
- If you have global `serena` MCP → ACE uses it (no conflicts!)
- If no global Serena → ACE uses bundled `serena-ace`
- Zero configuration required - works automatically
- Eliminates tool use concurrency errors (API Error 400)

### 📦 Dependencies (Auto-Managed by uvx)

All Python dependencies are automatically installed and managed by uvx (no pip install needed!):
- `chromadb>=1.0.16` - Vector database for persistent embeddings
- `sentence-transformers` - Semantic embedding model (all-MiniLM-L6-v2)
- `scikit-learn` - Cosine similarity calculations

**First run**: Downloads ~400MB of dependencies (one-time, ~10-15 seconds)
**Subsequent runs**: Instant (uses uvx cache)

📖 **See [DEPENDENCIES.md](docs/DEPENDENCIES.md)** for complete explanation of how dependency management works!

### Usage

**📖 NEW: [Complete Usage Guide](docs/USAGE_GUIDE.md)** - Learn when and how to use ACE on new vs existing projects!

#### Quick Setup (Choose One)

**Existing Codebase** (Recommended):
```bash
/ace-train-offline  # Scans entire codebase, runs 5 epochs (~2-5 min)
```

**New Project** (Start from scratch):
- Just start coding! ACE learns automatically as you write code.

**Team Patterns** (Import from another project):
```bash
/ace-import-patterns --input ./patterns.json --strategy smart
```

#### After Setup

The plugin works **100% automatically**:
1. Edit code in Python, JavaScript, or TypeScript
2. ACE detects patterns and analyzes effectiveness
3. Check `specs/playbooks/` to see learned patterns (or `CLAUDE.md` for Claude Code CLI format)
4. Use `/ace-status` to view learning statistics

**Read the [Usage Guide](docs/USAGE_GUIDE.md) for best practices, performance expectations, and troubleshooting!**

---

## 🏗️ How It Works

### The ACE Cycle

```
┌─────────────┐
│  You Code   │ (Generator: You + Claude Code)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Discover Patterns 🔍                │
│ (Agent-based - NO hardcoded!)       │
│ • Reflector analyzes raw code       │
│ • Identifies imports, APIs, patterns│
│ • Discovers from YOUR codebase      │
└──────┬──────────────────────────────┘
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
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Generator Feedback Loop 🔄      │
│ (NEW in v2.3.10)                 │
│ • Tag bullets as helpful/harmful│
│ • Increment counters            │
│ • Recalculate confidence        │
│ • Patterns self-improve! ✨     │
└─────────────────────────────────┘
```

### Three Roles (ACE Framework)

1. **Generator** - You + Claude Code (existing workflow)
2. **Reflector** - Dedicated LLM agent that analyzes patterns for effectiveness
   - Single agent (`reflector`) with iterative refinement capability (`reflector-prompt`)
   - Structured JSON input/output
   - **Full iterative refinement** (up to 5 rounds with convergence detection)
   - Progressive confidence increases (0.80 → 0.95 over rounds)
   - Evidence-based insights with specific recommendations
   - No fallback heuristics (acknowledged limitation per research paper Appendix B)
3. **Curator** - Deterministic algorithm (85% similarity threshold)
   - Bulletized structure with IDs: `[domain-NNNNN]`
   - Incremental delta updates (append, update, prune)
   - Tracks helpful/harmful counts per pattern
   - Uses semantic embeddings (ChromaDB) for similarity calculation

---

## ✨ Features

### Agent-Based Pattern Discovery ⭐ NEW (v2.3.10)
TRUE ACE architecture - patterns discovered from YOUR code:
- **No hardcoded keywords** - Reflector agent analyzes raw code
- **Discovers actual patterns** - imports, APIs, architectural choices
- **Codebase-specific** - learns what YOU actually use
- **Python, JavaScript, TypeScript** - multi-language support
- **Examples**: subprocess usage, pathlib operations, SQLite queries

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

### Dynamic Pattern Retrieval ⭐ NEW
Context-aware playbook injection (ACE paper §3.1):
- Automatically filters patterns by file type (Python/JS/TS)
- Domain-aware selection (async, typing, error-handling)
- Relevance scoring based on confidence and success rate
- Returns top 5-10 most relevant patterns instead of full playbook
- Reduces token usage while maintaining effectiveness

### Multi-Epoch Offline Training ⭐ NEW
Research-validated training mode (ACE paper §4.1):
- Scan entire codebase for training examples
- Run 1-5 epochs for pattern stabilization
- +2.6% improvement from repeated observation (paper Table 3)
- Supports git history and test file analysis
- Convergence detection shows when patterns have stabilized

### Pattern Export/Import ⭐ NEW
Cross-project learning (ACE paper §5):
- Export patterns to JSON with full metadata
- Import with smart merging (curator-based)
- Share patterns across teams and projects
- Transfer knowledge between codebases
- Three merge strategies: smart, overwrite, skip-existing

### Convergence Detection ⭐ NEW
Know when patterns have stabilized:
- Tracks confidence variance over observations (σ < 0.05)
- Requires minimum 20 observations for convergence
- Command: `python3 scripts/convergence-checker.py`
- Shows converged, learning, and insufficient-data patterns
- Helps identify which patterns are ready for production use

### Evolving Playbooks
ACE generates playbooks in two formats:

**spec-kit format** (`specs/` - committed to git):
- Human-readable, version-controlled
- Hierarchical structure per pattern
- Team-wide synchronization
- Cross-project sharing

**Claude Code CLI format** (`CLAUDE.md` - auto-generated):
- Optimized for Claude Code context injection
- Single-file bulletized format
- Auto-generated from `specs/`

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

### `/ace-train-offline` ⭐ NEW
Run multi-epoch offline training on your entire codebase:
```bash
/ace-train-offline              # Run 5 epochs on all code
```
This implements the ACE paper's offline training mode for +2.6% improvement. Scans your codebase and runs multiple learning epochs for better pattern stabilization.

### `/ace-export-patterns` ⭐ NEW
Export learned patterns to JSON for sharing across projects:
```bash
/ace-export-patterns --output ./my-patterns.json
```
Share your learned patterns with teammates or transfer to another project.

### `/ace-import-patterns` ⭐ NEW
Import patterns from another project:
```bash
/ace-import-patterns --input ./patterns.json --strategy smart
```
Merge strategies: `smart` (curator-based), `overwrite`, or `skip-existing`.

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

## 🏛️ Architecture: Dual Storage System

ACE uses a **dual storage architecture** for optimal learning and human usability:

### SQLite Database (`.ace-memory/` - gitignored)
**Purpose**: Learning engine and pattern tracking
- Pattern observations and confidence scores
- Insights from Reflector agent
- Test results and execution feedback
- Multi-epoch training history
- Semantic embeddings cache

### spec-kit Playbooks (`specs/` - committed to git)
**Purpose**: Human-readable, version-controlled documentation
- `specs/memory/constitution.md` - High-confidence principles (≥70%)
- `specs/playbooks/NNN-domain/` - Individual pattern directories
  - `spec.md` - Pattern definition with metadata
  - `plan.md` - Technical implementation approach
  - `insights.md` - Reflector analysis history

**Why both?**
- **SQLite**: Fast queries, statistical analysis, ML operations
- **spec-kit**: Human-readable, git-friendly, shareable, AI agent compatible

**Benefits**:
- ✅ Version control pattern evolution
- ✅ Team-wide synchronization
- ✅ Cross-project knowledge transfer
- ✅ Git-based offline training (ACE learns from ACE!)
- ✅ Human review and understanding
- ✅ Works with any AI coding agent

---

## 📁 Project Structure

```
ce-ai-ace/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace config
├── plugins/
│   └── ace-orchestration/       # ⭐ Plugin implementation
│       ├── plugin.json          # Plugin metadata + MCP config (auto-installs!)
│       ├── commands/            # Slash commands
│       ├── hooks/               # Lifecycle hooks
│       ├── agents/              # Reflector agent
│       ├── scripts/             # Python scripts
│       ├── specs/               # Playbook specs
│       └── tests/               # Test files
├── .serena/
│   ├── memories/                # Serena MCP knowledge storage (gitignored)
│   └── project.yml              # Serena project configuration
├── specs/                        # ⭐ NEW: spec-kit playbooks (committed!)
│   ├── memory/
│   │   └── constitution.md      # High-confidence principles
│   ├── playbooks/
│   │   ├── 001-python-io/       # Pattern: Use pathlib
│   │   │   ├── spec.md
│   │   │   ├── plan.md
│   │   │   └── insights.md
│   │   └── 002-python-strings/  # Pattern: Use f-strings
│   └── README.md                # Playbook documentation
├── docs/
│   ├── ACE_RESEARCH.md          # Research paper summary
│   ├── ACE_IMPLEMENTATION_GUIDE.md # Complete implementation guide ⭐ NEW
│   ├── EMBEDDINGS_REVIEW.md     # Embeddings implementation vs paper ⭐ NEW
│   ├── DOMAIN_DISCOVERY_REVIEW.md # Domain discovery vs paper ⭐ NEW
│   ├── TROUBLESHOOTING.md       # MCP conflicts and common issues ⭐ NEW
│   ├── SPECKIT_MIGRATION.md     # spec-kit integration guide ⭐ NEW
│   ├── GAP_ANALYSIS.md          # Comprehensive gap analysis
│   ├── PHASES_3_5_COMPLETE.md   # Phase 3-5 implementation details
│   ├── INSTALL.md               # Installation guide
│   ├── QUICKSTART.md            # Quick start guide
│   └── DIAGNOSTIC_PROMPT.md     # Diagnostic prompt for testing
├── tests/
│   ├── test-phase-3-5.py        # Automated test suite
│   ├── MANUAL_TEST.md           # Manual test guide
│   ├── TEST_PROMPT.md           # Ready-to-use test prompt
│   ├── TEST_PROMPT_FOR_USER.md  # User test scenarios
│   └── CONSUMER_TEST_PROMPT.md  # Consumer test prompt
├── CLAUDE.md                     # Auto-generated (for Claude Code CLI)
└── README.md                     # This file
```

**Important Notes**:
- No `index.js` or JavaScript exports! Claude Code 2.0 plugins are purely declarative (markdown + JSON + Python scripts)
- `specs/` is **committed to git** for version control and team sharing (⭐ NEW)
- `.ace-memory/` is **gitignored** (local learning state)
- `CLAUDE.md` is **auto-generated** for Claude Code CLI context injection
- `.serena/memories/` stores MCP-based project knowledge (excluded from git)

**New in this release**: spec-kit integration! ACE now generates human-readable, git-friendly playbooks in `specs/` alongside the `CLAUDE.md` format for Claude Code CLI.

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
3. Check plugin installed at `~/.claude/plugins/marketplaces/ace-plugin-marketplace/`

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

## 🤝 Contributing

Contributions welcome! Areas to improve:
1. **More patterns**: Add patterns for Go, Rust, C++, etc.
2. **Visualization**: Web UI for pattern analytics
3. **Team sharing**: Enhanced cross-team playbook synchronization
4. **Advanced Serena integration**: Full symbolic editing and auto-fixes
5. **Performance profiling**: Track pattern application impact on code quality

---

## 📄 License

MIT License - See LICENSE file for details

---

## 📚 Learn More

- **📖 Usage Guide**: [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md) - When and how to use ACE on your projects
- **📖 Dependencies**: [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) - How zero-setup dependency management works ⭐ NEW
- **📖 ACE Implementation Guide**: [docs/ACE_IMPLEMENTATION_GUIDE.md](docs/ACE_IMPLEMENTATION_GUIDE.md) - Complete guide with 100% research paper coverage
- **📖 Embeddings Architecture**: [docs/EMBEDDINGS_ARCHITECTURE.md](docs/EMBEDDINGS_ARCHITECTURE.md) - Technical architecture with ChromaDB caching
- **📖 Embeddings Review**: [docs/EMBEDDINGS_REVIEW.md](docs/EMBEDDINGS_REVIEW.md) - Claude-native semantic analysis vs research paper
- **📖 Domain Discovery Review**: [docs/DOMAIN_DISCOVERY_REVIEW.md](docs/DOMAIN_DISCOVERY_REVIEW.md) - Bottom-up taxonomy vs research paper
- **📖 Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - MCP conflicts and solutions
- **Research Paper**: https://arxiv.org/abs/2510.04618
- **ACE Research Summary**: [docs/ACE_RESEARCH.md](docs/ACE_RESEARCH.md)
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **Plugin Documentation**: https://docs.claude.com/en/docs/claude-code/plugins

---

## 📦 Releases

View the [full changelog](CHANGELOG.md) for detailed version history.

**Latest Release**: [v2.3.10](https://github.com/ce-dot-net/ce-ai-ace/releases/tag/v2.3.10) (October 2025)
- **TRUE ACE Architecture** - Agent-based pattern discovery (no hardcoded keywords!)
- **Generator Feedback Loop** - Patterns self-improve through helpful/harmful tagging
- **Confidence with Feedback** - New formula incorporates usage effectiveness
- **Complete Documentation** - Architecture guide, testing guide, comprehensive changelog
- **Breaking Change**: Removed hardcoded pattern detection for true agent-based discovery

**Previous Releases**: [GitHub Releases](https://github.com/ce-dot-net/ce-ai-ace/releases)

---

**Built with Claude Code 2.0 • Powered by Sonnet 4.5 • Research from Stanford/SambaNova/UC Berkeley**

🚀 **Start coding and watch your playbook evolve!**
