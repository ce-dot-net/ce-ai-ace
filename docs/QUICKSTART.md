# ACE Plugin - Quick Start Guide

## 📦 What is ACE?

The ACE (Agentic Context Engineering) plugin automatically learns from your coding patterns and builds a comprehensive, evolving playbook (`CLAUDE.md`) that improves your development workflow.

Based on research from Stanford University, SambaNova Systems, and UC Berkeley ([arXiv:2510.04618v1](https://arxiv.org/abs/2510.04618))

---

## 🚀 Installation (30 seconds)

### 1. Add Marketplace
```bash
/plugin marketplace add ce-dot-net/ce-ai-ace
```

### 2. Install Plugin
```bash
/plugin install ace-orchestration@ace-plugin-marketplace
```

### 3. Restart Claude Code
Close and reopen Claude Code CLI completely.

### 4. Verify
```bash
/plugin
```
You should see `ace-orchestration` listed.

---

## 🎮 How to Use

### The plugin works 100% automatically!

1. **Just code normally** with Claude Code
2. **Edit Python, JavaScript, or TypeScript files**
3. **ACE learns automatically** in the background

That's it! No configuration needed.

---

## 🔬 What Happens Behind the Scenes

Every time you edit code, the ACE cycle runs:

```
┌─────────────┐
│  You Code   │ → Edit Python/JS/TS files
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Detect Patterns │ → 20+ built-in patterns
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Gather Tests   │ → Execution feedback
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Reflect 🤔    │ → Analyze effectiveness
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Curate 🔀     │ → Deterministic merging
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Update Playbook │ → CLAUDE.md grows!
└─────────────────┘
```

---

## 💡 Slash Commands

### `/ace-status`
View comprehensive learning statistics:
```bash
/ace-status
```

**Shows:**
- Total patterns learned
- Success rates by domain
- Top confident patterns
- Patterns that may be pruned

---

### `/ace-patterns [domain] [min-confidence]`
List learned patterns with filtering:

```bash
/ace-patterns                    # All patterns
/ace-patterns python             # Only Python patterns
/ace-patterns javascript 0.7     # JS patterns with ≥70% confidence
```

---

### `/ace-force-reflect [file]`
Manually trigger reflection on a file:

```bash
/ace-force-reflect               # Analyze last edited file
/ace-force-reflect src/app.py    # Analyze specific file
```

---

### `/ace-clear --confirm`
Reset pattern database (with backup):

```bash
/ace-clear          # Show warning
/ace-clear --confirm # Actually reset
```

---

## 📖 Check Your Playbook

After coding for a while, check your evolved playbook:

```bash
cat CLAUDE.md
```

**You'll see:**
- High-confidence patterns (≥70%)
- Medium-confidence patterns (30-70%)
- Anti-patterns to avoid
- Specific, actionable insights
- Evidence-based recommendations

---

## 🎯 Example Workflow

### 1. Start a New Project
```bash
cd ~/my-project
claude code .
```

### 2. Code with Claude
```
"Create a Python function that validates user configuration"
```

### 3. ACE Learns Automatically
Console shows:
```
🔄 ACE: Starting reflection cycle for config.py
🔍 Detected 2 pattern(s): py-001, py-005
💡 Reflection complete
✨ Updated: Use TypedDict for configs (confidence: 0.85)
✅ ACE cycle complete
```

### 4. Check Your Playbook
```bash
cat CLAUDE.md
```

**Playbook shows:**
```markdown
## 🎯 High-Confidence Patterns (≥70%)

### Use TypedDict for configs
**Confidence**: 85% (12/14 successes)
**Domain**: python-typing

Define configuration with TypedDict for type safety...
```

---

## ✨ Detected Patterns

### Python (10+ patterns)
- TypedDict for configs
- Dataclasses for models
- F-strings for formatting
- List comprehensions
- Context managers
- Type hints
- **Anti-patterns**: bare except, mutable defaults

### JavaScript (10+ patterns)
- Custom React hooks
- Async/await
- Arrow functions
- Destructuring
- Optional chaining
- **Anti-patterns**: var keyword, callback hell

### TypeScript (5+ patterns)
- Interfaces over types
- Type guards
- Union types
- Generics
- **Anti-patterns**: any type overuse

---

## 📊 Expected Results

Based on research (Stanford/SambaNova/UC Berkeley):

- ✅ **+10-17%** accuracy improvement on complex tasks
- ✅ **82-92%** latency reduction vs. traditional approaches
- ✅ **75-84%** cost reduction
- ✅ **Prevents context collapse** through incremental updates

---

## 🐛 Troubleshooting

### Plugin not loading?
```bash
# Check if plugin is installed
/plugin

# Verify marketplace
/plugin marketplace list

# Restart Claude Code
```

### No patterns detected?
- Plugin only works with: `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files
- Check console for ACE cycle messages
- Try editing a Python/JS/TS file

### CLAUDE.md not updating?
```bash
# Check if database exists
ls -la .ace-memory/

# View statistics
/ace-status

# Check for errors in console
```

---

## 🎓 Learn More

- **README.md** - Complete documentation
- **INSTALL.md** - Installation troubleshooting
- **docs/ACE_RESEARCH.md** - Research paper summary
- **Research Paper**: https://arxiv.org/abs/2510.04618

---

## 🤝 Community

Found a bug? Have a feature request?
- Report issues: https://github.com/ce-dot-net/ce-ai-ace/issues
- Contribute: PRs welcome!

---

**Start coding and watch your playbook evolve! 🚀**

**Your CLAUDE.md will grow into a comprehensive, personalized coding guide tailored to YOUR patterns!**
