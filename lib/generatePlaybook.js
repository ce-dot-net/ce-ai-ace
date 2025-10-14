/**
 * ACE Playbook Generator
 *
 * Generates CLAUDE.md with confidence-based organization
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 */

const fs = require('fs').promises;
const { listPatterns } = require('./ace-utils');
const { calculateConfidence } = require('./patternDetector');

const CONFIDENCE_THRESHOLD = 0.7; // 70% for high-confidence classification

/**
 * Format a pattern for the playbook
 * @param {Object} pattern - Pattern object
 * @returns {string} Formatted markdown
 */
function formatPattern(pattern) {
  const conf = calculateConfidence(
    pattern.observations || 0,
    pattern.successes || 0
  );

  const latestInsight = pattern.insights && pattern.insights.length > 0
    ? pattern.insights[pattern.insights.length - 1]
    : null;

  let formatted = `
### ${pattern.name}

**Confidence**: ${(conf * 100).toFixed(0)}% (${pattern.successes || 0}/${pattern.observations || 0} successes)
**Domain**: ${pattern.domain}
**Language**: ${pattern.language || 'multiple'}
**Last seen**: ${pattern.lastSeen ? new Date(pattern.lastSeen).toLocaleDateString() : 'Never'}

${pattern.description}
`;

  if (latestInsight) {
    formatted += `\n**💡 Latest Insight**: ${latestInsight.insight}\n`;
    formatted += `\n**📋 Recommendation**: ${latestInsight.recommendation}\n`;
  }

  return formatted;
}

/**
 * Generate the complete playbook content
 * @returns {Promise<string>} Playbook markdown content
 */
async function generatePlaybook() {
  try {
    const allPatterns = await listPatterns();

    if (!allPatterns || allPatterns.length === 0) {
      return `# ACE Playbook

*No patterns learned yet. Keep coding and I'll learn from your work!*

## What is ACE?

ACE (Agentic Context Engineering) automatically learns from your coding patterns:

- ✅ **Helpful patterns** that work well
- ⚠️ **Anti-patterns** to avoid
- 📊 **Confidence scores** based on success rate
- 💡 **Specific insights** from reflection

Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)

---

## How It Works

1. **You code** - Write code with Claude Code as usual
2. **Patterns detected** - Plugin identifies coding patterns (20+ predefined)
3. **Reflector analyzes** - LLM evaluates pattern effectiveness
4. **Curator merges** - Deterministic algorithm (85% similarity) deduplicates
5. **Playbook evolves** - This file updates with learned insights

The playbook grows over time, creating a comprehensive guide tailored to YOUR codebase.
`;
    }

    // Categorize patterns
    const helpful = allPatterns.filter(p => p.type === 'helpful');
    const harmful = allPatterns.filter(p => p.type === 'harmful');

    const highConfidence = helpful
      .filter(p => calculateConfidence(p.observations, p.successes) >= CONFIDENCE_THRESHOLD)
      .sort((a, b) =>
        calculateConfidence(b.observations, b.successes) -
        calculateConfidence(a.observations, a.successes)
      );

    const mediumConfidence = helpful
      .filter(p => calculateConfidence(p.observations, p.successes) < CONFIDENCE_THRESHOLD)
      .sort((a, b) =>
        calculateConfidence(b.observations, b.successes) -
        calculateConfidence(a.observations, a.successes)
      );

    const antiPatterns = harmful
      .sort((a, b) =>
        calculateConfidence(b.observations, b.successes) -
        calculateConfidence(a.observations, a.successes)
      );

    // Build playbook
    let content = `# ACE Playbook

*Auto-generated: ${new Date().toISOString()}*
*Total patterns: ${allPatterns.length}*
*High-confidence: ${highConfidence.length} | Medium: ${mediumConfidence.length} | Anti-patterns: ${antiPatterns.length}*

---

`;

    if (highConfidence.length > 0) {
      content += `## 🎯 High-Confidence Patterns (≥${CONFIDENCE_THRESHOLD * 100}%)

*Apply these patterns to your current work - they have proven track records*

${highConfidence.map(formatPattern).join('\n---\n')}

`;
    }

    if (mediumConfidence.length > 0) {
      content += `## 💡 Medium-Confidence Patterns (<${CONFIDENCE_THRESHOLD * 100}%)

*Consider these patterns, but verify appropriateness for your specific context*

${mediumConfidence.map(formatPattern).join('\n---\n')}

`;
    }

    if (antiPatterns.length > 0) {
      content += `## ⚠️ Anti-Patterns (AVOID)

*These patterns have been identified as problematic - avoid in your code*

${antiPatterns.map(formatPattern).join('\n---\n')}

`;
    }

    content += `
---

## About ACE

This playbook is automatically generated using **Agentic Context Engineering (ACE)**, based on research from Stanford University, SambaNova Systems, and UC Berkeley.

**Key principles**:
- **Comprehensive over concise**: Rich context with detailed insights
- **Incremental delta updates**: Never rewrites the whole playbook
- **Deterministic merging**: 85% similarity threshold (no LLM guessing)
- **Evidence-based**: Patterns backed by test results and reflection

**Research**: arXiv:2510.04618v1
`;

    return content;

  } catch (error) {
    console.error('Error generating playbook:', error);
    return `# ACE Playbook\n\n*Error generating playbook: ${error.message}*\n`;
  }
}

/**
 * Write the playbook to CLAUDE.md
 * @returns {Promise<boolean>} Success status
 */
async function writePlaybook() {
  try {
    const content = await generatePlaybook();
    await fs.writeFile('CLAUDE.md', content, 'utf8');
    console.log('✅ Playbook updated successfully');
    return true;
  } catch (error) {
    console.error('❌ Failed to write playbook:', error);
    return false;
  }
}

module.exports = {
  generatePlaybook,
  writePlaybook,
  formatPattern,
  CONFIDENCE_THRESHOLD
};
