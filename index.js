/**
 * ACE Orchestration Plugin - Entry Point
 *
 * Agentic Context Engineering for Claude Code CLI
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 *
 * Features:
 * - Three-role architecture (Generator, Reflector, Curator)
 * - Deterministic semantic merging (85% similarity threshold)
 * - Sequential-thinking MCP for reflection
 * - Memory-bank MCP for pattern storage
 * - Incremental delta updates (prevents context collapse)
 * - 20+ predefined patterns across Python, JS, TS
 */

const postToolUse = require('./hooks/postToolUse');
const sessionEnd = require('./hooks/sessionEnd');
const fs = require('fs').promises;

module.exports = {
  name: 'ace-orchestration',
  version: '1.0.0',
  description: 'ACE pattern learning plugin for Claude Code CLI',

  /**
   * Hook definitions
   */
  hooks: {
    PostToolUse: postToolUse,
    SessionEnd: sessionEnd
  },

  /**
   * Plugin initialization
   */
  initialize: async () => {
    console.log('\n🚀 ACE Orchestration Plugin initializing...');
    console.log('   Based on Stanford/SambaNova/UC Berkeley research');
    console.log('   arXiv:2510.04618v1\n');

    try {
      // Create memory directory
      await fs.mkdir('.ace-memory', { recursive: true });
      console.log('✓ Memory storage created');

      // Create initial CLAUDE.md if doesn't exist
      try {
        await fs.access('CLAUDE.md');
        console.log('✓ Existing CLAUDE.md found');
      } catch {
        const initialContent = `# ACE Playbook

*Learning in progress...*

This playbook will automatically evolve as you code with Claude Code CLI.

## What is ACE?

ACE (Agentic Context Engineering) learns from your coding patterns automatically:
- ✅ Detects patterns in your code (20+ predefined)
- 🤔 Reflects on their effectiveness (via LLM)
- 🔀 Merges similar patterns (deterministic algorithm)
- 📖 Updates this playbook with insights

Keep coding, and watch this file grow!
`;
        await fs.writeFile('CLAUDE.md', initialContent);
        console.log('✓ Initial CLAUDE.md created');
      }

      console.log('\n✅ ACE ready to learn from your code!\n');
      console.log('📖 Patterns will be detected automatically');
      console.log('💡 CLAUDE.md will update with insights');
      console.log('🔄 Check after each coding session\n');

      return true;
    } catch (error) {
      console.error('❌ ACE initialization failed:', error.message);
      return false;
    }
  }
};
