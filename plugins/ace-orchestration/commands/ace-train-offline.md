---
description: Run multi-epoch offline training on your codebase to refine patterns
allowed-tools: Bash, Task
---

# ACE Offline Training

Run ACE offline training to learn patterns from your codebase over multiple epochs.

This implements the ACE research paper's multi-epoch training (Section 4.1, Table 3).
Adds approximately +2.6% improvement according to the research.

**IMPORTANT**: Offline training uses TRUE ACE agent-based pattern discovery.
You (Claude) will need to invoke agents as requested by the training script.

Run the offline training script from the ace-orchestration plugin:

```bash
uvx --from chroma-mcp --with chromadb --with sentence-transformers --with scikit-learn python3 plugins/ace-orchestration/scripts/offline-training.py
```

The script will output agent invocation requests to stderr. You should respond by using the Task tool
to invoke the requested agents (domain-discoverer, reflector, etc.) with the provided data.

This is the TRUE ACE architecture - patterns are DISCOVERED by agents analyzing code,
not matched against hardcoded keywords.
