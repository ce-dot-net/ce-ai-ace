/**
 * ACE Curator - Deterministic Pattern Merging
 *
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 *
 * KEY PRINCIPLE: The Curator is DETERMINISTIC - NO LLM CALLS
 * - Uses string similarity (85% threshold) for semantic matching
 * - Merges similar patterns to prevent redundancy
 * - Prunes low-confidence patterns (<30% after 10 observations)
 * - Prevents context collapse through incremental delta updates
 */

const stringSimilarity = require('string-similarity');

// Research-backed thresholds from the paper
const SIMILARITY_THRESHOLD = 0.85;  // 85% similarity for merging
const PRUNE_THRESHOLD = 0.3;        // 30% minimum confidence
const MIN_OBSERVATIONS = 10;        // Minimum observations before pruning

/**
 * Calculate semantic similarity between two patterns
 * Uses weighted string similarity: name (60%) + description (40%)
 *
 * @param {Object} pattern1 - First pattern
 * @param {Object} pattern2 - Second pattern
 * @returns {number} Similarity score between 0 and 1
 */
function calculateSimilarity(pattern1, pattern2) {
  const name1 = (pattern1.name || '').toLowerCase();
  const name2 = (pattern2.name || '').toLowerCase();
  const desc1 = (pattern1.description || '').toLowerCase();
  const desc2 = (pattern2.description || '').toLowerCase();

  // Weighted average: name matters more for matching
  const nameSim = stringSimilarity.compareTwoStrings(name1, name2);
  const descSim = stringSimilarity.compareTwoStrings(desc1, desc2);

  return (nameSim * 0.6) + (descSim * 0.4);
}

/**
 * Curate a new pattern - decide whether to merge, create, or prune
 * This is a DETERMINISTIC algorithm, no LLM involved
 *
 * @param {Object} newPattern - New pattern to curate
 * @param {Array} existingPatterns - Existing patterns in the library
 * @param {Object} config - Configuration overrides
 * @returns {Object} Decision object with action and reasoning
 */
function curate(newPattern, existingPatterns = [], config = {}) {
  const similarityThreshold = config.similarityThreshold || SIMILARITY_THRESHOLD;
  const pruneThreshold = config.pruneThreshold || PRUNE_THRESHOLD;
  const minObservations = config.minObservations || MIN_OBSERVATIONS;

  // 1. Find most similar pattern in same domain and type
  let bestMatch = null;
  let bestSimilarity = 0;

  for (const existing of existingPatterns) {
    // Only compare within same domain and type
    if (existing.domain !== newPattern.domain) continue;
    if (existing.type !== newPattern.type) continue;

    const similarity = calculateSimilarity(newPattern, existing);

    if (similarity > bestSimilarity) {
      bestSimilarity = similarity;
      bestMatch = existing;
    }
  }

  // 2. MERGE if similarity >= threshold
  if (bestMatch && bestSimilarity >= similarityThreshold) {
    return {
      action: 'merge',
      targetId: bestMatch.id,
      similarity: bestSimilarity,
      reasoning: `Similar to existing pattern (${(bestSimilarity * 100).toFixed(0)}% match)`
    };
  }

  // 3. PRUNE if low confidence after enough observations
  if (newPattern.observations >= minObservations) {
    const confidence = (newPattern.successes || 0) / newPattern.observations;
    if (confidence < pruneThreshold) {
      return {
        action: 'prune',
        targetId: newPattern.id,
        confidence: confidence,
        reasoning: `Low confidence (${(confidence * 100).toFixed(0)}%) after ${newPattern.observations} observations`
      };
    }
  }

  // 4. CREATE new pattern
  return {
    action: 'create',
    reasoning: 'Unique pattern, no similar matches found'
  };
}

/**
 * Merge two patterns deterministically
 * Combines observations, successes, failures, and insights
 *
 * @param {Object} target - Target pattern to merge into
 * @param {Object} source - Source pattern to merge from
 * @returns {Object} Merged pattern
 */
function mergePatterns(target, source) {
  return {
    ...target,
    observations: (target.observations || 0) + (source.observations || 0),
    successes: (target.successes || 0) + (source.successes || 0),
    failures: (target.failures || 0) + (source.failures || 0),
    neutrals: (target.neutrals || 0) + (source.neutrals || 0),
    lastSeen: source.lastSeen || target.lastSeen || new Date().toISOString(),
    // Merge insights arrays, keep last 10
    insights: [
      ...(target.insights || []),
      ...(source.insights || [])
    ].slice(-10)
  };
}

/**
 * De-duplicate a list of patterns
 * Merges patterns with >= 85% similarity
 *
 * @param {Array} patterns - Array of patterns
 * @param {Object} config - Configuration overrides
 * @returns {Array} De-duplicated array of patterns
 */
function deduplicate(patterns, config = {}) {
  const similarityThreshold = config.similarityThreshold || SIMILARITY_THRESHOLD;
  const merged = [];
  const processed = new Set();

  for (let i = 0; i < patterns.length; i++) {
    if (processed.has(i)) continue;

    let current = patterns[i];
    processed.add(i);

    // Find all similar patterns
    for (let j = i + 1; j < patterns.length; j++) {
      if (processed.has(j)) continue;

      // Only compare within same domain and type
      if (patterns[i].domain !== patterns[j].domain) continue;
      if (patterns[i].type !== patterns[j].type) continue;

      const similarity = calculateSimilarity(patterns[i], patterns[j]);

      if (similarity >= similarityThreshold) {
        current = mergePatterns(current, patterns[j]);
        processed.add(j);
      }
    }

    merged.push(current);
  }

  return merged;
}

/**
 * Prune low-value patterns
 * Removes patterns with confidence < 30% after 10+ observations
 *
 * @param {Array} patterns - Array of patterns
 * @param {Object} config - Configuration overrides
 * @returns {Array} Pruned array of patterns
 */
function prune(patterns, config = {}) {
  const pruneThreshold = config.pruneThreshold || PRUNE_THRESHOLD;
  const minObservations = config.minObservations || MIN_OBSERVATIONS;

  return patterns.filter(p => {
    // Keep patterns with few observations (still learning)
    if ((p.observations || 0) < minObservations) return true;

    // Calculate confidence
    const confidence = (p.successes || 0) / (p.observations || 1);

    // Remove if confidence too low
    return confidence >= pruneThreshold;
  });
}

/**
 * Grow-and-refine: Update existing pattern or create new bullet
 * Implements incremental delta updates from the paper
 *
 * @param {Object} pattern - Pattern to add or update
 * @param {Array} existingPatterns - Current pattern library
 * @returns {Object} Update decision
 */
function growAndRefine(pattern, existingPatterns) {
  const decision = curate(pattern, existingPatterns);

  if (decision.action === 'merge') {
    const target = existingPatterns.find(p => p.id === decision.targetId);
    if (target) {
      const merged = mergePatterns(target, pattern);
      return {
        action: 'update',
        pattern: merged,
        reasoning: decision.reasoning
      };
    }
  }

  if (decision.action === 'create') {
    return {
      action: 'append',
      pattern: pattern,
      reasoning: decision.reasoning
    };
  }

  return decision;
}

module.exports = {
  curate,
  mergePatterns,
  deduplicate,
  prune,
  growAndRefine,
  calculateSimilarity,
  // Export thresholds for testing and configuration
  SIMILARITY_THRESHOLD,
  PRUNE_THRESHOLD,
  MIN_OBSERVATIONS
};
