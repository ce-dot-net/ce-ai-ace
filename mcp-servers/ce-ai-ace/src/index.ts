#!/usr/bin/env node

/**
 * ACE Pattern Learning MCP Server
 *
 * Implements Agentic Context Engineering (ACE) framework for self-improving LLM contexts.
 * Based on research: https://arxiv.org/abs/2510.04618
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { ACEStorage } from './storage/index.js';
import { ACEConfig, getConfig } from './config.js';
import { registerTools } from './tools/index.js';
import { registerResources } from './resources/index.js';

const server = new Server(
  {
    name: 'ace-pattern-learning',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      sampling: {}, // Enable MCP sampling for Claude invocation
    },
  }
);

async function main() {
  const config: ACEConfig = getConfig();
  const storage = new ACEStorage(config);

  await storage.initialize();

  console.error('🧠 ACE Pattern Learning MCP Server starting...');
  console.error(`📊 Storage: ${config.storage.type} (${config.storage.path})`);
  console.error(`🎯 Similarity threshold: ${config.ace.similarity_threshold * 100}%`);
  console.error(`✅ Server initialized successfully\n`);

  // Register tools and resources
  registerTools(server, storage, config);
  registerResources(server, storage, config);

  // Start server
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('🚀 ACE MCP Server ready for connections');
}

main().catch((error) => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});
