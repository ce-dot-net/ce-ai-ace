# ACE Pattern Learning MCP Server

**Agentic Context Engineering** - Self-improving context optimization based on [Stanford/SambaNova/UC Berkeley research](https://arxiv.org/abs/2510.04618).

## Overview

This MCP server implements the ACE (Agentic Context Engineering) framework, which treats contexts as evolving playbooks that accumulate, refine, and organize strategies through:

- **Generator**: Produces reasoning trajectories (Claude Code native)
- **Reflector**: Analyzes code and discovers patterns via LLM sampling
- **Curator**: Merges/prunes patterns with 85% semantic similarity threshold
- **Incremental Delta Updates**: Structured, localized context modifications
- **Grow-and-Refine**: Balances expansion with redundancy control

## Features

✅ **Research-Compliant**: Implements all components from ACE paper
✅ **No External LLM**: Uses Claude Code's configured Claude API via sampling
✅ **Pure JavaScript ML**: Embeddings via `@xenova/transformers`
✅ **Fast Storage**: SQLite + vector index for semantic search
✅ **Configurable**: Local, GitHub, or remote storage backends
✅ **Offline Training**: Multi-epoch pattern refinement
✅ **Online Adaptation**: Real-time pattern discovery via hooks

## Installation

```bash
# Via npx (recommended)
npx ace-pattern-learning

# Or install globally
npm install -g ace-pattern-learning
ace-pattern-learning

# Or local development
git clone <repo>
cd mcp-servers/ace-pattern-learning
npm install
npm run build
npm link
```

## Usage

### With Claude Code Plugin

The ACE orchestration plugin automatically configures this MCP server:

```json
{
  "mcpServers": {
    "ace": {
      "command": "npx",
      "args": ["ace-pattern-learning"],
      "env": {
        "ACE_STORAGE_PATH": ".ace-memory/patterns.db"
      }
    }
  }
}
```

### Available Tools

- `ace_reflect(file_path, code, language)` - Analyze code and discover patterns
- `ace_train_offline(epochs, source)` - Multi-epoch offline training
- `ace_get_patterns(domain?, min_confidence?)` - Retrieve learned patterns
- `ace_get_playbook(task_hint?)` - Get formatted context for current task
- `ace_status()` - View learning statistics
- `ace_clear(confirm)` - Reset pattern database

### Available Resources

- `ace://patterns/all` - All patterns with metadata
- `ace://patterns/{domain}` - Patterns for specific domain
- `ace://playbook/current` - Current playbook context
- `ace://constitution` - High-confidence principles (≥70%)

## Architecture

```
ACE MCP Server (TypeScript)
├── Storage Layer
│   ├── SQLite (better-sqlite3) - Structured pattern data
│   ├── Embeddings (@xenova/transformers) - Semantic similarity
│   └── Vector Index (hnswlib-node) - Fast retrieval
│
├── Core Algorithms
│   ├── Reflector - Pattern discovery via sampling
│   ├── Curator - Merge/prune with 85% threshold
│   └── Retrieval - Semantic search for relevant patterns
│
└── MCP Interface
    ├── Tools - Callable operations
    ├── Resources - Data access
    └── Sampling - LLM invocation via Claude Code
```

## Configuration

```json
{
  "storage": {
    "type": "local",
    "path": ".ace-memory/patterns.db"
  },
  "ace": {
    "similarity_threshold": 0.85,
    "confidence_threshold_high": 0.70,
    "confidence_threshold_medium": 0.30,
    "max_refinement_rounds": 5,
    "deduplication_strategy": "lazy",
    "batch_size": 5
  }
}
```

## Research Paper

Based on "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models" by Zhang et al. (2025).

- Paper: https://arxiv.org/abs/2510.04618
- GitHub: https://github.com/ce-dot-net/ce-ai-ace

## License

MIT
