/**
 * Pattern Detector Tests
 */

const { detectPatterns, calculateConfidence, getPatternById } = require('../lib/patternDetector');

describe('Pattern Detector', () => {
  describe('detectPatterns', () => {
    test('detects TypedDict pattern in Python', () => {
      const code = `
class AppConfig(TypedDict):
    api_key: str
    port: int
`;
      const detected = detectPatterns(code, 'config.py');
      expect(detected.some(p => p.id === 'py-001')).toBe(true);
    });

    test('detects fetch try-catch pattern in JavaScript', () => {
      const code = `
try {
  const response = await fetch('/api/data');
  const data = await response.json();
} catch (error) {
  console.error(error);
}
`;
      const detected = detectPatterns(code, 'api.js');
      expect(detected.some(p => p.id === 'js-001')).toBe(true);
    });

    test('detects harmful bare except in Python', () => {
      const code = `
try:
    risky_operation()
except:
    pass
`;
      const detected = detectPatterns(code, 'bad.py');
      const bareExcept = detected.find(p => p.id === 'py-003');
      expect(bareExcept).toBeDefined();
      expect(bareExcept.type).toBe('harmful');
    });

    test('returns empty array for unknown file type', () => {
      const code = 'some code';
      const detected = detectPatterns(code, 'file.unknown');
      expect(detected).toEqual([]);
    });

    test('returns empty array for empty code', () => {
      const detected = detectPatterns('', 'file.py');
      expect(detected).toEqual([]);
    });
  });

  describe('calculateConfidence', () => {
    test('calculates confidence correctly', () => {
      expect(calculateConfidence(10, 8)).toBe(0.8);
      expect(calculateConfidence(5, 5)).toBe(1.0);
      expect(calculateConfidence(10, 3)).toBe(0.3);
    });

    test('returns 0 for zero observations', () => {
      expect(calculateConfidence(0, 0)).toBe(0);
      expect(calculateConfidence(0, 5)).toBe(0);
    });

    test('handles edge case where successes > observations', () => {
      expect(calculateConfidence(5, 10)).toBe(1);
    });
  });

  describe('getPatternById', () => {
    test('retrieves pattern by ID', () => {
      const pattern = getPatternById('py-001');
      expect(pattern).toBeDefined();
      expect(pattern.name).toBe('Use TypedDict for configs');
    });

    test('returns null for non-existent pattern', () => {
      const pattern = getPatternById('non-existent');
      expect(pattern).toBeNull();
    });
  });
});
