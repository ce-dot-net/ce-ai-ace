/**
 * ACE Pattern Definitions
 *
 * Based on Stanford/SambaNova/UC Berkeley research (arXiv:2510.04618v1)
 *
 * Each pattern has:
 * - id: Unique identifier
 * - name: Human-readable name
 * - regex: Pattern detection regex
 * - domain: Categorization (e.g., 'python-typing', 'react-patterns')
 * - type: 'helpful' or 'harmful'
 * - description: What this pattern does
 */

module.exports = {
  python: [
    {
      id: 'py-001',
      name: 'Use TypedDict for configs',
      regex: /class\s+\w*Config\w*\(TypedDict\)/,
      domain: 'python-typing',
      type: 'helpful',
      description: 'Define configuration with TypedDict for type safety and IDE support'
    },
    {
      id: 'py-002',
      name: 'Validate API responses',
      regex: /requests\.(get|post|put|delete)\([^)]*\)(?!\s*\.raise_for_status)/,
      domain: 'python-api',
      type: 'helpful',
      description: 'Always check status codes after API calls to handle errors properly'
    },
    {
      id: 'py-003',
      name: 'Avoid bare except',
      regex: /except\s*:/,
      domain: 'python-error-handling',
      type: 'harmful',
      description: 'Bare except catches system exits and keyboard interrupts, making debugging difficult'
    },
    {
      id: 'py-004',
      name: 'Use context managers for files',
      regex: /with\s+open\([^)]+\)\s+as\s+\w+:/,
      domain: 'python-resources',
      type: 'helpful',
      description: 'Use with statement for automatic resource cleanup and proper file handling'
    },
    {
      id: 'py-005',
      name: 'Use asyncio.gather for parallel requests',
      regex: /asyncio\.gather\(/,
      domain: 'python-async',
      type: 'helpful',
      description: 'Run multiple independent async calls concurrently for better performance'
    },
    {
      id: 'py-006',
      name: 'Use dataclasses for data structures',
      regex: /@dataclass/,
      domain: 'python-typing',
      type: 'helpful',
      description: 'Use dataclasses for clean, type-safe data structures with less boilerplate'
    },
    {
      id: 'py-007',
      name: 'Use f-strings for formatting',
      regex: /f["'][^"']*{[^}]+}[^"']*["']/,
      domain: 'python-best-practices',
      type: 'helpful',
      description: 'F-strings are more readable and performant than .format() or % formatting'
    },
    {
      id: 'py-008',
      name: 'Avoid mutable default arguments',
      regex: /def\s+\w+\([^)]*=\s*(\[\]|\{\})[^)]*\):/,
      domain: 'python-error-handling',
      type: 'harmful',
      description: 'Mutable default arguments are shared across function calls, causing unexpected behavior'
    }
  ],

  javascript: [
    {
      id: 'js-001',
      name: 'Wrap fetch in try-catch',
      regex: /try\s*{[^}]*fetch\([^)]*\)/s,
      domain: 'javascript-error-handling',
      type: 'helpful',
      description: 'Handle network errors in async operations to prevent unhandled promise rejections'
    },
    {
      id: 'js-002',
      name: 'Use custom hooks for data fetching',
      regex: /function\s+use[A-Z]\w*\([^)]*\)\s*{[^}]*fetch/s,
      domain: 'react-patterns',
      type: 'helpful',
      description: 'Encapsulate data fetching logic in custom hooks for reusability and cleaner components'
    },
    {
      id: 'js-003',
      name: 'Avoid direct state mutation',
      regex: /this\.state\.\w+\s*=/,
      domain: 'react-patterns',
      type: 'harmful',
      description: 'Mutating state directly bypasses React rendering cycle and causes bugs'
    },
    {
      id: 'js-004',
      name: 'Use const for immutable values',
      regex: /const\s+[A-Z_][A-Z0-9_]*\s*=/,
      domain: 'javascript-best-practices',
      type: 'helpful',
      description: 'Use const for values that should not change to prevent accidental reassignment'
    },
    {
      id: 'js-005',
      name: 'Use async/await over promise chains',
      regex: /async\s+(function|\([^)]*\)\s*=>)/,
      domain: 'javascript-async',
      type: 'helpful',
      description: 'Async/await syntax is more readable than .then() chains for async operations'
    },
    {
      id: 'js-006',
      name: 'Use optional chaining',
      regex: /\?\./,
      domain: 'javascript-best-practices',
      type: 'helpful',
      description: 'Optional chaining prevents errors when accessing properties on potentially null/undefined objects'
    },
    {
      id: 'js-007',
      name: 'Use nullish coalescing',
      regex: /\?\?/,
      domain: 'javascript-best-practices',
      type: 'helpful',
      description: 'Nullish coalescing (??) only checks for null/undefined, not falsy values like 0 or empty string'
    },
    {
      id: 'js-008',
      name: 'Avoid var declarations',
      regex: /\bvar\s+\w+/,
      domain: 'javascript-best-practices',
      type: 'harmful',
      description: 'Var has function scope and hoisting issues; use let/const with block scope instead'
    }
  ],

  typescript: [
    {
      id: 'ts-001',
      name: 'Use interface for object shapes',
      regex: /interface\s+\w+\s*{/,
      domain: 'typescript-types',
      type: 'helpful',
      description: 'Interfaces are extensible and provide clear contracts for object shapes'
    },
    {
      id: 'ts-002',
      name: 'Use type guards',
      regex: /function\s+is\w+\([^)]*\):\s*\w+\s+is\s+\w+/,
      domain: 'typescript-types',
      type: 'helpful',
      description: 'Type guards provide runtime type checking with compile-time type narrowing'
    },
    {
      id: 'ts-003',
      name: 'Use generics for reusable functions',
      regex: /function\s+\w+<[^>]+>\(/,
      domain: 'typescript-types',
      type: 'helpful',
      description: 'Generics enable type-safe reusable functions without losing type information'
    },
    {
      id: 'ts-004',
      name: 'Avoid any type',
      regex: /:\s*any\b/,
      domain: 'typescript-types',
      type: 'harmful',
      description: 'Using any defeats TypeScript\'s type checking; use unknown or specific types instead'
    }
  ],

  /**
   * Detect programming language from file path
   * @param {string} filePath - Path to the file
   * @returns {string} Language identifier or 'unknown'
   */
  getLanguage(filePath) {
    if (!filePath) return 'unknown';
    if (/\.py$/.test(filePath)) return 'python';
    if (/\.jsx?$/.test(filePath)) return 'javascript';
    if (/\.tsx?$/.test(filePath)) return 'typescript';
    return 'unknown';
  },

  /**
   * Get patterns for a specific language
   * @param {string} language - Language identifier
   * @returns {Array} Array of pattern definitions
   */
  getPatterns(language) {
    return this[language] || [];
  },

  /**
   * Get all patterns across all languages
   * @returns {Array} Array of all pattern definitions
   */
  getAllPatterns() {
    return [
      ...this.python,
      ...this.javascript,
      ...this.typescript
    ];
  }
};
