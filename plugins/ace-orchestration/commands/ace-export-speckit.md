---
description: Export specific spec-kit playbooks for sharing across projects
---

Export ACE playbooks in spec-kit format for sharing with team or other projects.

## Usage

```bash
# Export specific playbook
/ace-export-speckit 001-python-io

# Export all playbooks in a domain
/ace-export-speckit python

# Export all playbooks
/ace-export-speckit --all
```

## Implementation

```bash
# Export single playbook
tar -czf playbook-001-python-io.tar.gz -C specs/playbooks 001-python-io/

# Export constitution
cp specs/memory/constitution.md ./ace-constitution-$(date +%Y%m%d).md

# Export all
tar -czf ace-playbooks-$(date +%Y%m%d).tar.gz specs/
```

## spec-kit Format

Exports include:
- `spec.md` - Pattern definition with YAML frontmatter
- `plan.md` - Technical implementation approach
- `insights.md` - Reflector analysis history

## Import to Another Project

```bash
# Extract to target project
cd /path/to/other/project
tar -xzf playbook-001-python-io.tar.gz -C specs/playbooks/

# Or use pattern import
/ace-import-patterns --input playbook-001-python-io.tar.gz --strategy smart
```

## Benefits

- **Team Sharing**: Share learned patterns across team
- **Cross-Project**: Transfer knowledge between codebases
- **Backup**: Archive patterns for later use
- **Version Control**: Track pattern evolution via git
- **Human-Readable**: Standard markdown format

## See Also

- `/ace-import-patterns` - Import playbooks
- `/ace-patterns` - List available patterns
- `specs/README.md` - Playbook documentation
