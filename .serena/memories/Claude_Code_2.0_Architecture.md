# Claude Code 2.0.0 + Sonnet 4.5 - Architecture Summary

## Released: September 29, 2025

## Key Changes from 1.x to 2.0

### 1. Plugin System (CRITICAL)
- **Plugins are PURELY DECLARATIVE** - markdown + JSON only
- NO `index.js` or JavaScript entry point required
- Structure: `.claude-plugin/plugin.json` + markdown files
- Install via: `/plugin marketplace add` + `/plugin install`

### 2. Subagents (New in 2.0)
- Parallel task execution via Task tool
- Each subagent = isolated Claude Code instance
- Spawned with: `Task("description", "prompt", "agent-name")`
- Best practice: Spawn multiple tasks in ONE message for parallelism

### 3. Checkpoints (New in 2.0)
- Automatic save before each change
- Rewind via: `Esc+Esc` or `/rewind` command
- Can restore code, conversation, or both
- Enables safe experimentation

### 4. Hooks System
- Event-based automation (PreToolUse, PostToolUse, SessionEnd, etc.)
- Defined in `hooks/hooks.json`
- Execute shell scripts/commands
- Can block operations (exit code 2 in PreToolUse)

### 5. Background Tasks
- Run dev servers, watch tasks without blocking
- Syntax: "Run [command] in background"
- Check status with BashOutput tool

### 6. Sonnet 4.5 Integration
- Default model for Claude Code 2.0
- Better at long, complex development tasks
- Improved agent coordination
- Better tool use and reasoning

## Plugin File Structure (2.0)

```
plugin-root/
├── .claude-plugin/
│   └── plugin.json          # ONLY metadata, no code
├── commands/                 # Slash commands (markdown)
│   ├── command1.md
│   └── subdir/command2.md
├── agents/                   # Subagents (markdown)
│   ├── agent1.md
│   └── agent2.md
├── hooks/                    # Automation
│   └── hooks.json
├── scripts/                  # Helper scripts for hooks
│   ├── script1.sh
│   └── script2.py
└── README.md
```

## No index.js Required!

**OLD WAY (Wrong for Claude Code 2.0):**
```javascript
// ❌ This is NOT how Claude Code plugins work
module.exports = {
  name: 'plugin',
  hooks: { ... },
  commands: { ... }
}
```

**NEW WAY (Correct for Claude Code 2.0):**
```json
// ✅ .claude-plugin/plugin.json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "What this plugin does"
}
```

## Implications for ACE Plugin

1. **Remove all JavaScript module exports** - Not needed
2. **Convert hooks to shell scripts** - Called by hooks.json
3. **Create agents as markdown** - Reflector becomes markdown file
4. **Commands as markdown** - ACE status, patterns, etc.
5. **Database in separate script** - Called by hooks
6. **Curator as standalone script** - Python or Node.js CLI tool

## Agent Definition (Markdown)

```markdown
---
name: reflector
description: Analyzes coding patterns for effectiveness
tools: Read, Grep, Glob
model: sonnet
---

You are the Reflector in an ACE system...

[Full prompt here]
```

## Hook Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/ace-cycle.py"
          }
        ]
      }
    ]
  }
}
```

## Key Takeaways

1. Plugins are DECLARATIVE (markdown + JSON)
2. Hooks run EXTERNAL scripts (Python, Bash, Node.js)
3. Agents are MARKDOWN files with system prompts
4. Commands are MARKDOWN files with instructions
5. Task tool spawns subagents in PARALLEL
6. Checkpoints enable safe experimentation
7. Sonnet 4.5 is default model (better reasoning)
