/**
 * Curator Tests
 */

const {
  curate,
  mergePatterns,
  calculateSimilarity,
  deduplicate,
  prune,
  SIMILARITY_THRESHOLD
} = require('../lib/curator');

describe('Curator', () => {
  describe('calculateSimilarity', () => {
    test('identifies very similar patterns', () => {
      const pattern1 = {
        name: 'Use TypedDict for configs',
        description: 'Define configuration with TypedDict for type safety'
      };
      const pattern2 = {
        name: 'Use TypedDict for configuration',
        description: 'Define config with TypedDict'
      };
      const similarity = calculateSimilarity(pattern1, pattern2);
      expect(similarity).toBeGreaterThan(0.8);
    });

    test('identifies dissimilar patterns', () => {
      const pattern1 = {
        name: 'Use TypedDict for configs',
        description: 'Define configuration with TypedDict'
      };
      const pattern2 = {
        name: 'Use asyncio.gather',
        description: 'Run parallel async operations'
      };
      const similarity = calculateSimilarity(pattern1, pattern2);
      expect(similarity).toBeLessThan(0.3);
    });
  });

  describe('curate', () => {
    test('merges similar patterns above threshold', () => {
      const newPattern = {
        id: 'test-1',
        name: 'Use TypedDict for configuration',
        description: 'Define config with TypedDict',
        domain: 'python-typing',
        type: 'helpful'
      };

      const existing = [{
        id: 'py-001',
        name: 'Use TypedDict for configs',
        description: 'Define configuration with TypedDict for type safety',
        domain: 'python-typing',
        type: 'helpful',
        observations: 5,
        successes: 4
      }];

      const decision = curate(newPattern, existing);
      expect(decision.action).toBe('merge');
      expect(decision.targetId).toBe('py-001');
      expect(decision.similarity).toBeGreaterThanOrEqual(SIMILARITY_THRESHOLD);
    });

    test('creates new pattern when dissimilar', () => {
      const newPattern = {
        id: 'test-2',
        name: 'Use asyncio.gather for parallel requests',
        description: 'Run multiple async calls concurrently',
        domain: 'python-async',
        type: 'helpful'
      };

      const existing = [{
        id: 'py-001',
        name: 'Use TypedDict for configs',
        domain: 'python-typing',
        type: 'helpful'
      }];

      const decision = curate(newPattern, existing);
      expect(decision.action).toBe('create');
    });

    test('prunes low-confidence patterns', () => {
      const lowConfPattern = {
        id: 'test-3',
        name: 'Some pattern',
        domain: 'test',
        type: 'helpful',
        observations: 15,
        successes: 2 // 13% confidence - below 30% threshold
      };

      const decision = curate(lowConfPattern, []);
      expect(decision.action).toBe('prune');
      expect(decision.confidence).toBeLessThan(0.3);
    });

    test('does not prune patterns with few observations', () => {
      const newPattern = {
        id: 'test-4',
        name: 'Pattern with few observations',
        domain: 'test',
        type: 'helpful',
        observations: 3,
        successes: 0 // 0% confidence but too few observations
      };

      const decision = curate(newPattern, []);
      expect(decision.action).toBe('create');
    });
  });

  describe('mergePatterns', () => {
    test('combines observations and successes', () => {
      const target = {
        id: 'py-001',
        observations: 5,
        successes: 4,
        failures: 1,
        insights: [{ text: 'old insight' }]
      };

      const source = {
        observations: 3,
        successes: 2,
        failures: 1,
        insights: [{ text: 'new insight' }]
      };

      const merged = mergePatterns(target, source);
      expect(merged.observations).toBe(8);
      expect(merged.successes).toBe(6);
      expect(merged.failures).toBe(2);
      expect(merged.insights.length).toBe(2);
    });

    test('keeps last 10 insights only', () => {
      const target = {
        insights: Array(8).fill({ text: 'old' })
      };
      const source = {
        insights: Array(5).fill({ text: 'new' })
      };

      const merged = mergePatterns(target, source);
      expect(merged.insights.length).toBe(10);
    });
  });

  describe('deduplicate', () => {
    test('merges similar patterns', () => {
      const patterns = [
        {
          id: 'p1',
          name: 'Use TypedDict for configs',
          description: 'Define configuration with TypedDict',
          domain: 'python-typing',
          type: 'helpful',
          observations: 5,
          successes: 4
        },
        {
          id: 'p2',
          name: 'Use TypedDict for configuration',
          description: 'Define config with TypedDict for type safety',
          domain: 'python-typing',
          type: 'helpful',
          observations: 3,
          successes: 2
        }
      ];

      const deduped = deduplicate(patterns);
      expect(deduped.length).toBe(1);
      expect(deduped[0].observations).toBe(8); // 5 + 3
      expect(deduped[0].successes).toBe(6); // 4 + 2
    });

    test('keeps dissimilar patterns separate', () => {
      const patterns = [
        {
          id: 'p1',
          name: 'Use TypedDict',
          description: 'Type safety',
          domain: 'python-typing',
          type: 'helpful'
        },
        {
          id: 'p2',
          name: 'Use asyncio.gather',
          description: 'Parallel async',
          domain: 'python-async',
          type: 'helpful'
        }
      ];

      const deduped = deduplicate(patterns);
      expect(deduped.length).toBe(2);
    });
  });

  describe('prune', () => {
    test('removes low-confidence patterns with enough observations', () => {
      const patterns = [
        {
          id: 'p1',
          observations: 15,
          successes: 2 // 13% confidence
        },
        {
          id: 'p2',
          observations: 10,
          successes: 8 // 80% confidence
        }
      ];

      const pruned = prune(patterns);
      expect(pruned.length).toBe(1);
      expect(pruned[0].id).toBe('p2');
    });

    test('keeps patterns with few observations', () => {
      const patterns = [
        {
          id: 'p1',
          observations: 3,
          successes: 0 // 0% confidence but too few observations
        }
      ];

      const pruned = prune(patterns);
      expect(pruned.length).toBe(1);
    });
  });
});
