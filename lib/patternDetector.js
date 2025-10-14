/**
 * ACE Pattern Detector
 *
 * Regex-based pattern detection in code
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 */

const patterns = require('../config/patterns');

/**
 * Detect patterns in code
 * @param {string} code - Source code to analyze
 * @param {string} filePath - Path to the file (for language detection)
 * @returns {Array} Array of detected patterns with metadata
 */
function detectPatterns(code, filePath) {
  const language = patterns.getLanguage(filePath);
  if (language === 'unknown') {
    console.log(`⏭️  Unknown language for file: ${filePath}`);
    return [];
  }

  const languagePatterns = patterns.getPatterns(language);

  if (!languagePatterns || languagePatterns.length === 0) {
    console.log(`⏭️  No patterns defined for language: ${language}`);
    return [];
  }

  // Test each pattern's regex against the code
  const detected = languagePatterns
    .map(pattern => {
      try {
        const applied = pattern.regex.test(code);

        return {
          id: pattern.id,
          name: pattern.name,
          domain: pattern.domain,
          type: pattern.type,
          description: pattern.description,
          applied: applied,
          language: language
        };
      } catch (error) {
        console.error(`Error testing pattern ${pattern.id}:`, error.message);
        return {
          ...pattern,
          applied: false,
          language: language
        };
      }
    })
    .filter(match => match.applied);

  return detected;
}

/**
 * Calculate confidence score
 * @param {number} observations - Total number of observations
 * @param {number} successes - Number of successful applications
 * @returns {number} Confidence score between 0 and 1
 */
function calculateConfidence(observations, successes) {
  if (!observations || observations === 0) return 0;
  if (successes > observations) {
    console.warn(`Warning: successes (${successes}) > observations (${observations})`);
    return 1;
  }
  return successes / observations;
}

/**
 * Get pattern by ID
 * @param {string} patternId - Pattern identifier
 * @returns {Object|null} Pattern definition or null if not found
 */
function getPatternById(patternId) {
  const allPatterns = patterns.getAllPatterns();
  return allPatterns.find(p => p.id === patternId) || null;
}

/**
 * Get patterns by domain
 * @param {string} domain - Domain identifier
 * @returns {Array} Array of patterns in the domain
 */
function getPatternsByDomain(domain) {
  const allPatterns = patterns.getAllPatterns();
  return allPatterns.filter(p => p.domain === domain);
}

/**
 * Get patterns by type
 * @param {string} type - 'helpful' or 'harmful'
 * @returns {Array} Array of patterns of the specified type
 */
function getPatternsByType(type) {
  const allPatterns = patterns.getAllPatterns();
  return allPatterns.filter(p => p.type === type);
}

module.exports = {
  detectPatterns,
  calculateConfidence,
  getPatternById,
  getPatternsByDomain,
  getPatternsByType
};
