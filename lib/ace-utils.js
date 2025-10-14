/**
 * ACE MCP Utilities
 *
 * Communication layer for Memory Bank and Sequential Thinking MCPs
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 */

const { spawn } = require('child_process');

/**
 * Call an MCP server with JSON-RPC
 * @param {string} server - 'memory-bank' or 'sequential-thinking'
 * @param {string} method - Method name
 * @param {Object} params - Method parameters
 * @returns {Promise<Object>} Response from MCP server
 */
async function callMCP(server, method, params) {
  return new Promise((resolve, reject) => {
    const serverCommand = server === 'memory-bank'
      ? '@modelcontextprotocol/server-memory'
      : '@modelcontextprotocol/server-sequential-thinking';

    const mcpProcess = spawn('npx', ['-y', serverCommand]);
    let responseData = '';
    let errorData = '';

    mcpProcess.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    mcpProcess.stderr.on('data', (data) => {
      errorData += data.toString();
    });

    mcpProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`MCP call failed (code ${code}): ${errorData}`));
      } else {
        try {
          const response = JSON.parse(responseData);
          if (response.error) {
            reject(new Error(`MCP error: ${JSON.stringify(response.error)}`));
          } else {
            resolve(response.result || response);
          }
        } catch (e) {
          reject(new Error(`Invalid JSON response: ${responseData}`));
        }
      }
    });

    const request = JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params
    });

    mcpProcess.stdin.write(request + '\n');
    mcpProcess.stdin.end();
  });
}

/**
 * Store a pattern in memory-bank MCP
 * @param {Object} pattern - Pattern object to store
 * @returns {Promise<Object>} Storage result
 */
async function storePattern(pattern) {
  try {
    return await callMCP('memory-bank', 'store', {
      key: `pattern:${pattern.id}`,
      value: JSON.stringify(pattern),
      metadata: {
        domain: pattern.domain,
        type: pattern.type,
        confidence: pattern.confidence || 0,
        language: pattern.language || 'unknown'
      }
    });
  } catch (error) {
    console.error(`Failed to store pattern ${pattern.id}:`, error.message);
    throw error;
  }
}

/**
 * Retrieve a pattern from memory-bank MCP
 * @param {string} patternId - Pattern identifier
 * @returns {Promise<Object|null>} Pattern object or null if not found
 */
async function getPattern(patternId) {
  try {
    const result = await callMCP('memory-bank', 'retrieve', {
      key: `pattern:${patternId}`
    });

    if (result && result.value) {
      return typeof result.value === 'string'
        ? JSON.parse(result.value)
        : result.value;
    }
    return null;
  } catch (error) {
    if (error.message.includes('not found')) {
      return null;
    }
    console.error(`Failed to get pattern ${patternId}:`, error.message);
    throw error;
  }
}

/**
 * List all patterns from memory-bank MCP
 * @param {Object} filters - Optional filters
 * @returns {Promise<Array>} Array of pattern objects
 */
async function listPatterns(filters = {}) {
  try {
    const result = await callMCP('memory-bank', 'list', {
      prefix: 'pattern:',
      ...filters
    });

    if (!result || !Array.isArray(result)) {
      return [];
    }

    return result.map(item => {
      const value = item.value || item;
      return typeof value === 'string' ? JSON.parse(value) : value;
    });
  } catch (error) {
    console.error('Failed to list patterns:', error.message);
    return [];
  }
}

/**
 * Delete a pattern from memory-bank MCP
 * @param {string} patternId - Pattern identifier
 * @returns {Promise<boolean>} Success status
 */
async function deletePattern(patternId) {
  try {
    await callMCP('memory-bank', 'delete', {
      key: `pattern:${patternId}`
    });
    return true;
  } catch (error) {
    console.error(`Failed to delete pattern ${patternId}:`, error.message);
    return false;
  }
}

/**
 * Invoke Reflector using sequential-thinking MCP
 * This is where the LLM analyzes pattern effectiveness
 *
 * @param {Object} context - Reflection context
 * @returns {Promise<Object>} Reflection results
 */
async function reflect(context) {
  try {
    const reflectionResult = await callMCP('sequential-thinking', 'think', {
      prompt: context.reflectionPrompt,
      context: JSON.stringify(context.taskContext)
    });

    return reflectionResult;
  } catch (error) {
    console.error('Reflection failed:', error.message);

    // Fallback: Use heuristics based on test results
    const testPassed = context.taskContext?.evidence?.testStatus === 'passed';

    return {
      patterns_analyzed: (context.taskContext?.patterns || []).map(p => ({
        pattern_id: p.id,
        applied_correctly: true,
        contributed_to: testPassed ? 'success' : 'uncertain',
        confidence: testPassed ? 0.7 : 0.5,
        insight: testPassed
          ? `Pattern applied successfully. Tests passed.`
          : `Pattern applied but outcome uncertain. No test feedback available.`,
        recommendation: 'Enable sequential-thinking MCP for deeper analysis'
      })),
      meta_insights: [
        'Reflection unavailable - using test results only',
        'Install sequential-thinking MCP for better insights'
      ]
    };
  }
}

module.exports = {
  callMCP,
  storePattern,
  getPattern,
  listPatterns,
  deletePattern,
  reflect
};
