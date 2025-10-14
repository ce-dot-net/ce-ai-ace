/**
 * ACE PostToolUse Hook
 *
 * Orchestrates the ACE cycle after each code operation:
 * 1. Detect patterns (regex-based)
 * 2. Gather evidence (test results)
 * 3. Reflect (sequential-thinking MCP)
 * 4. Curate (deterministic algorithm)
 * 5. Update playbook
 *
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 */

const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const { exec: execCallback } = require('child_process');
const exec = promisify(execCallback);

const { detectPatterns, calculateConfidence } = require('../lib/patternDetector');
const { getPattern, storePattern, listPatterns, reflect } = require('../lib/ace-utils');
const { curate, mergePatterns } = require('../lib/curator');
const { writePlaybook } = require('../lib/generatePlaybook');

/**
 * Gather execution feedback (test results, errors)
 * @returns {Promise<Object>} Evidence object
 */
async function gatherEvidence() {
  try {
    // Try to run tests
    const { exitCode, stderr, stdout } = await exec('npm test', {
      timeout: 10000,
      maxBuffer: 1024 * 1024
    });

    return {
      testStatus: exitCode === 0 ? 'passed' : 'failed',
      errorLogs: stderr ? stderr.slice(-500) : '',
      output: stdout ? stdout.slice(-300) : '',
      hasTests: true
    };
  } catch (error) {
    // No tests or tests failed
    return {
      testStatus: 'failed',
      errorLogs: error.stderr ? error.stderr.slice(-500) : error.message,
      output: error.stdout ? error.stdout.slice(-300) : '',
      hasTests: false
    };
  }
}

/**
 * Load Reflector prompt template
 * @returns {Promise<string>} Prompt content
 */
async function loadReflectorPrompt() {
  const promptPath = path.join(__dirname, '../agents/reflector-prompt.md');
  return await fs.readFile(promptPath, 'utf8');
}

/**
 * Main ACE cycle hook
 * @param {Object} event - Hook event object
 */
module.exports = async function postToolUse(event) {
  console.log('\n🔄 ACE: Starting reflection cycle...');

  try {
    // Extract code and file path from event
    const code = event.result?.code || event.result?.content || '';
    const filePath = event.file || event.filePath || event.result?.file || '';

    if (!code) {
      console.log('⏭️  No code to analyze');
      return;
    }

    console.log(`📄 Analyzing: ${filePath || 'unnamed file'}`);

    // STEP 1: Detect patterns (Generator outputs)
    const detectedPatterns = detectPatterns(code, filePath);

    if (detectedPatterns.length === 0) {
      console.log('⏭️  No patterns detected');
      return;
    }

    console.log(`🔍 Detected ${detectedPatterns.length} pattern(s): ${detectedPatterns.map(p => p.id).join(', ')}`);

    // STEP 2: Gather evidence (execution feedback)
    const evidence = await gatherEvidence();
    console.log(`🧪 Evidence: ${evidence.testStatus} (tests: ${evidence.hasTests})`);

    // STEP 3: Invoke Reflector (sequential-thinking MCP)
    console.log('🤔 Invoking Reflector via sequential-thinking MCP...');
    const reflectorPrompt = await loadReflectorPrompt();

    const reflection = await reflect({
      reflectionPrompt: reflectorPrompt,
      taskContext: {
        code,
        patterns: detectedPatterns,
        evidence,
        fileContext: filePath
      }
    });

    console.log('💡 Reflection complete');

    // STEP 4: Curate each pattern (deterministic algorithm)
    let patternsProcessed = 0;

    for (const pattern of detectedPatterns) {
      try {
        // Find reflection for this pattern
        const analysis = reflection.patterns_analyzed?.find(
          a => a.pattern_id === pattern.id
        );

        if (!analysis) {
          console.log(`⏭️  No analysis for ${pattern.id}`);
          continue;
        }

        // Prepare new pattern record with reflection results
        const newPattern = {
          id: pattern.id,
          name: pattern.name,
          domain: pattern.domain,
          type: pattern.type,
          description: pattern.description,
          language: pattern.language,
          observations: 1,
          successes: analysis.contributed_to === 'success' ? 1 : 0,
          failures: analysis.contributed_to === 'failure' ? 1 : 0,
          neutrals: analysis.contributed_to === 'neutral' ? 1 : 0,
          insights: [{
            timestamp: new Date().toISOString(),
            insight: analysis.insight,
            recommendation: analysis.recommendation,
            confidence: analysis.confidence,
            appliedCorrectly: analysis.applied_correctly
          }],
          lastSeen: new Date().toISOString()
        };

        // Get existing patterns for comparison
        const existingPatterns = await listPatterns();

        // CURATOR: Deterministic decision (NO LLM!)
        const decision = curate(newPattern, existingPatterns);

        if (decision.action === 'merge') {
          // Merge with existing pattern
          const target = await getPattern(decision.targetId);
          if (target) {
            const merged = mergePatterns(target, newPattern);
            merged.confidence = calculateConfidence(
              merged.observations,
              merged.successes
            );
            await storePattern(merged);
            console.log(`🔀 Merged: ${merged.name} (${(decision.similarity * 100).toFixed(0)}% similar)`);
            patternsProcessed++;
          }

        } else if (decision.action === 'create') {
          // Create new pattern
          newPattern.confidence = calculateConfidence(
            newPattern.observations,
            newPattern.successes
          );
          await storePattern(newPattern);
          console.log(`✨ Created: ${newPattern.name}`);
          patternsProcessed++;

        } else if (decision.action === 'prune') {
          // This shouldn't happen on first observation
          console.log(`🗑️  Pruned: ${decision.targetId} (${decision.reasoning})`);
        }

      } catch (error) {
        console.error(`❌ Failed to process ${pattern.id}:`, error.message);
      }
    }

    // STEP 5: Update playbook
    if (patternsProcessed > 0) {
      await writePlaybook();
      console.log(`✅ ACE cycle complete (${patternsProcessed} patterns processed)\n`);
    } else {
      console.log('⏭️  No patterns updated\n');
    }

  } catch (error) {
    console.error('❌ ACE cycle failed:', error.message);
    console.error(error.stack);
  }
};
