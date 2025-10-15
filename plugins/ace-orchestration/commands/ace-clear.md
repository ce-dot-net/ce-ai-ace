---
description: Clear ACE pattern database (reset learning)
argument-hint: [--confirm]
allowed-tools: Bash
---

# ACE Clear

Reset the ACE pattern learning database.

⚠️ **WARNING**: This will delete ALL learned patterns and insights!

## Usage:
- `/ace-clear` - Show confirmation prompt
- `/ace-clear --confirm` - Actually delete database

## Steps:

1. **Check for --confirm flag**:
   - If `$1` != "--confirm":
     - Show warning message:
     ```
     ⚠️  ACE CLEAR WARNING

     This will permanently delete:
     • All learned patterns
     • All pattern insights
     • All observations
     • The entire .ace-memory/ directory

     To confirm, run: /ace-clear --confirm
     ```
     - STOP and wait for user confirmation

2. **If --confirm provided**:
   ```bash
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
   ```

3. **Show success message** with next steps:
   ```
   ✅ ACE Reset Complete

   The pattern learning system has been reset.

   What happens next:
   • Patterns will be detected automatically as you code
   • The reflector agent will analyze effectiveness
   • CLAUDE.md will be regenerated with new insights

   📊 Check status: /ace-status
   🔍 View patterns: /ace-patterns
   ```
