---
description: Run multi-epoch offline training on your codebase to refine patterns
allowed-tools: Bash
---

# ACE Offline Training

Run ACE offline training to learn patterns from your codebase over multiple epochs.

This implements the ACE research paper's multi-epoch training (Section 4.1, Table 3).
Adds approximately +2.6% improvement according to the research.

Run the offline training script from the ace-orchestration plugin:

```bash
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 plugins/ace-orchestration/scripts/offline-training.py
```
