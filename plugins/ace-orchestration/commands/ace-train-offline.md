---
description: Run multi-epoch offline training on your codebase to refine patterns
---

Run ACE offline training to learn patterns from your codebase over multiple epochs.

```bash
# Find plugin installation path and run offline training
PLUGIN_PATH=$(find ~/.claude/plugins/marketplaces -name "ace-plugin-marketplace" -type d 2>/dev/null | head -1)

if [ -z "$PLUGIN_PATH" ]; then
  echo "❌ ACE plugin not found. Please install via: /plugin install ace-orchestration@ace-plugin-marketplace"
  exit 1
fi

# Run 5 epochs on all available code (default)
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 "$PLUGIN_PATH/plugins/ace-orchestration/scripts/offline-training.py"
```

This implements the ACE research paper's multi-epoch training (Section 4.1, Table 3).
Adds approximately +2.6% improvement according to the research.
