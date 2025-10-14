---
description: Import patterns from another project or backup
---

Import patterns from a previously exported JSON file.

Usage:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pattern-portability.py import --input ./patterns.json
```

Imported patterns will be merged with existing ones using ACE's deterministic curation algorithm.
