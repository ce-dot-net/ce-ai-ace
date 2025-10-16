---
description: Run multi-epoch offline training on your codebase to refine patterns
allowed-tools: Bash
---

# ACE Offline Training

Run ACE offline training to learn patterns from your codebase over multiple epochs.

This implements the ACE research paper's multi-epoch training (Section 4.1, Table 3).
Adds approximately +2.6% improvement according to the research.

!```bash
# Locate the ACE plugin installation
if [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
  PLUGIN_PATH="$CLAUDE_PLUGIN_ROOT"
else
  PLUGIN_PATH=$(find ~/.claude/plugins/marketplaces -type d -name "ace-orchestration" 2>/dev/null | head -1)
fi

if [ -z "$PLUGIN_PATH" ]; then
  echo "❌ ACE plugin not found"
  exit 1
fi

# Run offline training
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 "$PLUGIN_PATH/scripts/offline-training.py"
```
