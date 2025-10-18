/**
 * ACE Curator
 *
 * Implements the Curator algorithm from ACE paper:
 * - Incremental delta updates
 * - Grow-and-refine with 85% similarity threshold
 * - Confidence-based pruning
 */

import { Pattern, Insight } from '../types.js';
import { ACEConfig } from '../config.js';
import { ACEStorage } from '../storage/index.js';
import { randomBytes } from 'crypto';

export class Curator {
  private storage: ACEStorage;
  private config: ACEConfig;

  constructor(storage: ACEStorage, config: ACEConfig) {
    this.storage = storage;
    this.config = config;
  }

  /**
   * Generate deterministic pattern ID
   */
  private generatePatternId(domain: string): string {
    const hash = randomBytes(4).toString('hex');
    const prefix = this.getDomainPrefix(domain);
    return `${prefix}-${hash}`;
  }

  /**
   * Get domain prefix for pattern IDs
   */
  private getDomainPrefix(domain: string): string {
    const prefixes: Record<string, string> = {
      'strategies-and-rules': 'rule',
      'code-snippets': 'code',
      'troubleshooting': 'ts',
      'api-usage': 'api',
      'error-handling': 'err',
      'context': 'ctx',
    };

    return prefixes[domain] || 'pat';
  }

  /**
   * Curate insights into patterns
   *
   * ACE paper: Incremental delta updates, not monolithic rewrites
   */
  async curate(insights: Insight[], existingPatterns?: Pattern[]): Promise<Pattern[]> {
    const patterns = existingPatterns || await this.storage.getAllPatterns();
    const newPatterns: Pattern[] = [];

    for (const insight of insights) {
      // Check if similar pattern exists (85% threshold)
      const similar = await this.storage.findSimilarPatterns(
        insight.description,
        this.config.ace.similarity_threshold
      );

      if (similar.length > 0) {
        // Merge with existing pattern
        const existing = similar[0].pattern;

        // Update observations (helpful/harmful counters)
        const observations = existing.observations + (insight.helpful ? 1 : 0);
        const harmful = existing.harmful + (insight.harmful ? 1 : 0);
        const total = observations + harmful;

        // Recalculate confidence
        const confidence = total > 0 ? observations / total : 0;

        // Add evidence
        const evidence = [...existing.evidence];
        if (insight.evidence && !evidence.includes(insight.evidence)) {
          evidence.push(insight.evidence);
        }

        await this.storage.updatePattern(existing.id, {
          observations,
          harmful,
          confidence,
          evidence,
          updated_at: new Date().toISOString(),
        });
      } else {
        // Create new pattern
        const pattern: Pattern = {
          id: this.generatePatternId(insight.domain || 'context'),
          name: insight.pattern_name,
          domain: insight.domain || 'general',
          content: insight.description,
          confidence: insight.helpful ? 1.0 : 0.0,
          observations: insight.helpful ? 1 : 0,
          harmful: insight.harmful ? 1 : 0,
          evidence: insight.evidence ? [insight.evidence] : [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        newPatterns.push(pattern);
        await this.storage.addPattern(pattern);
      }
    }

    // Prune low-confidence patterns (ACE paper: 30% threshold)
    await this.prune();

    // Deduplicate if needed (lazy strategy)
    if (this.config.ace.deduplication_strategy === 'proactive') {
      await this.deduplicate();
    }

    return await this.storage.getAllPatterns();
  }

  /**
   * Prune low-confidence patterns
   *
   * ACE paper: 30% confidence threshold for pruning
   */
  private async prune(): Promise<void> {
    const patterns = await this.storage.getAllPatterns();
    const threshold = this.config.ace.confidence_threshold_medium;

    for (const pattern of patterns) {
      // Prune if confidence < 30% and has at least 5 observations
      if (pattern.confidence < threshold && (pattern.observations + pattern.harmful) >= 5) {
        await this.storage.deletePattern(pattern.id);
      }
    }
  }

  /**
   * Deduplicate similar patterns
   *
   * ACE paper: 85% similarity threshold, grow-and-refine
   */
  private async deduplicate(): Promise<void> {
    const patterns = await this.storage.getAllPatterns();
    const processed = new Set<string>();

    for (const pattern of patterns) {
      if (processed.has(pattern.id)) continue;

      // Find similar patterns
      const similar = await this.storage.findSimilarPatterns(
        pattern.content,
        this.config.ace.similarity_threshold
      );

      if (similar.length > 1) {
        // Merge similar patterns
        const primary = similar[0].pattern;
        const duplicates = similar.slice(1);

        // Accumulate observations and evidence
        let totalObservations = primary.observations;
        let totalHarmful = primary.harmful;
        const mergedEvidence = [...primary.evidence];

        for (const { pattern: dup } of duplicates) {
          totalObservations += dup.observations;
          totalHarmful += dup.harmful;

          for (const evidence of dup.evidence) {
            if (!mergedEvidence.includes(evidence)) {
              mergedEvidence.push(evidence);
            }
          }

          // Delete duplicate
          await this.storage.deletePattern(dup.id);
          processed.add(dup.id);
        }

        // Update primary pattern
        const total = totalObservations + totalHarmful;
        const confidence = total > 0 ? totalObservations / total : 0;

        await this.storage.updatePattern(primary.id, {
          observations: totalObservations,
          harmful: totalHarmful,
          confidence,
          evidence: mergedEvidence,
          updated_at: new Date().toISOString(),
        });

        processed.add(primary.id);
      }
    }
  }

  /**
   * Get patterns for constitution (high-confidence principles)
   *
   * ACE paper: 70% confidence threshold for constitution
   */
  async getConstitution(): Promise<Pattern[]> {
    const patterns = await this.storage.getAllPatterns();
    return patterns.filter(
      p => p.confidence >= this.config.ace.confidence_threshold_high
    );
  }

  /**
   * Format patterns as playbook
   *
   * ACE paper Figure 3 format: structured sections with bullet IDs
   */
  async formatPlaybook(taskHint?: string): Promise<string> {
    let patterns: Pattern[];

    if (taskHint) {
      // Retrieve relevant patterns based on task
      const similar = await this.storage.findSimilarPatterns(taskHint, 0.5);
      patterns = similar.map(s => s.pattern);
    } else {
      patterns = await this.storage.getAllPatterns();
    }

    // Group by domain
    const byDomain: Record<string, Pattern[]> = {};

    for (const pattern of patterns) {
      if (!byDomain[pattern.domain]) {
        byDomain[pattern.domain] = [];
      }
      byDomain[pattern.domain].push(pattern);
    }

    // Format as playbook
    let playbook = '# ACE Playbook\n\n';
    playbook += '*Auto-generated by ACE (Agentic Context Engineering)*\n';
    playbook += `*Patterns: ${patterns.length}, Domains: ${Object.keys(byDomain).length}*\n\n`;

    // Constitution (high-confidence principles)
    const constitution = patterns.filter(
      p => p.confidence >= this.config.ace.confidence_threshold_high
    );

    if (constitution.length > 0) {
      playbook += '## 📜 Constitution (High-Confidence Principles ≥70%)\n\n';
      for (const pattern of constitution) {
        playbook += `- **[${pattern.id}]** ${pattern.content}\n`;
        playbook += `  *Confidence: ${(pattern.confidence * 100).toFixed(1)}%, Observations: ${pattern.observations}*\n\n`;
      }
    }

    // Patterns by domain
    for (const [domain, domainPatterns] of Object.entries(byDomain)) {
      const title = domain.toUpperCase().replace(/-/g, ' ');
      playbook += `## ${title}\n\n`;

      for (const pattern of domainPatterns) {
        playbook += `- **[${pattern.id}]** ${pattern.content}\n`;

        if (pattern.evidence.length > 0) {
          playbook += `  *Evidence: ${pattern.evidence[0].substring(0, 100)}...*\n`;
        }

        playbook += `  *Confidence: ${(pattern.confidence * 100).toFixed(1)}%*\n\n`;
      }
    }

    return playbook;
  }
}
