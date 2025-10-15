---
description: Run multi-epoch offline training on your codebase to refine patterns
---

Run ACE offline training to learn patterns from your codebase over multiple epochs.

Usage:
```bash
# Run 5 epochs on all available code (default)
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 ${CLAUDE_PLUGIN_ROOT}/scripts/offline-training.py

# Run 3 epochs on test files only
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 ${CLAUDE_PLUGIN_ROOT}/scripts/offline-training.py --epochs 3 --source test-files

# Run on git history
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 ${CLAUDE_PLUGIN_ROOT}/scripts/offline-training.py --source git-history
```

This implements the ACE research paper's multi-epoch training (Section 4.1, Table 3).
Adds approximately +2.6% improvement according to the research.
