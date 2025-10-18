/**
 * ACE MCP Tools
 *
 * Exposes ACE functionality as MCP tools that can be called by Claude Code.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { ACEStorage } from '../storage/index.js';
import { ACEConfig } from '../config.js';
import { Curator } from '../curator/index.js';
import { Reflector } from '../reflector/index.js';

export function registerTools(
  server: Server,
  storage: ACEStorage,
  config: ACEConfig
): void {
  const curator = new Curator(storage, config);
  const reflector = new Reflector(storage, config);

  // We'll pass server to handlers that need sampling

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: 'ace_reflect',
          description: 'Discover patterns from code using ACE Reflector (invokes Claude for analysis)',
          inputSchema: {
            type: 'object',
            properties: {
              code: {
                type: 'string',
                description: 'Code to analyze for patterns',
              },
              language: {
                type: 'string',
                description: 'Programming language (typescript, javascript, python, etc.)',
              },
              file_path: {
                type: 'string',
                description: 'File path for context',
              },
            },
            required: ['code', 'language', 'file_path'],
          },
        },
        {
          name: 'ace_train_offline',
          description: 'Run multi-epoch offline training on git history (ACE paper: historical codebase analysis)',
          inputSchema: {
            type: 'object',
            properties: {
              max_commits: {
                type: 'number',
                description: 'Number of recent commits to analyze',
                default: 50,
              },
            },
          },
        },
        {
          name: 'ace_get_patterns',
          description: 'Get patterns from ACE database with optional filtering',
          inputSchema: {
            type: 'object',
            properties: {
              domain: {
                type: 'string',
                description: 'Filter by domain (optional)',
              },
              min_confidence: {
                type: 'number',
                description: 'Minimum confidence threshold (0-1, optional)',
              },
            },
          },
        },
        {
          name: 'ace_get_playbook',
          description: 'Generate ACE playbook (ACE paper Figure 3 format) with optional task filtering',
          inputSchema: {
            type: 'object',
            properties: {
              task_hint: {
                type: 'string',
                description: 'Task description for semantic filtering (optional)',
              },
            },
          },
        },
        {
          name: 'ace_status',
          description: 'Get ACE pattern database statistics',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'ace_clear',
          description: 'Clear ACE pattern database (requires confirmation)',
          inputSchema: {
            type: 'object',
            properties: {
              confirm: {
                type: 'boolean',
                description: 'Must be true to confirm deletion',
              },
            },
            required: ['confirm'],
          },
        },
      ],
    };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'ace_reflect':
          return await handleReflect(args, reflector, curator, server);

        case 'ace_train_offline':
          return await handleTrainOffline(args, reflector, curator, server);

        case 'ace_get_patterns':
          return await handleGetPatterns(args, storage);

        case 'ace_get_playbook':
          return await handleGetPlaybook(args, curator);

        case 'ace_status':
          return await handleStatus(storage);

        case 'ace_clear':
          return await handleClear(args, storage);

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${(error as Error).message}`,
          },
        ],
        isError: true,
      };
    }
  });
}

/**
 * Handle ace_reflect tool call
 */
async function handleReflect(
  args: any,
  reflector: Reflector,
  curator: Curator,
  server: Server
): Promise<any> {
  const { code, language, file_path } = args;

  console.error(`\n🔍 ACE Reflector analyzing ${file_path}...`);

  // Discover patterns (pass server for sampling)
  const insights = await reflector.reflect(code, language, file_path, server);

  console.error(`📊 Discovered ${insights.length} insights`);

  // Curate into patterns
  const patterns = await curator.curate(insights);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          {
            insights: insights.length,
            patterns_discovered: insights.length,
            patterns_merged: insights.length - patterns.filter(p =>
              insights.some(i => i.pattern_name === p.name)
            ).length,
            total_patterns: patterns.length,
          },
          null,
          2
        ),
      },
    ],
  };
}

/**
 * Handle ace_train_offline tool call
 */
async function handleTrainOffline(
  args: any,
  reflector: Reflector,
  curator: Curator,
  server: Server
): Promise<any> {
  const maxCommits = args.max_commits || 50;

  console.error(`\n🏋️  ACE Offline Training (max ${maxCommits} commits)...`);

  const patternsBefore = await curator.getConstitution();
  const statsBefore = await reflector.storage.getStats();

  // Train on git history (pass server for sampling)
  const { insights, filesProcessed } = await reflector.trainOffline(maxCommits, server);

  console.error(`\n📊 Curating ${insights.length} insights...`);

  // Curate all insights
  const patternsAfter = await curator.curate(insights);
  const statsAfter = await reflector.storage.getStats();

  const result = {
    files_processed: filesProcessed,
    insights_discovered: insights.length,
    patterns_before: patternsBefore.length,
    patterns_after: patternsAfter.length,
    avg_confidence_before: statsBefore.total_patterns > 0
      ? (statsBefore.high_confidence * 0.85 + statsBefore.medium_confidence * 0.5) / statsBefore.total_patterns
      : 0,
    avg_confidence_after: statsAfter.total_patterns > 0
      ? (statsAfter.high_confidence * 0.85 + statsAfter.medium_confidence * 0.5) / statsAfter.total_patterns
      : 0,
  };

  console.error('\n✅ Training complete!');
  console.error(`   Files: ${result.files_processed}`);
  console.error(`   Insights: ${result.insights_discovered}`);
  console.error(`   Patterns: ${result.patterns_before} → ${result.patterns_after}`);

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  };
}

/**
 * Handle ace_get_patterns tool call
 */
async function handleGetPatterns(args: any, storage: ACEStorage): Promise<any> {
  const { domain, min_confidence } = args;

  let patterns = domain
    ? await storage.getPatternsByDomain(domain)
    : await storage.getAllPatterns();

  if (min_confidence !== undefined) {
    patterns = patterns.filter(p => p.confidence >= min_confidence);
  }

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(
          patterns.map(p => ({
            id: p.id,
            name: p.name,
            domain: p.domain,
            content: p.content,
            confidence: p.confidence,
            observations: p.observations,
            harmful: p.harmful,
          })),
          null,
          2
        ),
      },
    ],
  };
}

/**
 * Handle ace_get_playbook tool call
 */
async function handleGetPlaybook(args: any, curator: Curator): Promise<any> {
  const { task_hint } = args;

  const playbook = await curator.formatPlaybook(task_hint);

  return {
    content: [
      {
        type: 'text',
        text: playbook,
      },
    ],
  };
}

/**
 * Handle ace_status tool call
 */
async function handleStatus(storage: ACEStorage): Promise<any> {
  const stats = await storage.getStats();

  const output = `# ACE Pattern Database Status

**Total Patterns**: ${stats.total_patterns}
- High Confidence (≥70%): ${stats.high_confidence}
- Medium Confidence (30-70%): ${stats.medium_confidence}
- Low Confidence (<30%): ${stats.low_confidence}

**Domains**: ${stats.domains.join(', ') || 'none'}

**Database**: \`.ace-memory/patterns.db\`
`;

  return {
    content: [
      {
        type: 'text',
        text: output,
      },
    ],
  };
}

/**
 * Handle ace_clear tool call
 */
async function handleClear(args: any, storage: ACEStorage): Promise<any> {
  const { confirm } = args;

  if (!confirm) {
    throw new Error('Must set confirm=true to clear database');
  }

  await storage.clear();

  return {
    content: [
      {
        type: 'text',
        text: '✅ ACE pattern database cleared',
      },
    ],
  };
}
