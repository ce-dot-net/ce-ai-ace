/**
 * ACE SessionEnd Hook
 *
 * Finalizes the session:
 * 1. Deduplicate patterns
 * 2. Prune low-value patterns
 * 3. Generate final playbook
 *
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 */

const { writePlaybook } = require('../lib/generatePlaybook');
const { listPatterns, storePattern } = require('../lib/ace-utils');
const { deduplicate, prune } = require('../lib/curator');

/**
 * Session end hook
 * @param {Object} event - Hook event object
 */
module.exports = async function sessionEnd(event) {
  console.log('\n🏁 ACE: Session ending...');

  try {
    // Get all patterns
    let patterns = await listPatterns();

    if (!patterns || patterns.length === 0) {
      console.log('📊 No patterns learned in this session');
      return;
    }

    console.log(`📊 Total patterns before cleanup: ${patterns.length}`);

    // Deduplicate patterns (merge similar ones)
    patterns = deduplicate(patterns);
    console.log(`🔀 After deduplication: ${patterns.length}`);

    // Prune low-value patterns
    const beforePrune = patterns.length;
    patterns = prune(patterns);
    const pruned = beforePrune - patterns.length;

    if (pruned > 0) {
      console.log(`🗑️  Pruned ${pruned} low-confidence pattern(s)`);
    }

    // Store cleaned patterns back
    for (const pattern of patterns) {
      await storePattern(pattern);
    }

    // Generate final playbook
    await writePlaybook();

    console.log(`✅ Session complete! Final pattern count: ${patterns.length}`);
    console.log('📖 Check CLAUDE.md for your evolved playbook\n');

  } catch (error) {
    console.error('❌ Session end failed:', error.message);
  }
};
