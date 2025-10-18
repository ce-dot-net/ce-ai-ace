/**
 * ACE Configuration
 *
 * Configuration for the ACE Pattern Learning system based on research paper parameters.
 */

export interface ACEConfig {
  storage: {
    type: 'local' | 'github' | 'remote';
    path: string;
  };
  ace: {
    // ACE Paper: 85% semantic similarity threshold for deduplication
    similarity_threshold: number;

    // ACE Paper: 70% confidence threshold for constitution (high-confidence principles)
    confidence_threshold_high: number;

    // ACE Paper: 30% confidence threshold for pruning
    confidence_threshold_medium: number;

    // ACE Paper: Iterative refinement rounds for Reflector
    max_refinement_rounds: number;

    // ACE Paper: Lazy vs proactive deduplication
    deduplication_strategy: 'lazy' | 'proactive';

    // Batch size for parallel processing
    batch_size: number;

    // Context window threshold for lazy deduplication
    context_window_threshold: number;
  };
}

export function getConfig(): ACEConfig {
  return {
    storage: {
      type: (process.env.ACE_STORAGE_TYPE as any) || 'local',
      path: process.env.ACE_STORAGE_PATH || '.ace-memory/patterns.db',
    },
    ace: {
      similarity_threshold: parseFloat(process.env.ACE_SIMILARITY_THRESHOLD || '0.85'),
      confidence_threshold_high: parseFloat(process.env.ACE_CONFIDENCE_HIGH || '0.70'),
      confidence_threshold_medium: parseFloat(process.env.ACE_CONFIDENCE_MEDIUM || '0.30'),
      max_refinement_rounds: parseInt(process.env.ACE_MAX_REFINEMENT || '5', 10),
      deduplication_strategy: (process.env.ACE_DEDUP_STRATEGY as any) || 'lazy',
      batch_size: parseInt(process.env.ACE_BATCH_SIZE || '5', 10),
      context_window_threshold: parseInt(process.env.ACE_CONTEXT_THRESHOLD || '100000', 10),
    },
  };
}
