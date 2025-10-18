/**
 * ACE Storage Layer
 *
 * Manages pattern storage with SQLite + embeddings for semantic similarity.
 */

import Database from 'better-sqlite3';
import { existsSync, mkdirSync } from 'fs';
import { dirname } from 'path';
import { Pattern, StorageBackend } from '../types.js';
import { ACEConfig } from '../config.js';
import { EmbeddingsEngine } from '../embeddings/index.js';

export class ACEStorage implements StorageBackend {
  private db!: Database.Database;
  private embeddings!: EmbeddingsEngine;
  private config: ACEConfig;

  constructor(config: ACEConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    // Ensure directory exists
    const dbDir = dirname(this.config.storage.path);
    if (!existsSync(dbDir)) {
      mkdirSync(dbDir, { recursive: true });
    }

    // Initialize SQLite
    this.db = new Database(this.config.storage.path);
    this.db.pragma('journal_mode = WAL');

    // Create schema
    this.createSchema();

    // Initialize embeddings engine
    this.embeddings = new EmbeddingsEngine(this.config);
    await this.embeddings.initialize();

    console.error('✅ Storage initialized');
  }

  private createSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS patterns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        content TEXT NOT NULL,
        confidence REAL NOT NULL,
        observations INTEGER NOT NULL DEFAULT 1,
        harmful INTEGER NOT NULL DEFAULT 0,
        evidence TEXT NOT NULL, -- JSON array
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        metadata TEXT -- JSON object
      );

      CREATE INDEX IF NOT EXISTS idx_patterns_domain ON patterns(domain);
      CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON patterns(confidence DESC);
      CREATE INDEX IF NOT EXISTS idx_patterns_observations ON patterns(observations DESC);

      CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_id TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_insights_pattern ON insights(pattern_id);
      CREATE INDEX IF NOT EXISTS idx_insights_timestamp ON insights(timestamp DESC);

      CREATE TABLE IF NOT EXISTS epochs (
        epoch INTEGER PRIMARY KEY,
        patterns_before INTEGER NOT NULL,
        patterns_after INTEGER NOT NULL,
        patterns_refined INTEGER NOT NULL,
        avg_confidence_before REAL NOT NULL,
        avg_confidence_after REAL NOT NULL,
        files_processed INTEGER NOT NULL,
        timestamp TEXT NOT NULL
      );
    `);
  }

  async addPattern(pattern: Pattern): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT INTO patterns (id, name, domain, content, confidence, observations, harmful, evidence, created_at, updated_at, metadata)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      pattern.id,
      pattern.name,
      pattern.domain,
      pattern.content,
      pattern.confidence,
      pattern.observations || 1,
      pattern.harmful || 0,
      JSON.stringify(pattern.evidence || []),
      pattern.created_at || new Date().toISOString(),
      pattern.updated_at || new Date().toISOString(),
      JSON.stringify(pattern.metadata || {})
    );

    // Add to vector store
    await this.embeddings.addPattern(pattern);
  }

  async getPattern(id: string): Promise<Pattern | null> {
    const stmt = this.db.prepare('SELECT * FROM patterns WHERE id = ?');
    const row = stmt.get(id) as any;

    if (!row) return null;

    return this.rowToPattern(row);
  }

  async getAllPatterns(): Promise<Pattern[]> {
    const stmt = this.db.prepare('SELECT * FROM patterns ORDER BY confidence DESC, observations DESC');
    const rows = stmt.all() as any[];

    return rows.map(row => this.rowToPattern(row));
  }

  async getPatternsByDomain(domain: string): Promise<Pattern[]> {
    const stmt = this.db.prepare('SELECT * FROM patterns WHERE domain = ? ORDER BY confidence DESC');
    const rows = stmt.all(domain) as any[];

    return rows.map(row => this.rowToPattern(row));
  }

  async updatePattern(id: string, updates: Partial<Pattern>): Promise<void> {
    const fields: string[] = [];
    const values: any[] = [];

    Object.entries(updates).forEach(([key, value]) => {
      if (key === 'evidence' || key === 'metadata') {
        fields.push(`${key} = ?`);
        values.push(JSON.stringify(value));
      } else if (key !== 'id' && key !== 'created_at') {
        fields.push(`${key} = ?`);
        values.push(value);
      }
    });

    fields.push('updated_at = ?');
    values.push(new Date().toISOString());
    values.push(id);

    const stmt = this.db.prepare(`UPDATE patterns SET ${fields.join(', ')} WHERE id = ?`);
    stmt.run(...values);

    // Update vector store if content changed
    if (updates.content) {
      const pattern = await this.getPattern(id);
      if (pattern) {
        await this.embeddings.updatePattern(pattern);
      }
    }
  }

  async deletePattern(id: string): Promise<void> {
    const stmt = this.db.prepare('DELETE FROM patterns WHERE id = ?');
    stmt.run(id);

    await this.embeddings.deletePattern(id);
  }

  async findSimilarPatterns(
    content: string,
    threshold: number
  ): Promise<Array<{ pattern: Pattern; similarity: number }>> {
    const similar = await this.embeddings.findSimilar(content, threshold);

    const results: Array<{ pattern: Pattern; similarity: number }> = [];

    for (const { id, similarity } of similar) {
      const pattern = await this.getPattern(id);
      if (pattern) {
        results.push({ pattern, similarity });
      }
    }

    return results;
  }

  async getStats(): Promise<{
    total_patterns: number;
    high_confidence: number;
    medium_confidence: number;
    low_confidence: number;
    domains: string[];
  }> {
    const totalStmt = this.db.prepare('SELECT COUNT(*) as count FROM patterns');
    const total = (totalStmt.get() as any).count;

    const highStmt = this.db.prepare(
      'SELECT COUNT(*) as count FROM patterns WHERE confidence >= ?'
    );
    const high = (highStmt.get(this.config.ace.confidence_threshold_high) as any).count;

    const mediumStmt = this.db.prepare(
      'SELECT COUNT(*) as count FROM patterns WHERE confidence >= ? AND confidence < ?'
    );
    const medium = (mediumStmt.get(
      this.config.ace.confidence_threshold_medium,
      this.config.ace.confidence_threshold_high
    ) as any).count;

    const domainsStmt = this.db.prepare('SELECT DISTINCT domain FROM patterns ORDER BY domain');
    const domainRows = domainsStmt.all() as any[];
    const domains = domainRows.map(row => row.domain);

    return {
      total_patterns: total,
      high_confidence: high,
      medium_confidence: medium,
      low_confidence: total - high - medium,
      domains,
    };
  }

  async clear(): Promise<void> {
    this.db.exec('DELETE FROM patterns');
    this.db.exec('DELETE FROM insights');
    this.db.exec('DELETE FROM epochs');

    await this.embeddings.clear();
  }

  private rowToPattern(row: any): Pattern {
    return {
      id: row.id,
      name: row.name,
      domain: row.domain,
      content: row.content,
      confidence: row.confidence,
      observations: row.observations,
      harmful: row.harmful,
      evidence: JSON.parse(row.evidence),
      created_at: row.created_at,
      updated_at: row.updated_at,
      metadata: row.metadata ? JSON.parse(row.metadata) : {},
    };
  }
}
