#!/usr/bin/env node

/**
 * Test script for ACE MCP server package
 * Tests all functionality before publishing to npm
 */

const { spawn } = require('child_process');
const { promisify } = require('util');
const sleep = promisify(setTimeout);

const tests = [];
let passedTests = 0;
let failedTests = 0;

function log(message, type = 'info') {
  const colors = {
    info: '\x1b[36m',    // Cyan
    success: '\x1b[32m', // Green
    error: '\x1b[31m',   // Red
    warn: '\x1b[33m',    // Yellow
  };
  const reset = '\x1b[0m';
  console.log(`${colors[type]}${message}${reset}`);
}

function addTest(name, fn) {
  tests.push({ name, fn });
}

async function runTests() {
  log('\n🧪 ACE MCP Server Package Tests\n', 'info');
  log('='.repeat(60), 'info');

  for (const test of tests) {
    try {
      log(`\n▶ Testing: ${test.name}`, 'info');
      await test.fn();
      log(`✅ PASS: ${test.name}`, 'success');
      passedTests++;
    } catch (error) {
      log(`❌ FAIL: ${test.name}`, 'error');
      log(`   Error: ${error.message}`, 'error');
      failedTests++;
    }
  }

  log('\n' + '='.repeat(60), 'info');
  log(`\n📊 Test Results:`, 'info');
  log(`   Total: ${tests.length}`, 'info');
  log(`   Passed: ${passedTests}`, 'success');
  log(`   Failed: ${failedTests}`, failedTests > 0 ? 'error' : 'success');

  if (failedTests === 0) {
    log('\n🎉 All tests passed! Package is ready to publish.', 'success');
    process.exit(0);
  } else {
    log('\n⚠️  Some tests failed. Fix issues before publishing.', 'error');
    process.exit(1);
  }
}

// Test 1: Binary exists
addTest('Binary command exists', async () => {
  const which = spawn('which', ['ce-ai-ace']);
  const chunks = [];

  for await (const chunk of which.stdout) {
    chunks.push(chunk);
  }

  await new Promise((resolve, reject) => {
    which.on('close', (code) => {
      if (code === 0) {
        const path = Buffer.concat(chunks).toString().trim();
        log(`   Binary found at: ${path}`, 'info');
        resolve();
      } else {
        reject(new Error('Binary not found in PATH'));
      }
    });
  });
});

// Test 2: MCP server starts
addTest('MCP server starts successfully', async () => {
  const server = spawn('ce-ai-ace');
  let stderr = '';

  server.stderr.on('data', (data) => {
    stderr += data.toString();
  });

  await sleep(3000); // Wait for server to initialize

  if (!stderr.includes('ACE MCP Server ready for connections')) {
    server.kill();
    throw new Error('Server did not start properly');
  }

  log('   Server initialized successfully', 'info');
  server.kill();
});

// Test 3: Server responds to initialize
addTest('Server responds to MCP initialize', async () => {
  const server = spawn('ce-ai-ace');
  let response = '';

  server.stdout.on('data', (data) => {
    response += data.toString();
  });

  await sleep(3000); // Wait for server ready

  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'test', version: '1.0' }
    }
  };

  server.stdin.write(JSON.stringify(initRequest) + '\n');

  await sleep(1000);

  if (response.length === 0) {
    server.kill();
    throw new Error('No response from server');
  }

  log('   Server responded to initialize', 'info');
  server.kill();
});

// Test 4: Server lists tools
addTest('Server lists all 6 MCP tools', async () => {
  const server = spawn('ce-ai-ace');
  let response = '';

  server.stdout.on('data', (data) => {
    response += data.toString();
  });

  await sleep(3000);

  // Send initialize
  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'test', version: '1.0' }
    }
  };
  server.stdin.write(JSON.stringify(initRequest) + '\n');

  await sleep(500);

  // Send tools/list
  const toolsRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  };
  server.stdin.write(JSON.stringify(toolsRequest) + '\n');

  await sleep(1000);

  const expectedTools = [
    'ace_reflect',
    'ace_train_offline',
    'ace_get_patterns',
    'ace_get_playbook',
    'ace_status',
    'ace_clear'
  ];

  for (const tool of expectedTools) {
    if (!response.includes(tool)) {
      server.kill();
      throw new Error(`Missing tool: ${tool}`);
    }
  }

  log(`   All 6 tools found: ${expectedTools.join(', ')}`, 'info');
  server.kill();
});

// Test 5: Package metadata
addTest('Package metadata is correct', async () => {
  const pkg = require('./package.json');

  if (pkg.name !== '@ce-dot-net/ce-ai-ace') {
    throw new Error(`Wrong package name: ${pkg.name}`);
  }

  if (!pkg.bin['ce-ai-ace']) {
    throw new Error('Missing binary definition');
  }

  if (!pkg.keywords.includes('mcp')) {
    throw new Error('Missing "mcp" keyword');
  }

  if (pkg.license !== 'MIT') {
    throw new Error('Wrong license');
  }

  log(`   Name: ${pkg.name}`, 'info');
  log(`   Version: ${pkg.version}`, 'info');
  log(`   Binary: ce-ai-ace`, 'info');
  log(`   License: ${pkg.license}`, 'info');
});

// Test 6: Package files whitelist
addTest('Package files whitelist is correct', async () => {
  const pkg = require('./package.json');

  if (!pkg.files) {
    throw new Error('Missing files whitelist');
  }

  const requiredFiles = ['dist/**/*', 'README.md', 'package.json'];
  for (const file of requiredFiles) {
    if (!pkg.files.includes(file)) {
      throw new Error(`Missing from files whitelist: ${file}`);
    }
  }

  log(`   Files whitelist: ${pkg.files.join(', ')}`, 'info');
});

// Run all tests
runTests().catch((error) => {
  log(`\n❌ Test runner failed: ${error.message}`, 'error');
  process.exit(1);
});
