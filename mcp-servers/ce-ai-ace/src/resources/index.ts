/**
 * ACE MCP Resources
 *
 * Exposes ACE data as readable resources via ace:// URIs.
 * ACE paper: Patterns and playbooks accessible as structured data.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { ACEStorage } from '../storage/index.js';
import { ACEConfig } from '../config.js';
import { Curator } from '../curator/index.js';

export function registerResources(
  server: Server,
  storage: ACEStorage,
  config: ACEConfig
): void {
  const curator = new Curator(storage, config);

  // List available resources
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    const stats = await storage.getStats();

    return {
      resources: [
        {
          uri: 'ace://patterns/all',
          name: 'All ACE Patterns',
          description: `All ${stats.total_patterns} patterns in the database`,
          mimeType: 'application/json',
        },
        {
          uri: 'ace://patterns/constitution',
          name: 'ACE Constitution',
          description: `High-confidence principles (≥70%): ${stats.high_confidence} patterns`,
          mimeType: 'application/json',
        },
        {
          uri: 'ace://playbook',
          name: 'ACE Playbook',
          description: 'Auto-generated playbook (ACE paper Figure 3 format)',
          mimeType: 'text/markdown',
        },
        {
          uri: 'ace://stats',
          name: 'ACE Statistics',
          description: 'Pattern database statistics',
          mimeType: 'application/json',
        },
        ...stats.domains.map(domain => ({
          uri: `ace://patterns/domain/${domain}`,
          name: `Patterns: ${domain}`,
          description: `All patterns in ${domain} domain`,
          mimeType: 'application/json',
        })),
      ],
    };
  });

  // Read resource content
  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;

    try {
      if (uri === 'ace://patterns/all') {
        return await handleAllPatterns(storage);
      }

      if (uri === 'ace://patterns/constitution') {
        return await handleConstitution(curator);
      }

      if (uri === 'ace://playbook') {
        return await handlePlaybook(curator);
      }

      if (uri === 'ace://stats') {
        return await handleStats(storage);
      }

      if (uri.startsWith('ace://patterns/domain/')) {
        const domain = uri.replace('ace://patterns/domain/', '');
        return await handleDomainPatterns(storage, domain);
      }

      throw new Error(`Unknown resource: ${uri}`);
    } catch (error) {
      return {
        contents: [
          {
            uri,
            mimeType: 'text/plain',
            text: `Error: ${(error as Error).message}`,
          },
        ],
      };
    }
  });
}

/**
 * Handle ace://patterns/all resource
 */
async function handleAllPatterns(storage: ACEStorage): Promise<any> {
  const patterns = await storage.getAllPatterns();

  return {
    contents: [
      {
        uri: 'ace://patterns/all',
        mimeType: 'application/json',
        text: JSON.stringify(patterns, null, 2),
      },
    ],
  };
}

/**
 * Handle ace://patterns/constitution resource
 */
async function handleConstitution(curator: Curator): Promise<any> {
  const constitution = await curator.getConstitution();

  return {
    contents: [
      {
        uri: 'ace://patterns/constitution',
        mimeType: 'application/json',
        text: JSON.stringify(constitution, null, 2),
      },
    ],
  };
}

/**
 * Handle ace://playbook resource
 */
async function handlePlaybook(curator: Curator): Promise<any> {
  const playbook = await curator.formatPlaybook();

  return {
    contents: [
      {
        uri: 'ace://playbook',
        mimeType: 'text/markdown',
        text: playbook,
      },
    ],
  };
}

/**
 * Handle ace://stats resource
 */
async function handleStats(storage: ACEStorage): Promise<any> {
  const stats = await storage.getStats();

  return {
    contents: [
      {
        uri: 'ace://stats',
        mimeType: 'application/json',
        text: JSON.stringify(stats, null, 2),
      },
    ],
  };
}

/**
 * Handle ace://patterns/domain/{domain} resource
 */
async function handleDomainPatterns(storage: ACEStorage, domain: string): Promise<any> {
  const patterns = await storage.getPatternsByDomain(domain);

  return {
    contents: [
      {
        uri: `ace://patterns/domain/${domain}`,
        mimeType: 'application/json',
        text: JSON.stringify(patterns, null, 2),
      },
    ],
  };
}
