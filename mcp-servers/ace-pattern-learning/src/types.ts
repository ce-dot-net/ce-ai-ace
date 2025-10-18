/**
 * ACE Type Definitions
 *
 * Core types for the ACE Pattern Learning system.
 */

/**
 * Pattern - A discovered coding pattern or strategy
 *
 * Based on ACE paper's incremental delta updates with structured bullets.
 */
export interface Pattern {
  id: string;                    // Unique identifier (e.g., "ctx-00001", "code-00013")
  name: string;                  // Pattern name
  domain: string;                // Domain/category (e.g., "api-usage", "error-handling")
  content: string;               // Pattern description/rule
  confidence: number;            // Confidence score (0-1)
  observations: number;          // Number of times observed (helpful count)
  harmful: number;               // Number of times marked harmful
  evidence: string[];            // Code examples/evidence
  created_at: string;            // ISO timestamp
  updated_at: string;            // ISO timestamp
  metadata?: Record<string, any>; // Additional metadata
}

/**
 * Insight - Raw insight from Reflector before curation
 */
export interface Insight {
  pattern_name: string;
  description: string;
  domain?: string;
  evidence: string;
  reasoning: string;
  helpful?: boolean;
  harmful?: boolean;
}

/**
 * PlaybookSection - Structured sections in the playbook
 *
 * Based on ACE paper Figure 3 format.
 */
export interface PlaybookSection {
  title: string;
  bullets: PlaybookBullet[];
}

export interface PlaybookBullet {
  id: string;
  content: string;
  helpful: number;
  harmful: number;
  confidence: number;
}

/**
 * Training Stats - Statistics for offline training epochs
 */
export interface TrainingStats {
  epoch: number;
  patterns_before: number;
  patterns_after: number;
  patterns_refined: number;
  avg_confidence_before: number;
  avg_confidence_after: number;
  files_processed: number;
}

/**
 * Storage Backend interface
 */
export interface StorageBackend {
  initialize(): Promise<void>;

  // Pattern operations
  addPattern(pattern: Pattern): Promise<void>;
  getPattern(id: string): Promise<Pattern | null>;
  getAllPatterns(): Promise<Pattern[]>;
  getPatternsByDomain(domain: string): Promise<Pattern[]>;
  updatePattern(id: string, updates: Partial<Pattern>): Promise<void>;
  deletePattern(id: string): Promise<void>;

  // Search operations
  findSimilarPatterns(content: string, threshold: number): Promise<Array<{ pattern: Pattern; similarity: number }>>;

  // Stats
  getStats(): Promise<{
    total_patterns: number;
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    domains: string[];
  }>;

  // Cleanup
  clear(): Promise<void>;
}
