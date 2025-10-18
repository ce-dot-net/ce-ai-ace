---
description: Export learned patterns to share across projects
allowed-tools: Bash
---

# ACE Export Patterns

Export your learned patterns to a JSON file for backup or cross-project sharing.

Exported patterns include:
- Pattern definitions and metadata
- Confidence scores and observations
- Insights and recommendations
- Evolution history

Run the pattern export script:

```bash
python3 plugins/ace-orchestration/scripts/pattern-portability.py export --output ./my-patterns.json
```
