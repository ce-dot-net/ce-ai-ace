---
description: Export specific spec-kit playbooks for sharing across projects
allowed-tools: Bash
---

# ACE Export Spec-Kit

Export ACE playbooks in spec-kit format for sharing with team or other projects.

## Usage
- `/ace-export-speckit 001-python-io` - Export specific playbook
- `/ace-export-speckit python` - Export all playbooks in a domain
- `/ace-export-speckit --all` - Export all playbooks

## spec-kit Format

Exports include:
- `spec.md` - Pattern definition with YAML frontmatter
- `plan.md` - Technical implementation approach
- `insights.md` - Reflector analysis history

## Benefits
- **Team Sharing**: Share learned patterns across team
- **Cross-Project**: Transfer knowledge between codebases
- **Backup**: Archive patterns for later use
- **Version Control**: Track pattern evolution via git
- **Human-Readable**: Standard markdown format

!```bash
if [ "$1" = "--all" ]; then
  # Export all playbooks
  tar -czf ace-playbooks-$(date +%Y%m%d).tar.gz specs/
  echo "✅ Exported all playbooks to ace-playbooks-$(date +%Y%m%d).tar.gz"
elif [ -d "specs/playbooks/$1" ]; then
  # Export single playbook
  tar -czf playbook-$1.tar.gz -C specs/playbooks $1/
  echo "✅ Exported playbook to playbook-$1.tar.gz"
elif [ -f specs/memory/constitution.md ]; then
  # Export constitution
  cp specs/memory/constitution.md ./ace-constitution-$(date +%Y%m%d).md
  echo "✅ Exported constitution to ace-constitution-$(date +%Y%m%d).md"
else
  echo "❌ Playbook not found: $1"
  echo "Usage: /ace-export-speckit [playbook-id|--all]"
fi
```
