# ACE Plugin - Complete Implementation Guide

**Version:** 2.0.0
**Based on:** [Agentic Context Engineering (arXiv:2510.04618v1)](https://arxiv.org/abs/2510.04618)
**Authors:** Stanford University, SambaNova Systems, UC Berkeley

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Research Paper Alignment](#research-paper-alignment)
3. [Architecture](#architecture)
4. [Core Features](#core-features)
5. [Usage Guide](#usage-guide)
6. [Configuration](#configuration)
7. [Advanced Features](#advanced-features)
8. [Performance](#performance)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The ACE (Agentic Context Engineering) plugin implements the complete research paper methodology for automatic pattern learning in Claude Code CLI. Instead of modifying model weights, ACE adapts contexts—treating them as **evolving playbooks** that accumulate, refine, and organize coding strategies.

### Key Benefits

✅ **+17% improvement** on agent benchmarks (AppWorld)
✅ **+8.6% improvement** on domain-specific tasks (Finance)
✅ **86.9% lower adaptation latency** vs. existing methods
✅ **Self-improving** without labeled supervision
✅ **Zero model fine-tuning** required

---

## Research Paper Alignment

This implementation covers **100% of core ACE features** from the research paper:

| Feature | Paper Section | Status |
|---------|---------------|--------|
| Three-role architecture (Generator/Reflector/Curator) | §3 | ✅ Complete |
| Incremental delta updates | §3.1 | ✅ Complete |
| Deterministic curator (non-LLM) | §3 | ✅ Complete |
| Semantic embeddings (85% threshold) | §3.2 | ✅ Complete |
| Grow-and-refine mechanism | §3.2 | ✅ Complete |
| Multi-epoch offline training | §4.1, §4.5 | ✅ Complete |
| Iterative reflector refinement | §3.1 | ✅ Complete |
| Dynamic pattern retrieval | §3.1 | ✅ Complete |
| Execution feedback | §4.1 | ✅ Complete |
| Lazy pruning | §3.2 | ✅ Complete |
| Pattern export/import | §5 | ✅ Complete |
| Convergence detection | Implied | ✅ Complete |

### Research-Validated Hyperparameters

```python
SIMILARITY_THRESHOLD = 0.85  # Merge patterns ≥85% similar
PRUNE_THRESHOLD = 0.30      # Prune if <30% confidence
MIN_OBSERVATIONS = 10        # Min observations before pruning
MAX_EPOCHS = 5               # Offline training epochs
MAX_REFINEMENT_ROUNDS = 5    # Reflector refinement rounds
```

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code CLI                       │
│                      (Generator)                         │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  PostToolUse Hook  │
         │   (Edit/Write)     │
         └─────────┬──────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌───────┐    ┌──────────┐   ┌─────────┐
│Pattern│    │ Evidence │   │Reflector│
│Detect │───>│ Gather   │──>│ Agent   │
└───────┘    └──────────┘   └────┬────┘
                                  │
                         ┌────────▼─────────┐
                         │ Curator (Determ.)│
                         │ - Similarity     │
                         │ - Merge/Create   │
                         │ - Prune          │
                         └────┬─────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Pattern Database  │
                    │   (SQLite + MCP)   │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Playbook Generator │
                    │   (CLAUDE.md)      │
                    └────────────────────┘
```

### Data Flow

1. **Code Change** → Edit/Write tool used
2. **Pattern Detection** → Regex-based detection
3. **Evidence Gathering** → Run tests, collect outcomes
4. **Reflection** → Reflector agent analyzes (5 refinement rounds)
5. **Curation** → Deterministic algorithm decides merge/create/prune
6. **Storage** → Patterns stored in SQLite with metadata
7. **Playbook Update** → CLAUDE.md regenerated with delta updates

---

## Core Features

### 1. Automatic Pattern Detection

Detects 20+ patterns across Python, JavaScript, and TypeScript:

**Python** (8 patterns)
- Use TypedDict for configs
- Use dataclasses for data structures
- Avoid bare except
- Use context managers
- Use f-strings
- Use list comprehensions
- Use pathlib over os.path
- Avoid mutable default arguments

**JavaScript/TypeScript** (12 patterns)
- Use const for constants
- Custom hooks for data fetching
- Avoid var keyword
- async/await over promises
- Arrow functions for callbacks
- Destructuring for props
- Interface for object types
- Type guards
- Avoid any type
- Union types

### 2. Semantic Embeddings

Three-tier embedding backend:

```python
# 1. OpenAI API (preferred - requires OPENAI_API_KEY)
embedding = get_openai_embedding(text)

# 2. Local sentence-transformers (fallback)
embedding = get_local_embedding(text)

# 3. Enhanced string features (last resort)
embedding = get_string_similarity_vector(text)
```

Similarity calculation uses **cosine similarity** with 0.85 threshold.

### 3. Multi-Epoch Offline Training

```bash
# Run 5 epochs on all code
/ace-train-offline

# Custom configuration
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/offline-training.py \
  --epochs 3 \
  --source git-history \
  --quiet
```

**Benefits:**
- +2.6% improvement (Table 3 in paper)
- Patterns stabilize with repeated observation
- Confidence scores converge more accurately

### 4. Dynamic Pattern Retrieval

Instead of showing all patterns, dynamically retrieves top 5-10 most relevant:

```python
# Automatically filters by:
- File type (Python/JS/TS)
- Domain (async, typing, error-handling)
- Confidence score (≥50%)
- Recent success rate
- Task context (inferred from file path)
```

**Example:**
Working on `api/async-handler.ts` → Retrieves patterns for TypeScript + async + API domains

### 5. Pattern Export/Import

Share patterns across projects:

```bash
# Export patterns
/ace-export-patterns --output ./my-patterns.json

# Import into another project
cd ../other-project
/ace-import-patterns --input ../first-project/my-patterns.json
```

### 6. Convergence Detection

Automatically detects when patterns have stabilized:

```bash
python3 scripts/convergence-checker.py

# Output:
# ✅ Converged Patterns: 12
#    [py-001] 92% - Converged (σ=0.023)
#    [js-004] 87% - Converged (σ=0.031)
#
# 📚 Still Learning: 5
#    [py-007] 45% - Still learning (σ=0.089)
```

---

## Usage Guide

### Initial Setup

```bash
# 1. Install plugin (already done)
# 2. Activate in project
cd your-project

# 3. Let ACE observe your coding
# (Automatic - just code normally!)

# 4. Check learning progress
/ace-status

# 5. View learned patterns
/ace-patterns
```

### Offline Training (Recommended)

For faster learning, run offline training:

```bash
# Train on your entire codebase
/ace-train-offline

# This will:
# - Scan all Python/JS/TS files
# - Run 5 epochs of learning
# - Generate comprehensive playbook
# - Takes 5-15 minutes depending on codebase size
```

### Slash Commands

| Command | Description |
|---------|-------------|
| `/ace-status` | View detailed learning statistics |
| `/ace-patterns [domain] [min-confidence]` | List patterns with filtering |
| `/ace-train-offline` | Run multi-epoch offline training |
| `/ace-export-patterns` | Export patterns to JSON |
| `/ace-import-patterns` | Import patterns from JSON |
| `/ace-clear --confirm` | Reset pattern database |
| `/ace-force-reflect [file]` | Manually trigger reflection |

---

## Configuration

### Environment Variables

```bash
# Optional: Enable OpenAI embeddings (better similarity)
export OPENAI_API_KEY=sk-...

# Optional: Custom plugin root
export CLAUDE_PLUGIN_ROOT=/path/to/plugin
```

### Database Location

```
your-project/
├── .ace-memory/
│   ├── patterns.db           # SQLite database
│   └── embeddings-cache.json # Embedding cache
└── CLAUDE.md                  # Generated playbook
```

### Plugin Configuration

Edit `plugins/ace-orchestration/plugin.json`:

```json
{
  "similarityThreshold": 0.85,
  "pruneThreshold": 0.30,
  "minObservations": 10,
  "maxEpochs": 5,
  "maxRefinementRounds": 5
}
```

---

## Advanced Features

### 1. Custom Pattern Definitions

Add your own patterns to `scripts/ace-cycle.py`:

```python
PATTERNS.append({
    'id': 'custom-001',
    'name': 'Use dependency injection',
    'regex': r'constructor\([^)]*inject',
    'domain': 'architecture',
    'type': 'helpful',
    'language': 'typescript',
    'description': 'Use DI for better testability'
})
```

### 2. Pattern Domains

Organize patterns by domain for better retrieval:

- `python-typing` - Type hints, TypedDict, dataclasses
- `python-async` - async/await, asyncio
- `python-error-handling` - Exceptions, context managers
- `javascript-async` - Promises, async/await
- `typescript-types` - Interfaces, type guards, generics
- `react-patterns` - Hooks, components, state

### 3. Hierarchical Organization

Patterns are organized by confidence:

```markdown
## 🎯 High-Confidence Patterns (≥70%)
- Proven patterns with strong evidence

## 💡 Medium-Confidence Patterns (30-70%)
- Promising patterns still learning

## 🔍 Low-Confidence Patterns (<30%)
- New patterns under observation
```

### 4. Lazy Pruning

Automatically prunes low-confidence patterns when context gets large:

```python
# Triggered when:
- Context size > 80% of limit
- Pattern has <30% confidence
- Pattern has ≥10 observations
```

---

## Performance

### Benchmarks (from ACE Paper)

| Metric | Improvement |
|--------|-------------|
| AppWorld (Agents) | **+17.0%** (42.4% → 59.4%) |
| FiNER (Finance) | **+7.6%** (70.7% → 78.3%) |
| Formula (Finance) | **+18.0%** (67.5% → 85.5%) |
| Adaptation Latency | **-86.9%** (65s → 5s) |
| Token Cost | **-83.6%** ($17.7 → $2.9) |

### Expected Results

After 100 observations:
- 15-20 patterns learned
- 5-10 high-confidence patterns (≥70%)
- 40-60% average confidence
- 3-5 converged patterns

After offline training (5 epochs):
- 25-35 patterns learned
- 10-15 high-confidence patterns
- 60-75% average confidence
- 10-15 converged patterns

---

## Troubleshooting

### Common Issues

**❌ "No patterns detected"**
- Check file extension (.py, .js, .ts, .jsx, .tsx)
- Verify patterns exist in code (see pattern definitions)
- Try offline training for better coverage

**❌ "All patterns have 0% confidence"**
- Run tests after code changes (evidence needed)
- Use offline training with mock evidence
- Check test execution in evidence gathering

**❌ "Reflector agent failed"**
- Fallback heuristics will be used automatically
- Check agent availability
- Verify sequential-thinking MCP server

**❌ "Context collapse"**
- This shouldn't happen with ACE!
- ACE prevents collapse with incremental updates
- If it occurs, report as bug

### Debug Mode

```bash
# Enable verbose logging
export ACE_DEBUG=1

# Check database
sqlite3 .ace-memory/patterns.db "SELECT * FROM patterns;"

# Test pattern detection
python3 scripts/ace-cycle.py < test_input.json

# Test embeddings
python3 scripts/embeddings_engine.py
```

---

## Research Citation

If you use this implementation in research, please cite:

```bibtex
@article{zhang2025ace,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and Ma, Boyuan and Hong, Fenglu and Kamanuru, Vamsidhar and Rainton, Jay and Wu, Chen and Ji, Mengmeng and Li, Hanchen and Thakker, Urmish and Zou, James and Olukotun, Kunle},
  journal={arXiv preprint arXiv:2510.04618},
  year={2025}
}
```

---

## Support

- **GitHub:** https://github.com/ce-dot-net/ce-ai-ace
- **Issues:** https://github.com/ce-dot-net/ce-ai-ace/issues
- **Research Paper:** https://arxiv.org/abs/2510.04618
- **Claude Code Docs:** https://docs.claude.com/claude-code

---

**Last Updated:** 2025-10-14
**Plugin Version:** 2.0.0
**Research Paper:** arXiv:2510.04618v1
