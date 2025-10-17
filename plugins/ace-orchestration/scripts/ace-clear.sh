#!/usr/bin/env bash
# ACE Clear - Reset pattern learning database

set -euo pipefail

if [ "${1:-}" != "--confirm" ]; then
  echo "⚠️  ACE CLEAR WARNING"
  echo ""
  echo "This will permanently delete:"
  echo "• All learned patterns"
  echo "• All pattern insights"
  echo "• All observations"
  echo "• The entire .ace-memory/ directory"
  echo ""
  echo "To confirm, run: /ace-orchestration:ace-clear --confirm"
  exit 0
fi

# Backup current database
if [ -d .ace-memory ]; then
  timestamp=$(date +%Y%m%d_%H%M%S)
  cp -r .ace-memory ".ace-memory.backup.$timestamp"
  echo "✅ Backup created: .ace-memory.backup.$timestamp"
fi

# Delete database and generated spec-kit playbooks
rm -rf .ace-memory
rm -f CLAUDE.md

# Remove auto-generated spec-kit playbooks from previous training
# Keep manually created playbooks (001-temp, 003-avoid-bare-except, etc.)
# Remove only numbered directories that were auto-generated during offline training
if [ -d specs/playbooks ]; then
  # Remove directories with pattern NNN-* where NNN >= 005 (auto-generated)
  # This preserves manually created playbooks 001, 003 while removing training artifacts
  find specs/playbooks -type d -name '[0-9][0-9][0-9]-*' | while read dir; do
    dir_num=$(basename "$dir" | cut -d'-' -f1)
    if [ "$dir_num" -ge 5 ] 2>/dev/null; then
      rm -rf "$dir"
    fi
  done
fi

echo "🗑️  ACE database cleared"
echo "📝 Pattern learning will restart from scratch"
echo ""
echo "Backup saved in case you need to restore"
echo ""
echo "✅ ACE Reset Complete"
echo ""
echo "The pattern learning system has been reset."
echo ""
echo "What happens next:"
echo "• Patterns will be discovered automatically as you code"
echo "• The reflector agent will analyze effectiveness"
echo "• CLAUDE.md will be regenerated with new insights"
echo ""
echo "📊 Check status: /ace-orchestration:ace-status"
echo "🔍 View patterns: /ace-orchestration:ace-patterns"
