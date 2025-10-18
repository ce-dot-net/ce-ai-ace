/**
 * ACE Reflector
 *
 * Discovers patterns from raw code using MCP Sampling (Claude invocation).
 * ACE paper: "The Reflector discovers patterns through iterative refinement."
 */

import { Insight } from '../types.js';
import { ACEConfig } from '../config.js';
import { ACEStorage } from '../storage/index.js';

export class Reflector {
  public storage: ACEStorage; // Public for access in tools
  private config: ACEConfig;

  constructor(storage: ACEStorage, config: ACEConfig) {
    this.storage = storage;
    this.config = config;
  }

  /**
   * Discover patterns from code using MCP sampling
   *
   * ACE paper: Reflector analyzes code and extracts patterns iteratively
   */
  async reflect(
    code: string,
    language: string,
    filePath: string,
    server?: any
  ): Promise<Insight[]> {
    if (!server) {
      throw new Error('MCP server required for reflection (sampling)');
    }

    // Get existing patterns for context (avoid rediscovery)
    const existingPatterns = await this.storage.getAllPatterns();
    const constitution = existingPatterns.filter(
      p => p.confidence >= this.config.ace.confidence_threshold_high
    );

    // Build Reflector prompt (ACE paper: analyze code → discover patterns)
    const prompt = this.buildReflectorPrompt(
      code,
      language,
      filePath,
      constitution
    );

    try {
      // MCP Sampling: Invoke Claude to discover patterns
      const response = await server.createMessage({
        messages: [
          {
            role: 'user',
            content: { type: 'text', text: prompt },
          },
        ],
        maxTokens: 2000,
      });

      // Parse insights from response
      const insights = this.parseInsights(response.content.text);
      return insights;
    } catch (error) {
      console.error('Reflection failed:', error);
      return [];
    }
  }

  /**
   * Build Reflector prompt for pattern discovery
   *
   * ACE paper: "The Reflector discovers patterns from raw code"
   */
  private buildReflectorPrompt(
    code: string,
    language: string,
    filePath: string,
    constitution: any[]
  ): string {
    const constitutionText = constitution.length > 0
      ? `\n## Known High-Confidence Principles (≥70%)\n\n${constitution
          .map(p => `- [${p.id}] ${p.content}`)
          .join('\n')}`
      : '';

    return `# ACE Reflector: Pattern Discovery

You are the **Reflector** component of the ACE (Agentic Context Engineering) system.
Your job is to analyze code and discover reusable patterns, strategies, or principles.

## ACE Research Paper Guidelines

1. **Discover patterns from raw code** (not pre-detected)
2. **Focus on actionable insights** that can guide future coding
3. **Avoid duplicating existing high-confidence patterns** (see below)
4. **Provide concrete evidence** (code snippets)
5. **Categorize by domain** (error-handling, api-usage, code-snippets, etc.)

${constitutionText}

## Code to Analyze

**File**: \`${filePath}\`
**Language**: ${language}

\`\`\`${language}
${code.substring(0, 5000)}${code.length > 5000 ? '\n...(truncated)...' : ''}
\`\`\`

## Your Task

Discover 1-3 patterns from this code. For each pattern, provide:

1. **pattern_name**: Short descriptive name (e.g., "error-wrapping-with-context")
2. **description**: Actionable principle (e.g., "Wrap errors with context before rethrowing")
3. **domain**: Category (strategies-and-rules, code-snippets, error-handling, api-usage, troubleshooting, context)
4. **evidence**: Code snippet demonstrating the pattern
5. **reasoning**: Why this pattern is helpful or harmful
6. **helpful**: true if beneficial pattern, false otherwise
7. **harmful**: true if anti-pattern, false otherwise

**Output Format (JSON array)**:

\`\`\`json
{
  "patterns": [
    {
      "pattern_name": "descriptive-name",
      "description": "Actionable principle or strategy",
      "domain": "error-handling",
      "evidence": "const result = await fn().catch(e => wrap(e, context));",
      "reasoning": "Wrapping errors preserves stack traces and adds context",
      "helpful": true,
      "harmful": false
    }
  ]
}
\`\`\`

**IMPORTANT**: Return ONLY the JSON object, no additional text.`;
  }

  /**
   * Parse insights from Claude response
   */
  private parseInsights(responseText: string): Insight[] {
    try {
      // Extract JSON from response (handle markdown code blocks)
      const jsonMatch = responseText.match(/```json\s*([\s\S]*?)\s*```/) ||
                       responseText.match(/```\s*([\s\S]*?)\s*```/) ||
                       [null, responseText];

      const json = JSON.parse(jsonMatch[1] || responseText);
      const patterns = json.patterns || [];

      return patterns.map((p: any) => ({
        pattern_name: p.pattern_name || 'unnamed-pattern',
        description: p.description || '',
        domain: p.domain || 'general',
        evidence: p.evidence || '',
        reasoning: p.reasoning || '',
        helpful: p.helpful !== false, // Default to true
        harmful: p.harmful === true,  // Default to false
      }));
    } catch (error) {
      console.error('Failed to parse insights:', error);
      console.error('Response:', responseText);
      return [];
    }
  }

  /**
   * Offline training: Discover patterns from historical commits
   *
   * ACE paper: "Multi-epoch training on historical codebase"
   */
  async trainOffline(
    maxCommits: number,
    server?: any
  ): Promise<{ insights: Insight[]; filesProcessed: number }> {
    if (!server) {
      throw new Error('MCP server required for offline training');
    }

    // Get recent commit hashes (ACE paper: git history analysis)
    const { execSync } = await import('child_process');
    const commits = execSync(`git log --pretty=format:%h --max-count=${maxCommits}`)
      .toString()
      .trim()
      .split('\n');

    const allInsights: Insight[] = [];
    let filesProcessed = 0;

    for (const commit of commits) {
      console.error(`\n📊 Analyzing commit ${commit}...`);

      // Get changed files in commit
      const files = execSync(`git diff-tree --no-commit-id --name-only -r ${commit}`)
        .toString()
        .trim()
        .split('\n')
        .filter(f => this.isCodeFile(f));

      for (const file of files.slice(0, 5)) { // Max 5 files per commit
        try {
          // Get file content at commit
          const code = execSync(`git show ${commit}:${file}`).toString();
          const language = this.detectLanguage(file);

          // Discover patterns
          const insights = await this.reflect(code, language, file, server);
          allInsights.push(...insights);
          filesProcessed++;

          console.error(`  ✅ ${file}: ${insights.length} patterns`);
        } catch (error) {
          console.error(`  ⏭️  ${file}: skipped (${(error as Error).message})`);
        }
      }
    }

    return { insights: allInsights, filesProcessed };
  }

  /**
   * Check if file is a code file
   */
  private isCodeFile(file: string): boolean {
    const codeExtensions = ['.ts', '.js', '.tsx', '.jsx', '.py', '.go', '.java', '.rs', '.c', '.cpp'];
    return codeExtensions.some(ext => file.endsWith(ext));
  }

  /**
   * Detect programming language from file extension
   */
  private detectLanguage(file: string): string {
    const ext = file.split('.').pop() || '';
    const languages: Record<string, string> = {
      ts: 'typescript',
      tsx: 'typescript',
      js: 'javascript',
      jsx: 'javascript',
      py: 'python',
      go: 'go',
      java: 'java',
      rs: 'rust',
      c: 'c',
      cpp: 'cpp',
    };
    return languages[ext] || ext;
  }
}
