---
description: Clear ACE pattern database (reset learning)
argument-hint: [--confirm]
allowed-tools: Bash
---

# ACE Clear

Reset the ACE pattern learning database.

⚠️ **WARNING**: This will delete ALL learned patterns and insights!

Arguments: $ARGUMENTS

!```bash
if [ "$1" != "--confirm" ]; then
  echo "⚠️  ACE CLEAR WARNING"
  echo ""
  echo "This will permanently delete:"
  echo "• All learned patterns"
  echo "• All pattern insights"
  echo "• All observations"
  echo "• The entire .ace-memory/ directory"
  echo ""
  echo "To confirm, run: /ace-clear --confirm"
  exit 0
fi

# Backup current database
if [ -d .ace-memory ]; then
  timestamp=$(date +%Y%m%d_%H%M%S)
  cp -r .ace-memory ".ace-memory.backup.$timestamp"
  echo "✅ Backup created: .ace-memory.backup.$timestamp"
fi

# Delete database
rm -rf .ace-memory
rm -f CLAUDE.md

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
echo "• Patterns will be detected automatically as you code"
echo "• The reflector agent will analyze effectiveness"
echo "• CLAUDE.md will be regenerated with new insights"
echo ""
echo "📊 Check status: /ace-status"
echo "🔍 View patterns: /ace-patterns"
```
