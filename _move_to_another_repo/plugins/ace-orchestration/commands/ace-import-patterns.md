---
description: Import patterns from another project or backup
allowed-tools: Bash
---

# ACE Import Patterns

Import patterns from a previously exported JSON file.

Imported patterns will be merged with existing ones using ACE's deterministic curation algorithm.

Run the pattern import script:

```bash
python3 plugins/ace-orchestration/scripts/pattern-portability.py import --input ./patterns.json
```
