# ACE Plugin Architecture - Implementation Details

## Project Overview

**Name**: ace-orchestration-plugin
**Version**: 1.0.0
**Purpose**: Automatic pattern learning for Claude Code CLI using ACE framework
**Total LOC**: 1,307 lines across 19 files

## File Structure

```
ce-ai-ace/
├── config/
│   └── patterns.js              # 20+ pattern definitions
├── lib/
│   ├── patternDetector.js       # Regex detection engine
│   ├── curator.js               # Deterministic merging (CRITICAL)
│   ├── ace-utils.js             # MCP communication layer
│   └── generatePlaybook.js      # CLAUDE.md generator
├── agents/
│   └── reflector-prompt.md      # LLM reflection template
├── hooks/
│   ├── postToolUse.js           # Main ACE cycle orchestration
│   └── sessionEnd.js            # Cleanup & finalization
├── tests/
│   ├── patternDetector.test.js  # Pattern detection tests
│   └── curator.test.js          # Curator algorithm tests
├── docs/
│   └── ACE_RESEARCH.md          # Research summary
├── index.js                     # Plugin entry point
├── plugin.json                  # Plugin manifest
├── package.json                 # Dependencies
└── .mcp.json                    # MCP server configs
```

## Core Components

### 1. Pattern Detector (lib/patternDetector.js)

**Purpose**: Regex-based pattern detection in code

**Key Functions**:
- `detectPatterns(code, filePath)` - Detects patterns via regex
- `calculateConfidence(observations, successes)` - Computes confidence score
- `getPatternById(id)` - Retrieves pattern definition

**Languages Supported**:
- Python (.py) - 8 patterns
- JavaScript (.js, .jsx) - 8 patterns
- TypeScript (.ts, .tsx) - 4 patterns

**Example Patterns**:
```javascript
{
  id: 'py-001',
  name: 'Use TypedDict for configs',
  regex: /class\s+\w*Config\w*\(TypedDict\)/,
  domain: 'python-typing',
  type: 'helpful'
}
```

### 2. Curator (lib/curator.js) - CRITICAL COMPONENT

**Purpose**: Deterministic pattern merging (NO LLM!)

**Key Functions**:
- `calculateSimilarity(p1, p2)` - String similarity (60% name + 40% description)
- `curate(newPattern, existing)` - Decides merge/create/prune
- `mergePatterns(target, source)` - Combines patterns
- `deduplicate(patterns)` - Removes redundancy
- `prune(patterns)` - Removes low-confidence patterns

**Algorithm**:
```javascript
// 1. Find most similar pattern (same domain + type)
const bestMatch = findMostSimilar(newPattern, existingPatterns);

// 2. MERGE if >= 85% similar
if (bestMatch.similarity >= 0.85) {
  return { action: 'merge', targetId: bestMatch.id };
}

// 3. PRUNE if < 30% confidence after 10+ observations
if (observations >= 10 && confidence < 0.3) {
  return { action: 'prune' };
}

// 4. CREATE new pattern
return { action: 'create' };
```

**Thresholds**:
- `SIMILARITY_THRESHOLD = 0.85` (from research)
- `PRUNE_THRESHOLD = 0.3` (from research)
- `MIN_OBSERVATIONS = 10` (from research)

### 3. MCP Utils (lib/ace-utils.js)

**Purpose**: Communication with MCP servers

**MCP Servers Used**:
1. **memory-bank**: Pattern storage (persistent)
2. **sequential-thinking**: Reflector analysis (LLM)

**Key Functions**:
- `callMCP(server, method, params)` - Generic MCP call
- `storePattern(pattern)` - Save to memory-bank
- `getPattern(id)` - Retrieve from memory-bank
- `listPatterns()` - Query all patterns
- `reflect(context)` - Invoke sequential-thinking for analysis

### 4. Reflector Prompt (agents/reflector-prompt.md)

**Purpose**: Structured prompt for LLM pattern analysis

**Input Structure**:
```json
{
  "code": "source code",
  "patterns": [{"id", "name", "description"}],
  "evidence": {
    "testStatus": "passed|failed",
    "errorLogs": "string",
    "hasTests": boolean
  }
}
```

**Output Structure**:
```json
{
  "patterns_analyzed": [{
    "pattern_id": "string",
    "applied_correctly": boolean,
    "contributed_to": "success|failure|neutral",
    "confidence": 0.1-1.0,
    "insight": "Specific observation",
    "recommendation": "When to use/avoid"
  }]
}
```

**Quality Standards**:
- ✅ Evidence-based (reference specific code/tests)
- ✅ Specific (name exact lines/functions)
- ✅ Actionable recommendations
- ❌ No vague statements like "pattern worked well"

