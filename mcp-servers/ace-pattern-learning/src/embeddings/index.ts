/**
 * ACE Embeddings Engine
 *
 * Semantic embeddings using @xenova/transformers (Transformers.js) for 85% similarity threshold.
 * Pure JavaScript implementation - no Python dependencies!
 */

import { pipeline, env } from '@xenova/transformers';
import { Pattern } from '../types.js';
import { ACEConfig } from '../config.js';

// Disable local model caching for now (can enable for production)
env.cacheDir = './.cache/transformers';

interface EmbeddingCache {
  [patternId: string]: number[];
}

export class EmbeddingsEngine {
  private extractor: any;
  private cache: EmbeddingCache = {};
  private config: ACEConfig;

  constructor(config: ACEConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    console.error('🔄 Loading sentence transformer model (all-MiniLM-L6-v2)...');

    // Load sentence transformer model
    // Same model as Python: sentence-transformers/all-MiniLM-L6-v2
    this.extractor = await pipeline(
      'feature-extraction',
      'Xenova/all-MiniLM-L6-v2'
    );

    console.error('✅ Embeddings engine initialized');
  }

  /**
   * Generate embedding for text
   */
  private async getEmbedding(text: string): Promise<number[]> {
    const output = await this.extractor(text, {
      pooling: 'mean',
      normalize: true,
    });

    return Array.from(output.data);
  }

  /**
   * Calculate cosine similarity between two vectors
   * ACE paper uses cosine similarity with 85% threshold
   */
  private cosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) {
      throw new Error('Vectors must have same length');
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }

    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  /**
   * Add pattern to vector store
   */
  async addPattern(pattern: Pattern): Promise<void> {
    const embedding = await this.getEmbedding(pattern.content);
    this.cache[pattern.id] = embedding;
  }

  /**
   * Update pattern in vector store
   */
  async updatePattern(pattern: Pattern): Promise<void> {
    const embedding = await this.getEmbedding(pattern.content);
    this.cache[pattern.id] = embedding;
  }

  /**
   * Delete pattern from vector store
   */
  async deletePattern(id: string): Promise<void> {
    delete this.cache[id];
  }

  /**
   * Find similar patterns using semantic similarity
   *
   * ACE paper: 85% similarity threshold for deduplication
   */
  async findSimilar(
    content: string,
    threshold: number
  ): Promise<Array<{ id: string; similarity: number }>> {
    const queryEmbedding = await this.getEmbedding(content);
    const results: Array<{ id: string; similarity: number }> = [];

    for (const [id, embedding] of Object.entries(this.cache)) {
      const similarity = this.cosineSimilarity(queryEmbedding, embedding);

      if (similarity >= threshold) {
        results.push({ id, similarity });
      }
    }

    // Sort by similarity descending
    results.sort((a, b) => b.similarity - a.similarity);

    return results;
  }

  /**
   * Deduplicate patterns based on similarity threshold
   *
   * ACE paper: 85% similarity threshold
   */
  async deduplicate(patterns: Pattern[]): Promise<Pattern[]> {
    const unique: Pattern[] = [];
    const threshold = this.config.ace.similarity_threshold; // 0.85

    for (const pattern of patterns) {
      // Check if similar pattern already exists
      const similar = await this.findSimilar(pattern.content, threshold);

      // Find if any similar pattern is already in unique set
      const existingIndex = unique.findIndex(
        u => similar.some(s => s.id === u.id)
      );

      if (existingIndex === -1) {
        // No similar pattern found, add as unique
        unique.push(pattern);
      } else {
        // Similar pattern exists, merge observations
        unique[existingIndex].observations += pattern.observations;
        unique[existingIndex].harmful += pattern.harmful;

        // Recalculate confidence
        const total = unique[existingIndex].observations + unique[existingIndex].harmful;
        unique[existingIndex].confidence = unique[existingIndex].observations / total;

        // Merge evidence
        unique[existingIndex].evidence = [
          ...unique[existingIndex].evidence,
          ...pattern.evidence,
        ];
      }
    }

    return unique;
  }

  /**
   * Clear all embeddings
   */
  async clear(): Promise<void> {
    this.cache = {};
  }

  /**
   * Get cache size
   */
  getCacheSize(): number {
    return Object.keys(this.cache).length;
  }
}
