# Local Testing Instructions

## Quick Start

### 1. Add Local Marketplace

In Claude Code CLI, run:

```bash
/plugin marketplace add file:///Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace
```

### 2. Install Plugin

```bash
/plugin install ace-orchestration@ace-plugin-marketplace
```

### 3. Restart Claude Code

Close and reopen Claude Code CLI completely.

### 4. Verify Installation

```bash
/plugin
```

You should see `ace-orchestration` listed.

---

## Test the Plugin

### Create Test Project

```bash
mkdir ~/test-ace-plugin
cd ~/test-ace-plugin
```

### Create Test File

```bash
cat > test.py << 'EOF'
from typing import TypedDict

class Config(TypedDict):
    host: str
    port: int

def main():
    config: Config = {
        "host": "localhost",
        "port": 8080
    }
    print(f"Server: {config['host']}:{config['port']}")

if __name__ == "__main__":
    main()
EOF
```

### Edit with Claude Code

Ask Claude Code to:
```
"Add a database_url field to the Config TypedDict"
```

### Expected Output

Console should show:
```
🔄 ACE: Starting reflection cycle for test.py
🔍 Detected 2 pattern(s): py-001, py-005
🧪 Evidence: none
💡 Reflection complete
✨ Created: Use TypedDict for configs
✨ Created: Use f-strings for formatting
✅ ACE cycle complete (2 patterns processed)
```

### Check Results

```bash
# Database created
ls -la .ace-memory/
# Should show: patterns.db

# Playbook generated
cat CLAUDE.md
# Should show pattern details

# Test commands
/ace-status
/ace-patterns
/ace-patterns python
```

---

## Troubleshooting

### Plugin Not Loading?

```bash
# Check marketplace
/plugin marketplace list

# Verify plugin structure
ls -la /Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace/.claude-plugin/

# Check Python
python3 --version
```

### Hooks Not Firing?

```bash
# Check script permissions
ls -la /Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace/scripts/

# Test script manually
echo '{"tool_input": {"file_path": "test.py"}}' | python3 /Users/ptsafaridis/repos/github_com/ce-dot-net/ce-ai-ace/scripts/ace-cycle.py
```

### No Patterns Detected?

- Only `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files are supported
- Check console for error messages
- Verify file contains detectable patterns (TypedDict, f-strings, etc.)

---

## Test Checklist

- [ ] Plugin installs successfully
- [ ] Plugin appears in `/plugin` list
- [ ] Hook fires on file edit (see console message)
- [ ] Database created in `.ace-memory/`
- [ ] CLAUDE.md generated
- [ ] `/ace-status` shows statistics
- [ ] `/ace-patterns` lists patterns
- [ ] Patterns have correct confidence scores

---

## Success Criteria

✅ Console shows ACE cycle messages
✅ `.ace-memory/patterns.db` exists
✅ `CLAUDE.md` contains learned patterns
✅ Slash commands work
✅ No Python errors in console

---

## Next Steps After Successful Test

1. Create GitHub repository
2. Push code: `git push origin main`
3. Update marketplace to use GitHub URL
4. Share with community!

---

**Good luck testing! 🚀**