### 5. Playbook Generator (lib/generatePlaybook.js)

**Purpose**: Generates CLAUDE.md with confidence-based organization

**Structure**:
```markdown
# ACE Playbook

## 🎯 High-Confidence Patterns (≥70%)
[Patterns with confidence >= 0.7]

## 💡 Medium-Confidence Patterns (<70%)
[Patterns with confidence < 0.7]

## ⚠️ Anti-Patterns (AVOID)
[Harmful patterns]
```

**Features**:
- Confidence scoring
- Latest insights included
- Specific recommendations
- Timestamp tracking

### 6. PostToolUse Hook (hooks/postToolUse.js)

**Purpose**: Main ACE cycle orchestration (runs after each code operation)

**Flow**:
1. Extract code and file path from event
2. Detect patterns (regex-based)
3. Gather evidence (run tests)
4. Invoke Reflector (sequential-thinking MCP)
5. Curate each pattern (deterministic algorithm)
6. Update playbook

**Key Logic**:
```javascript
// For each detected pattern:
const newPattern = {
  id, name, domain, type, description, language,
  observations: 1,
  successes: analysis.contributed_to === 'success' ? 1 : 0,
  insights: [{ timestamp, insight, recommendation }]
};

const existingPatterns = await listPatterns();
const decision = curate(newPattern, existingPatterns);

if (decision.action === 'merge') {
  const merged = mergePatterns(target, newPattern);
  await storePattern(merged);
} else if (decision.action === 'create') {
  await storePattern(newPattern);
}
```

### 7. SessionEnd Hook (hooks/sessionEnd.js)

**Purpose**: Cleanup and finalization

**Flow**:
1. Get all patterns
2. Deduplicate (merge similar)
3. Prune low-confidence patterns
4. Store cleaned patterns
5. Generate final playbook

## Dependencies

```json
{
  "dependencies": {
    "string-similarity": "^4.0.4"  // For semantic similarity
  },
  "devDependencies": {
    "jest": "^29.0.0"  // For testing
  }
}
```

## Configuration (plugin.json)

```json
{
  "configuration": {
    "similarityThreshold": 0.85,     // Merge patterns >= 85% similar
    "pruneThreshold": 0.3,           // Prune if < 30% confidence
    "minObservations": 10,           // Min observations before pruning
    "confidenceThreshold": 0.7,      // High-confidence cutoff
    "maxPatternsInPlaybook": 50,     // Max patterns to display
    "enableReflection": true,        // Use sequential-thinking MCP
    "logLevel": "info"               // Logging verbosity
  }
}
```

## Pattern Categories

### Python (8 patterns)
- py-001: Use TypedDict for configs ✅
- py-002: Validate API responses ✅
- py-003: Avoid bare except ❌
- py-004: Use context managers ✅
- py-005: Use asyncio.gather ✅
- py-006: Use dataclasses ✅
- py-007: Use f-strings ✅
- py-008: Avoid mutable defaults ❌

### JavaScript (8 patterns)
- js-001: Wrap fetch in try-catch ✅
- js-002: Use custom hooks ✅
- js-003: Avoid direct state mutation ❌
- js-004: Use const for immutables ✅
- js-005: Use async/await ✅
- js-006: Use optional chaining ✅
- js-007: Use nullish coalescing ✅
- js-008: Avoid var ❌

### TypeScript (4 patterns)
- ts-001: Use interface ✅
- ts-002: Use type guards ✅
- ts-003: Use generics ✅
- ts-004: Avoid any ❌

## Testing

**Test Suites**:
1. `patternDetector.test.js` - Pattern detection logic
2. `curator.test.js` - Curator algorithm (similarity, merging, pruning)

**Coverage**:
- Pattern detection for all languages
- Confidence calculation edge cases
- Similarity calculation accuracy
- Merge/create/prune decisions
- Deduplication logic

## Key Design Decisions

### Why Deterministic Curator?
- No LLM variance in curation
- Reproducible results
- Much lower latency (no LLM call)
- Research explicitly states: "non-LLM merges"

### Why 85% Similarity Threshold?
- From research paper
- Balances precision (avoid false merges) vs. recall (catch similar patterns)
- Tested on multiple benchmarks

### Why String Similarity vs. Embeddings?
- Faster (no model loading)
- Sufficient for pattern names + descriptions
- Research shows non-LLM methods work well

### Why Sequential-Thinking MCP for Reflection?
- Structured, step-by-step reasoning
- Better insight quality than simple prompts
- Aligns with research's "reflective" approach
