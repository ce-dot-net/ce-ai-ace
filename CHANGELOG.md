# Changelog

All notable changes to the ACE (Agentic Context Engineering) plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.0] - 2025-10-18

### 🚀 Major: TypeScript MCP Server Architecture

**BREAKING CHANGE**: Migrated from Python scripts + ChromaDB to native TypeScript MCP server.

### Added
- **TypeScript MCP Server** (`mcp-servers/ace-pattern-learning/`)
  - Native MCP protocol support with STDIO transport
  - Pure JavaScript embeddings using `@xenova/transformers` (no Python!)
  - SQLite storage with `better-sqlite3` (no ChromaDB server needed)
  - MCP Sampling for Claude invocation (uses Claude Code's Claude API)
  - 6 MCP Tools: `ace_reflect`, `ace_train_offline`, `ace_get_patterns`, `ace_get_playbook`, `ace_status`, `ace_clear`
  - Dynamic MCP Resources: `ace://patterns/all`, `ace://playbook`, `ace://stats`, etc.
- **LLM-Based Domain Discovery** - Domains discovered by Claude analyzing code, not hardcoded keywords
- **100% Research Paper Compliance** - All ACE paper requirements implemented (85%/70%/30% thresholds)

### Changed
- **Slash Commands** - All commands now use MCP tools instead of Python scripts
  - `/ace-status` → `mcp__ace-pattern-learning__ace_status`
  - `/ace-patterns` → `mcp__ace-pattern-learning__ace_get_patterns`
  - `/ace-train-offline` → `mcp__ace-pattern-learning__ace_train_offline`
  - `/ace-clear` → `mcp__ace-pattern-learning__ace_clear`
  - `/ace-force-reflect` → `mcp__ace-pattern-learning__ace_reflect`
- **Hooks** - Simplified to prompt-based reflection (removed Python script calls)
- **Plugin Description** - Updated to reflect TypeScript MCP architecture

### Removed
- ❌ **Deprecated Python Scripts** - All 22 Python scripts removed
  - `ace-cycle.py`, `offline-training.py`, `domain_discovery.py`, etc.
  - `requirements.txt` (no Python dependencies needed!)
  - `ace-clear.sh` (replaced by MCP tool)
- ❌ **ChromaDB Dependency** - No longer needed (pure JS embeddings)
- ❌ **Claude Agent SDK** - Not needed (MCP sampling handles it)
- ❌ **uvx Overhead** - No more complex script orchestration

### Performance
- ⚡ **Faster Startup** - Instant via STDIO (vs ~5 seconds for uvx + ChromaDB)
- 📦 **Smaller Footprint** - 4 npm packages vs 10+ Python packages
- 🔄 **Single Process** - MCP server only (vs Python + ChromaDB + uvx)

### Architecture Benefits
- ✅ Native Claude Code integration
- ✅ Zero configuration (auto-starts with plugin)
- ✅ No external dependencies or servers
- ✅ Type-safe TypeScript implementation
- ✅ Same embedding models as Python (all-MiniLM-L6-v2)
- ✅ TRUE ACE: LLM discovers patterns AND domains from raw code

### Migration Notes
- Old `.ace-memory/` data remains compatible (SQLite schema unchanged)
- MCP server registered in `plugin.json` mcpServers section
- No user action required - works automatically on plugin load

## [2.4.2] - 2025-10-18

### Added
- **Claude Agent SDK support** - Optional programmatic agent invocation for offline training
  - Installed `claude-agent-sdk==0.1.3` (latest stable release)
  - Enhanced `offline-training.py` with SDK integration
  - Graceful fallback to manual Task tool if SDK unavailable
  - Enables fully automated multi-epoch training without user interaction
- **Comprehensive requirements.txt** - Complete dependency documentation
  - All dependencies linked to ACE research paper sections
  - Clear separation: Required vs Optional vs Development dependencies
  - Installation instructions with pip and uvx
  - Standard library dependencies documented (no install needed)

### Fixed
- **SDK implementation** - Corrected agent invocation pattern in offline-training.py
  - Before: Incorrectly used `agents` parameter (for defining agents)
  - After: Properly uses Task tool for agent invocation via SDK
  - Added proper `cwd` configuration for SDK calls
  - Streaming mode (query function) as recommended by docs
- **SDK version** - Corrected to v0.1.3 (latest stable on PyPI)
  - Documentation showed v0.1.4 but not yet released
  - Updated requirements.txt to use available version

### Changed
- **Agent invocation architecture** - Validated dual-pattern approach
  - ace-cycle.py: Task tool via stderr (hooks + interactive)
  - domain_discovery.py: Task tool via stderr (hooks + interactive)
  - offline-training.py: SDK optional (automation + batch)
  - Both patterns validated against Claude Code documentation
  - Documented in Serena memory: `Agent_Invocation_Architecture`

### Documentation
- **Dependencies audit complete** - All dependencies audited and documented
  - ACE research paper compliance verified
  - Installation status tracked in Serena memory
  - Agent SDK integration patterns documented
  - Two invocation patterns explained with use cases

## [2.4.1] - 2025-10-18

### Fixed
- **PostToolUse hook concurrency control** - Eliminated API Error 400 from parallel Edit/Write operations
  - Root cause: When Claude executes multiple Edit/Write in parallel, both trigger PostToolUse hook simultaneously
  - Two `ace-cycle.py` processes run concurrently, both output `{'continue': True}` at slightly different times
  - Claude Code's message builder gets confused about which `tool_result` belongs to which `tool_use`
  - Result: API request sent to Anthropic missing `tool_result` blocks → 400 Bad Request
  - **Solution**: Added file-based mutual exclusion lock using `fcntl.flock()`
  - Lock file: `.ace-memory/.ace-cycle.lock` (non-blocking acquisition)
  - First parallel edit acquires lock and runs normally, second edit skips immediately with `{'continue': True}`
  - Prevents message corruption while maintaining both edits' success
  - Benefits: No 400 errors, no performance impact, graceful degradation, proper cleanup
  - Technical details in `docs/FIX_400_ERROR.md` and `docs/ACE_400_ERROR_ANALYSIS.md`

### Changed
- **Agent examples cleanup** - Removed obsolete Serena MCP references from domain-discoverer agent
  - Replaced Serena examples with ChromaDB and git integration examples
  - ChromaDB still used for vector storage (not removed!)
  - Examples now show actual current integrations (chromadb, git, plugins, hooks)

## [2.4.0] - 2025-10-18

### Added
- **Complete pytest testing framework** with 33 comprehensive tests
  - ACE research paper compliance tests (11 tests validating arXiv:2510.04618v1)
  - Hook execution tests (PostToolUse, AgentStart, SessionEnd)
  - Script execution tests (ace-cycle, generate-playbook, generate-speckit)
  - Playbook generation tests (CLAUDE.md, spec-kit structure)
  - Full integration tests (Edit → patterns → playbooks workflow)
- **ACETestHelper** class for Claude Code CLI simulation
  - Simulates Edit/Write tool triggers
  - Mocks agent responses (reflector, domain-discoverer)
  - Database validation utilities
  - Hook JSON stdin simulation
- **Research paper validation**
  - Generator → Reflector → Curator architecture tests
  - 85% similarity threshold validation
  - 30% prune threshold validation
  - Confidence formula verification (successes/observations)
  - Deterministic Curator validation (no LLM in curation)
  - Graceful degradation tests
  - Pattern merge behavior tests
- **Test fixtures and helpers**
  - `conftest.py` with reusable fixtures
  - `ace_test_helper.py` for CLI simulation
  - Sample code fixtures for pattern discovery
  - Mock agent response fixtures
  - Temporary project and database fixtures

### Changed
- Testing approach: pytest-based instead of manual shell execution
- All tests run in isolated temporary environments
- Fast unit tests with mocked dependencies
- Slower integration tests with real components

### Fixed
- Test coverage now validates theory → implementation gap
- Tests ensure no deviation from ACE research paper architecture

## [2.3.28] - 2025-10-17

### Fixed
- **Deterministic pattern ID generation in offline training** - Fixed UNIQUE constraint violation
  - Changed from loop index to content-hash-based ID generation
  - Pattern IDs now deterministic: `hashlib.md5(f"{domain_id}:{pattern_name}")[:5]`
  - Prevents duplicate bullet_ids when same pattern discovered across epochs
  - Bug caused `sqlite3.IntegrityError: UNIQUE constraint failed: patterns.bullet_id`
  - Issue occurred during multi-epoch training when patterns re-discovered
  - Fix allows successful completion of 5-epoch training (223 patterns, 2450 observations)

### Added
- **ACE Research Paper Verification Report** - Comprehensive verification against TRUE ACE architecture
  - Created `docs/ACE_Research_Paper_Verification.md` (10-section analysis)
  - Verified all 10 critical ACE components match research paper specifications
  - Confirmed: Generator → Reflector → Curator architecture (TRUE ACE)
  - Confirmed: Agent-based pattern discovery (no hardcoded patterns)
  - Confirmed: Multi-epoch training (5 epochs per Section 4.1)
  - Confirmed: Confidence formulas, curation thresholds (85% merge, 30% prune)
  - Confirmed: Semantic similarity engine with sentence-transformers
  - Confirmed: Incremental delta updates (Section 3.1)
  - Confirmed: Iterative refinement (up to 5 rounds, Section 3.2)
  - Evidence includes code references, formula verification, testing results
  - **Status: ✅ FULLY COMPLIANT WITH ACE RESEARCH PAPER**

## [2.3.27] - 2025-10-17

### Fixed
- **ACE clear script now removes auto-generated spec-kit playbooks**
  - Fixed issue where old training artifacts from `specs/playbooks/` influenced new offline training runs
  - `ace-clear.sh` now removes auto-generated playbooks (directories numbered ≥005)
  - Preserves manually created playbooks (001-temp, 003-avoid-bare-except, etc.)
  - Ensures clean slate for fresh pattern discovery without contamination from previous runs
  - Uses `find` to identify and remove only auto-generated directories: `[005-999]-*`
  - Issue affected users who ran multiple training sessions - old patterns would reappear

### Documentation
- **Clarified Write permission behavior for domain-discoverer agent**
  - Agent requires Write tool to save JSON responses to `.ace-memory/discovery-queue/`
  - Permission prompts are expected Claude Code security behavior (no auto-approve API)
  - Users can click "Allow automatically" when first prompted
  - Subsequent writes to same directory pattern are auto-approved by Claude Code
  - This is by design for security - prevents malicious plugins from arbitrary file writes

## [2.3.26] - 2025-10-17

### Fixed
- **Offline training agent response parsing** - Fixed domain-discoverer agent response format parsing
  - Agent returns `{concrete, abstract, principles}` structure from domain taxonomy discovery
  - Script was looking for non-existent `patterns` key in response JSON
  - Added conversion logic to transform agent's domain taxonomy into pattern list format
  - Converts concrete domain patterns, abstract patterns, and principles into unified pattern objects
  - Each pattern gets unique ID (domain-NNNNN format), name, description, confidence
  - Issue affected all offline training runs - patterns were discovered but not stored in database
  - Now successfully processes 164 unique patterns from 9 files (351 pattern observations per epoch)
  - Tests confirm: 5 epochs completed, 3260 total observations, no UNIQUE constraint violations
  - Validates that v2.3.24 bullet_id fix still works correctly with actual multi-pattern files

## [2.3.25] - 2025-10-17

### Changed
- **Cleanup and spec-kit updates** - Removed old backups and updated spec-kit playbooks
  - Removed obsolete .ace-memory backups from testing sessions
  - Removed old CHANGELOG version files (v2.3.9, v2.3.15)
  - Updated spec-kit playbooks with patterns from successful offline training test
  - Replaced placeholder test patterns with actual discovered patterns
  - 16 new spec-kit playbooks generated from domain-discoverer agent analysis

## [2.3.24] - 2025-10-17

### Fixed
- **Bullet ID generation deterministic hashing** - Fixes UNIQUE constraint violation in offline training
  - Changed from database count-based to pattern_id hash-based generation
  - Prevents collisions when storing multiple patterns from same domain in one run
  - Aligns with ACE paper "batch size of 1" guidance (each pattern gets unique ID)
  - Issue occurred when domain-discoverer agent found 20+ patterns in single file
  - Now uses MD5 hash of pattern_id for deterministic 5-digit number (00000-99998)
  - Fixes bug that affected anyone running offline training with multi-pattern files
  - Bug was: `sqlite3.IntegrityError: UNIQUE constraint failed: patterns.bullet_id`

## [2.3.23] - 2025-10-17

### Fixed
- **Reflector agent invocation caching** - Implements response caching for PostToolUse hook pattern discovery
  - Both `invoke_reflector_agent()` and `invoke_reflector_agent_with_feedback()` now check for cached responses
  - Responses cached in `.ace-memory/reflections/` directory (per-file and per-refinement-round)
  - Same two-phase workflow as domain-discoverer: (1) Generate request → (2) Claude processes → (3) Re-run uses cache
  - Aligns with ACE paper's max 5 refinement rounds (Section 4: "maximum number of Reflector refinement rounds...to 5")
  - Added Write tool to both reflector agents (reflector.md and reflector-prompt.md) so they can save responses
  - Verified against research paper using pdfgrep - confirms iterative refinement architecture
  - All three agents now properly implement Claude Code agent coordination pattern

## [2.3.22] - 2025-10-17

### Fixed
- **Offline training Claude Code agent coordination** - Properly implements Claude Code agent architecture
  - Agents are `.md` files invoked via Claude's Task tool (not Python subprocess)
  - Script outputs discovery requests to stderr for Claude to process
  - Claude invokes domain-discoverer agent and saves responses to queue
  - Subsequent training runs use cached agent responses for multi-epoch learning
  - Two-phase workflow: (1) First run generates requests → (2) Claude processes → (3) Re-run uses cached data
  - Aligns with Claude Code best practices for agent orchestration
  - Research-backed: follows ACE paper's Generator-Reflector-Curator architecture

## [2.3.21] - 2025-10-17

### Fixed
- **Offline training autonomous agent invocation** - Training now runs fully automatically
  - Removed interactive pause/queue workflow
  - `batch_reflect_via_agent()` now directly invokes domain-discoverer agent via subprocess
  - Agents run autonomously during training epochs (no manual intervention needed)
  - Responses cached in discovery queue for multi-epoch reuse
  - Implements TRUE ACE research paper offline training (autonomous, not interactive)
  - Aligns with paper Section 4.1: offline optimization should be automated
  - **NOTE**: v2.3.21 approach was incorrect - agents can't be invoked via subprocess in Claude Code. See v2.3.22 for proper fix.

## [2.3.20] - 2025-10-17

### Fixed
- **Offline training queue** - Fixed non-deterministic request IDs
  - Use hashlib.md5 instead of Python's hash() for deterministic IDs
  - Check for existing responses BEFORE writing new requests
  - Prevents duplicate requests for same file across runs
  - Queue system now works correctly for multi-epoch training

## [2.3.19] - 2025-10-17

### Fixed
- **domain-discoverer agent** - Added Write tool access
  - Agent can now save discovered patterns to response files
  - Required for queue-based offline training workflow
  - Agent reads code, discovers patterns, writes JSON response

## [2.3.18] - 2025-10-17

### Fixed
- **Offline Training Queue System** - Implemented proper queue-based agent invocation
  - Removed hardcoded `time.sleep(1)` timer (was a temporary hack)
  - Offline training now writes discovery requests to `.ace-memory/discovery-queue/`
  - Agents process requests and write responses as `*.response.json` files
  - Training pauses and prompts user to process pending requests
  - Re-running `/ace-train-offline` resumes with discovered patterns
  - No more relying on arbitrary sleep timers - proper file-based coordination
  - Follows queue-driven workflow pattern from Claude Code best practices

### Changed
- **ace-clear behavior** - Clarified that `specs/` directory is preserved
  - `specs/` contains example playbooks (part of codebase, not generated data)
  - Only `.ace-memory/` and `CLAUDE.md` are removed during clear
  - This is correct behavior - specs are reference examples, not learned patterns

## [2.3.14] - 2025-10-17

### Changed
- **Simplified All Commands** - Updated all command patterns to use simple instructions
  - Removed `!` auto-exec prefix from all remaining commands
  - Removed complex CLAUDE_PLUGIN_ROOT finding logic
  - Commands now use simple relative paths: `plugins/ace-orchestration/scripts/...`
  - ace-train-offline.md, ace-export-patterns.md, ace-import-patterns.md all simplified
  - Consistent pattern across all 8 slash commands



## [2.3.13] - 2025-10-17

### Changed
- **Simplified Command Pattern** - Verified against official Claude Code documentation
  - Removed complex bash conditionals from ace-clear.md
  - Commands now use simple natural language instructions
  - `$ARGUMENTS` is a markdown placeholder (substituted before Claude sees it)
  - Claude executes scripts via Bash tool based on clear instructions
  - Pattern verified against official docs: slash commands are instructions, not scripts



## [2.3.12] - 2025-10-17

### Fixed
- **Slash Command Pattern** - Fixed slash commands to work as instructions, not auto-executing scripts
  - Removed `!` prefix from bash blocks - commands are instructions to Claude, not auto-exec
  - Created `scripts/ace-clear.sh` helper script
  - Updated ace-clear.md to use instruction pattern with `$ARGUMENTS` placeholder
  - `$ARGUMENTS` is substituted in markdown, Claude executes the command with Bash tool
  - This is the correct Claude Code slash command pattern per official documentation



## [2.3.11] - 2025-10-17

### Fixed
- **Command Arguments Bug** - Fixed slash commands not receiving arguments properly
  - Changed `$1` to `$ARGUMENTS` in all command bash blocks
  - Fixed ace-clear.md - `--confirm` argument now works
  - Fixed ace-export-speckit.md - playbook selection now works
  - Fixed ace-force-reflect.md - file path argument now works
  - Fixed ace-patterns.md - domain/confidence filters now work
  - Commands now properly receive and process user arguments


## [2.3.10] - 2025-10-17

### Fixed
- **Marketplace Version Sync** - Updated marketplace.json to v2.3.10
  - Previous release v2.3.9 didn't update marketplace.json (still showed 2.3.8)
  - Marketplace description updated to emphasize TRUE ACE architecture
  - All version references now synchronized across all files
  - README.md badge updated to 2.3.10
  - plugin.json version updated to 2.3.10

### Note
This is a version bump release to properly sync marketplace distribution. All TRUE ACE architecture features from v2.3.9 are included:
- Agent-based pattern discovery (no hardcoded keywords)
- Generator feedback loop for pattern self-improvement
- Confidence calculation with usage feedback
- Complete documentation (ACE_TRUE_ARCHITECTURE.md, ACE_TESTING_GUIDE.md, CHANGELOG_v2.3.9.md)

## [2.3.9] - 2025-10-17

### Added
- **TRUE ACE Architecture Implementation** - Complete research paper alignment
  - Agent-based pattern discovery (Reflector analyzes raw code)
  - Generator feedback loop for pattern self-improvement
  - PostTaskCompletion hook collects helpful/harmful bullet tagging
  - Confidence calculation incorporates usage feedback
  - New formula: (successes + helpful) / (observations + helpful + harmful)

### Changed
- **Pattern Discovery** - Removed hardcoded detection, implemented agent-based discovery
  - Removed detect_patterns() function entirely
  - Updated reflect() to pass raw code directly to Reflector
  - Reflector discovers patterns from imports, APIs, architectural choices
  - Patterns learned from YOUR codebase, not predefined keywords

### Added Documentation
- docs/ACE_TRUE_ARCHITECTURE.md (296 lines) - Complete architecture guide
- docs/ACE_TESTING_GUIDE.md (351 lines) - 10 comprehensive test scenarios
- CHANGELOG_v2.3.9.md (339 lines) - Detailed release notes
- hooks/PostTaskCompletion.sh - NEW feedback hook
- scripts/collect-pattern-feedback.py - NEW feedback collector

### Removed
- **Deprecated Files** - Removed hardcoded pattern detection
  - plugins/ace-orchestration/scripts/semantic_pattern_extractor.py

### Breaking Changes
**Users should run `/ace-orchestration:ace-clear --confirm`** to reset patterns. Old patterns used hardcoded detection and won't self-improve. Let ACE rediscover patterns from your actual codebase!

## [2.3.8] - 2025-10-17

### Fixed
- **Slash Command Auto-Execution** - Fixed all slash commands to auto-execute bash blocks
  - Added `!` prefix to all bash code blocks for automatic execution
  - Commands now execute automatically instead of showing instructions
  - Fixed all 8 commands: ace-clear, ace-train-offline, ace-status, ace-patterns, ace-force-reflect, ace-export-patterns, ace-import-patterns, ace-export-speckit
  - Properly structured command markdown files per Claude Code documentation
  - Removed manual execution requirement - commands work as expected

## [2.3.7] - 2025-10-17

### Changed
- **Agent Architecture Clarification** - Enhanced documentation for Generator-Reflector-Curator roles
  - Added explicit `agents` field to plugin.json for better discoverability
  - Updated README.md Three Roles section with agent details and design decisions
  - Clarified single Reflector with iterative refinement (not two separate agents)
  - Documented no fallback heuristics (research paper Appendix B compliance)
  - Added Curator semantic embeddings note (ChromaDB usage)

### Fixed
- **Agent YAML Frontmatter** - Fixed missing YAML frontmatter in reflector-prompt.md
  - Agent was not properly registered due to missing metadata
  - Added complete YAML frontmatter: name, description, tools, model
  - All 3 agents now have proper frontmatter for auto-discovery

### Added
- **Comprehensive Agent Documentation** - Created agents/README.md
  - Complete agent architecture explanation (Generator/Reflector/Curator)
  - Agent definition format with YAML frontmatter requirements
  - Agent registration and auto-discovery details
  - Agent invocation patterns (Task tool via stderr)
  - Design decisions including why NO fallback heuristics
  - Research paper alignment verification

### Removed
- **Fallback Heuristics** - Removed all hardcoded fallback logic (94 lines)
  - Removed `fallback_reflection()` function (24 lines) from ace-cycle.py
  - Removed `fallback_refinement()` function (39 lines) from ace-cycle.py
  - Replaced with simple returns acknowledging limitation
  - Aligns with research paper Appendix B: fallbacks are "acknowledged limitation"
  - When Reflector cannot analyze, return empty result instead of hardcoded heuristics

## [2.3.6] - 2025-10-17

### Fixed
- **Database Initialization** - Fixed pattern database initialization in offline training
  - Ensured all required tables are created before use
  - Fixed schema consistency across training modes

## [2.3.5] - 2025-10-16

### Fixed
- **Database Table Initialization** - Fixed offline training to initialize all database tables before use
  - Error: `sqlite3.OperationalError: no such table: patterns` when running `/ace-train-offline`
  - Root cause: `offline-training.py` created epochs tables via `epoch-manager.py` but didn't initialize main `patterns` table
  - Solution: Call `init_database()` from `ace-cycle.py` at start of offline training to create all required tables
  - Offline training now properly initializes complete database schema (patterns, insights, observations, epochs)

## [2.3.4] - 2025-10-16

### Fixed
- **Database Directory Creation** - Fixed offline training to create `.ace-memory/` directory before database initialization
  - Error: `sqlite3.OperationalError: unable to open database file` when running `/ace-train-offline` on fresh projects
  - Root cause: `epoch-manager.py` tried to create database without ensuring parent directory exists
  - Solution: Added `DB_PATH.parent.mkdir(parents=True, exist_ok=True)` in `init_epochs_table()`
  - Offline training now works correctly on projects without existing `.ace-memory/` directory

## [2.3.3] - 2025-10-16

### Fixed
- **Command Bash Execution** - Consolidated multi-block bash scripts into single blocks
  - Fixed ace-train-offline.md: Combined plugin path detection and script execution into one bash block
  - Fixed ace-force-reflect.md: Combined file detection, validation, and ACE cycle trigger into one bash block
  - Root cause: Claude Code executes each markdown bash block independently; variables don't persist across blocks
  - Commands now execute properly with persistent variable scope throughout the entire script

### Technical Details
- Issue: Separate bash code blocks in command markdown files don't share variable scope
- Variables like `$PLUGIN_PATH` defined in one block weren't available in subsequent blocks
- Error: "parse error near `fi'" when trying to reference undefined variables
- Solution: Consolidate all bash logic into single code blocks per command

## [2.3.2] - 2025-10-16

### Fixed
- **Command Registration** - Added missing `"commands": "./commands"` field to plugin.json
  - All 8 slash commands now properly registered and discoverable in Claude Code CLI
  - Commands: /ace-status, /ace-patterns, /ace-force-reflect, /ace-clear, /ace-train-offline, /ace-export-patterns, /ace-import-patterns, /ace-export-speckit
- **Script Path Resolution** - Fixed all command files to use robust path detection
  - Prefer `$CLAUDE_PLUGIN_ROOT` environment variable when available (hooks context)
  - Fallback to dynamic `find` command for marketplace installations (slash command context)
  - Updated: ace-train-offline.md, ace-force-reflect.md, ace-export-patterns.md, ace-import-patterns.md
- **Script Naming** - Corrected ace-train-offline.md to reference correct script name (offline-training.py)
- **File Permissions** - Made missing scripts executable: offline-training.py, pattern-portability.py, convergence-checker.py
- **Command Metadata** - Added `allowed-tools: Bash` frontmatter to command files for proper tool access

### Changed
- All command files now use defensive dual-mode path resolution for marketplace compatibility
- Improved error messages when ACE plugin installation cannot be located

## [2.3.1] - 2025-10-16

### Changed
- **Documentation Accuracy** - Aligned all docs with ACE research paper (arxiv:2510.04618)
  - Fixed `generate-playbook.py` docstring to reflect actual ACE paper sections
  - Removed incorrect section references (APIS/VERIFICATION) that were not in paper
  - Added accurate section descriptions matching paper Figure 3
  - Created comprehensive verification document (docs/ACE_PAPER_VERIFICATION.md)
- **ACE Paper Compliance**
  - Verified 100% implementation of all paper components
  - Documented all core features: Generator/Reflector/Curator, bulletized structure, delta updates
  - Confirmed domain taxonomy, grow-and-refine, and multi-epoch training alignment
  - Clarified implementation extensions beyond paper (confidence-based organization)

### Documentation
- Added **docs/ACE_PAPER_VERIFICATION.md** - Complete verification checklist against research paper
  - All 10 core ACE components verified as implemented
  - Detailed evidence and code references
  - Summary of smart extensions beyond paper spec

## [2.3.0] - 2025-10-16

### Added
- **Smart Serena MCP Detection** - Intelligent handling of global vs plugin-bundled Serena
  - Auto-detects if global `serena` MCP is installed
  - Prefers global Serena if available (no duplicate conflicts)
  - Falls back to bundled `serena-ace` if no global installation
  - Creates `.ace-config` to signal which Serena to use
  - Eliminates API Error 400 (tool use concurrency issues)
  - Zero manual configuration required for users

### Changed
- **check-mcp-conflicts.py** renamed to smart Serena manager
  - Now manages Serena strategy selection automatically
  - Outputs clear messages about which Serena is being used
  - Supports both use cases: global Serena users and fresh installs
- **SessionStart hook** now handles Serena detection and configuration

### Fixed
- **MCP concurrency conflicts** - Eliminated 400 errors when both Serena instances exist
- **Tool use conflicts** - No more duplicate tool registration from multiple Serena servers

## [2.2.3] - 2025-10-15

### Changed
- **Documentation updates** - Synchronized all documentation with marketplace structure
  - Fixed CHANGELOG.md path references (`.claude-plugin/commands/` → `plugins/ace-orchestration/commands/`)
  - Updated MCP_INTEGRATION.md plugin location paths
  - Updated ACE_IMPLEMENTATION_GUIDE.md plugin.json path references
  - Updated EMBEDDINGS_ARCHITECTURE.md plugin configuration section
  - Fixed README.md project structure diagram (removed duplicate root-level directories)
  - Updated README.md troubleshooting section with correct plugin installation path

## [2.2.2] - 2025-10-15

### Fixed
- **Slash command paths** - Fixed paths for marketplace installation structure
  - `/ace-train-offline` now uses `$PLUGIN_PATH/plugins/ace-orchestration/scripts/`
  - `/ace-export-patterns` now uses correct plugin structure path
  - `/ace-import-patterns` now uses correct plugin structure path
  - All commands work correctly when installed via marketplace

### Changed
- **README.md** - Updated to reflect v2.2.2 and new marketplace structure

## [2.2.1] - 2025-10-15

### Changed
- **Completed marketplace restructure** - All plugin files now in proper location
  - Scripts, specs, tests moved to plugins/ace-orchestration/
  - Clean separation between marketplace and plugin
  - Ready for multi-plugin expansion

## [2.2.0] - 2025-10-15

### Changed
- **[BREAKING] Restructured repository as proper multi-plugin marketplace**
  - Plugin files moved from root to `plugins/ace-orchestration/` directory
  - Marketplace now supports multiple plugins (scalable architecture)
  - Follows community best practices (Anthropic, wshobson, AgiFlow patterns)
  - Eliminates version confusion between marketplace and plugin
  - **Users must uninstall old version and reinstall**: `/plugin uninstall ace-orchestration` then `/plugin install` or `/plugin marketplace update ace-plugin-marketplace`
- Updated marketplace.json source path from `"./"` to `"./plugins/ace-orchestration"`
- Repository structure now clearly separates marketplace from plugin implementation

### Migration Guide
For existing users:
1. Uninstall current version: `/plugin uninstall ace-orchestration`
2. Update marketplace: `/plugin marketplace update ace-plugin-marketplace`
3. Reinstall plugin: Enable it from plugin list
4. All patterns and settings preserved in `.ace-memory/`

## [2.1.3] - 2025-10-15

### Fixed
- **marketplace.json version sync** - Updated marketplace.json to reflect correct plugin version
  - marketplace.json was not updated in v2.1.2 release, causing version mismatch
  - Plugin now correctly reports v2.1.3 across all distribution channels

## [2.1.2] - 2025-10-15

### Fixed
- **Slash command path resolution bug** - Commands now work when installed via marketplace
  - Fixed `/ace-train-offline`, `/ace-export-patterns`, and `/ace-import-patterns` commands
  - Root cause: `${CLAUDE_PLUGIN_ROOT}` environment variable not set in slash command contexts
  - Solution: Commands now dynamically find plugin installation path at `~/.claude/plugins/marketplaces/ace-plugin-marketplace/`
  - All commands show helpful error if plugin not installed
  - Ensures commands work for all users, not just in development repo

## [2.1.1] - 2025-10-15

### Added
- **Slash commands directory** (`plugins/ace-orchestration/commands/`)
  - All 8 ACE commands now properly registered in plugin
  - `/ace-orchestration:ace-train-offline` command now available
  - Updated offline training command to use uvx dependencies

### Changed
- **ace-train-offline.md** updated with uvx dependency sharing commands
  - Ensures offline training has access to chromadb and embeddings
  - Consistent with all other hooks using uvx

## [2.1.0] - 2025-10-15

### Added
- **Zero-Setup Dependency Management** with uvx
  - All Python dependencies (chromadb, sentence-transformers, scikit-learn) auto-managed by uvx
  - Scripts run via uvx with dependency sharing: `uvx --from chroma-mcp --with chromadb --with sentence-transformers`
  - First run downloads ~400MB (one-time), subsequent runs use cache (instant)
- **Comprehensive Dependency Documentation** (docs/DEPENDENCIES.md)
  - Complete explanation of uvx dependency sharing approach
  - Performance characteristics and troubleshooting guide
  - How we discovered the solution (breakthrough moment story)
- **Enhanced Embeddings Documentation**
  - docs/EMBEDDINGS_ARCHITECTURE.md - Technical architecture with ChromaDB caching
  - docs/EMBEDDINGS_REVIEW.md - Research paper compliance analysis
  - docs/DOMAIN_DISCOVERY_REVIEW.md - Bottom-up domain taxonomy vs paper

### Changed
- **All hooks updated** to use uvx dependency sharing for chromadb/embeddings access
  - AgentStart: `uvx --from chroma-mcp --with chromadb python3 script.py`
  - PostToolUse/AgentEnd: Full stack with sentence-transformers and scikit-learn
- **README.md Prerequisites** section added with uvx installation instructions
- **Embeddings cache checking** improved to avoid numpy array truth value warnings
- **Plugin.json MCP configuration** fixed to use correct `chroma-mcp` package name

### Removed
- **install.sh** - Deprecated development script (no longer needed, scripts auto-create directories)

### Fixed
- **Critical dependency accessibility bug**: chromadb wasn't accessible to plugin scripts
  - Root cause: uvx installs MCPs in isolated environment, scripts ran in system Python
  - Solution: Run all scripts via uvx with same dependency environment
- **Embeddings cache lookup bug**: Fixed numpy array truth value error in cache checking
- **Plugin marketplace compatibility**: Plugin now works when installed via marketplace (zero manual setup!)

## [2.0.0] - 2025-10-15

### Added
- **Complete Usage Guide** with before/after examples showing automatic pattern following
- Three initialization strategies: offline training, online learning, pattern import
- Real-world examples demonstrating ACE benefits (f-strings, custom hooks, TypeScript interfaces)
- Comprehensive guidance on when to use ACE (existing vs new projects)
- Research-backed performance expectations and timelines
- Prominent usage guide link in README Quick Start section

### Changed
- Enhanced README.md with clear setup paths (Existing/New/Team workflows)
- Improved Quick Start section with actionable commands

## [2.0.0-rc.1] - 2025-10-14

### Added
- **Full Serena MCP Integration** with intelligent fallback to regex detection
- 3-tier detection system: config → filesystem → tools
- Hybrid pattern detection (Serena MCP → regex fallback)
- Complete MCP JSON-RPC client implementation (237 lines)
- Auto-detection script for Serena availability (266 lines)
- MCP bridge for universal MCP server communication
- Comprehensive MCP integration documentation

### Changed
- Pattern detector now tries Serena MCP first, falls back gracefully
- All implementations are production-ready (no TODOs or placeholders)

### Fixed
- Module import issues for hyphenated script filenames using `importlib.util`

## [2.0.0-beta.3] - 2025-10-14

### Added
- **Complete ACE Iterative Refinement** (100% research paper coverage)
- Full iterative refinement with up to 5 rounds and convergence detection
- Progressive confidence increases (0.80 → 0.95 over rounds)
- Evidence-based insights with specific recommendations
- **spec-kit Integration** for human-readable, version-controlled playbooks
- `specs/` directory structure committed to git for team collaboration
- `specs/memory/constitution.md` for high-confidence principles (≥70%)
- `specs/playbooks/NNN-domain/` for individual pattern tracking
- Dual storage: SQLite for learning + spec-kit for human readability

### Changed
- Reflector agent now performs multi-round analysis until convergence
- Playbooks generated in both spec-kit format (`specs/`) and Claude Code CLI format (`CLAUDE.md`)
- Enhanced pattern export/import with full spec-kit support

## [2.0.0-beta.2] - 2025-10-14

### Added
- **Phase 3: Delta Updates & Semantic Embeddings**
  - Incremental CLAUDE.md updates (surgical changes, no full rewrites)
  - Multi-backend semantic embeddings (OpenAI API, sentence-transformers, enhanced fallback)
  - Embeddings cache for fast lookups (`.ace-memory/embeddings-cache.json`)
  - Research-compliant 85% cosine similarity threshold
- **Phase 4: Multi-Epoch Training**
  - Offline training mode with up to 5 epochs
  - `/ace-train-offline` slash command for instant pattern learning
  - Epoch management utilities
  - Training cache for offline learning
  - Pattern evolution tracking
- **Phase 5: Serena Integration (Initial)**
  - Hybrid pattern detection (AST-aware + regex fallback)
  - Symbol-level analysis using `find_symbol`
  - Reference tracking with `find_referencing_symbols`
  - Serena memories for searchable insights
- **New Slash Commands**
  - `/ace-train-offline` - Run multi-epoch training on entire codebase
  - `/ace-export-patterns` - Export patterns to JSON for sharing
  - `/ace-import-patterns` - Import patterns from other projects
  - `/ace-export-speckit` - Export spec-kit playbooks
- **Complete Hook Lifecycle**
  - AgentStart: Inject CLAUDE.md into agent contexts
  - PreToolUse: Validate patterns before code is written
  - PostToolUse: Run ACE cycle after Edit/Write operations
  - AgentEnd: Analyze agent output for meta-learning
  - SessionEnd: Cleanup and final playbook generation
- **Advanced Features**
  - Dynamic pattern retrieval (context-aware, file-type filtering)
  - Convergence detection (σ < 0.05 variance threshold)
  - Pattern portability (export/import with smart merging)
  - Lazy pruning for context management

### Changed
- CLAUDE.md now uses incremental delta updates (append/update/prune)
- Pattern merging uses semantic embeddings instead of string matching
- Playbook structure optimized for Claude Code context injection

### Fixed
- Prevented context collapse through incremental updates
- Improved pattern similarity detection accuracy

## [2.0.0-beta.1] - 2025-10-14

### Added
- **Phase 1 & 2: ACE Framework Foundations**
  - Three-role architecture: Generator, Reflector, Curator
  - Bulletized structure with pattern IDs: `[domain-NNNNN]`
  - ACE sections: STRATEGIES, CODE SNIPPETS, CONTEXT, etc.
  - Deterministic curation with 85% similarity threshold
  - Incremental delta updates (grow-and-refine)
  - Helpful/harmful pattern tracking
- **Pattern Detection System**
  - 20+ predefined patterns for Python, JavaScript, TypeScript
  - Automatic pattern detection on Edit/Write operations
  - Test result correlation for effectiveness analysis
- **Reflector Agent**
  - LLM-based pattern analysis for effectiveness
  - Structured JSON input/output
  - Evidence-based insights extraction
- **SQLite Database**
  - Pattern observations and confidence scores
  - Insights from Reflector agent
  - Test results and execution feedback
  - Semantic embeddings cache
- **Documentation**
  - ACE Research Summary (docs/ACE_RESEARCH.md)
  - Implementation Guide (docs/ACE_IMPLEMENTATION_GUIDE.md)
  - Gap Analysis (docs/GAP_ANALYSIS.md)
  - Installation Guide (docs/INSTALL.md)
  - Quick Start Guide (docs/QUICKSTART.md)

### Changed
- Migrated from Claude Code 1.x to 2.0 declarative plugin system
- Converted to pure markdown + JSON + Python scripts (no index.js)
- Updated hooks to shell script execution model

### Fixed
- Dynamic path resolution for CLAUDE_PLUGIN_ROOT
- Marketplace source path for proper plugin discovery
- Slash command execution without environment variables

## [1.0.0] - 2025-10-14

### Added
- **Initial ACE Plugin Implementation**
  - Basic pattern detection framework
  - Simple playbook generation
  - Claude Code CLI integration
  - Plugin structure for Claude Code 2.0
  - Research papers included for reference (arXiv:2510.04618v1)
- **Core Commands**
  - `/ace-status` - View learning statistics
  - `/ace-patterns` - List learned patterns with filtering
  - `/ace-clear` - Reset pattern database
  - `/ace-force-reflect` - Manually trigger reflection
- **Basic Hooks**
  - PostToolUse: Trigger ACE cycle on code changes
- **Documentation**
  - Initial README with project overview
  - Basic installation instructions
  - Research background section

### Known Limitations
- No incremental updates (full CLAUDE.md rewrites)
- No semantic embeddings (string-based similarity)
- No multi-epoch training
- No pattern export/import
- Basic pattern detection (regex-only)

---

## Version History Summary

- **v2.3.8** (2025-10-17): Slash command auto-execution fixes - All commands now execute automatically
- **v2.3.7** (2025-10-17): Agent architecture clarification - Complete documentation and fallback removal
- **v2.3.6** (2025-10-17): Database initialization fixes
- **v2.3.5** (2025-10-16): Database table initialization fixes
- **v2.3.4** (2025-10-16): Database directory creation fixes
- **v2.3.3** (2025-10-16): Command bash block execution fixes
- **v2.3.2** (2025-10-16): Command registration and path resolution fixes
- **v2.3.1** (2025-10-16): Documentation accuracy - 100% ACE paper alignment verification
- **v2.3.0** (2025-10-16): Smart Serena MCP detection - Eliminates concurrency conflicts
- **v2.2.3** (2025-10-15): Documentation updates for marketplace structure
- **v2.2.2** (2025-10-15): Fixed slash command paths for marketplace installation
- **v2.2.1** (2025-10-15): Completed marketplace restructure with all files moved
- **v2.2.0** (2025-10-15): Restructured as multi-plugin marketplace (BREAKING: requires reinstall)
- **v2.1.3** (2025-10-15): Fixed marketplace.json version sync
- **v2.1.2** (2025-10-15): Fixed slash command path resolution for marketplace installations
- **v2.1.1** (2025-10-15): Added slash commands directory and offline training command
- **v2.1.0** (2025-10-15): Zero-setup dependency management with uvx + critical bug fixes
- **v2.0.0** (2025-10-15): Complete research implementation + comprehensive usage guide
- **v2.0.0-rc.1** (2025-10-14): Serena MCP integration with intelligent fallback
- **v2.0.0-beta.3** (2025-10-14): Iterative refinement + spec-kit integration
- **v2.0.0-beta.2** (2025-10-14): Phase 3-5 complete (delta updates, embeddings, multi-epoch, Serena)
- **v2.0.0-beta.1** (2025-10-14): Phase 1-2 foundations (ACE framework, bulletized structure)
- **v1.0.0** (2025-10-14): Initial ACE plugin release

---

## Research Background

This plugin implements the ACE (Agentic Context Engineering) framework from:

**"Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models"**

*Qizheng Zhang¹, Changran Hu², Shubhangi Upasani², et al.*

¹Stanford University, ²SambaNova Systems, ³UC Berkeley

[Research Paper](https://arxiv.org/abs/2510.04618)

### Research Results
- **+17.1%** improvement on AppWorld benchmark (42.4% → 59.4%)
- **+8.6%** improvement on domain-specific tasks (Finance)
- **86.9%** lower adaptation latency vs. existing methods
- **83.6%** token cost reduction ($17.7 → $2.9)

---

## Contributing

When adding entries to this changelog:

1. **Categories**: Added, Changed, Deprecated, Removed, Fixed, Security
2. **Audience**: Write for plugin users, not developers
3. **Links**: Reference commits, PRs, or issues where relevant
4. **Breaking Changes**: Clearly mark with **[BREAKING]** prefix
5. **Semantic Versioning**:
   - **Major** (X.0.0): Breaking changes
   - **Minor** (0.X.0): New features (backward compatible)
   - **Patch** (0.0.X): Bug fixes

---

[Unreleased]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.4.1...HEAD
[2.4.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.10...v2.4.0
[2.3.10]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.9...v2.3.10
[2.3.9]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.8...v2.3.9
[2.3.8]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.7...v2.3.8
[2.3.7]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.6...v2.3.7
[2.3.6]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.5...v2.3.6
[2.3.5]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.4...v2.3.5
[2.3.4]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.3...v2.3.4
[2.3.3]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.2...v2.3.3
[2.3.2]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.2.3...v2.3.0
[2.2.3]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.2.2...v2.2.3
[2.2.2]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.1.3...v2.2.0
[2.1.3]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.0.0-rc.1...v2.0.0
[2.0.0-rc.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.0.0-beta.3...v2.0.0-rc.1
[2.0.0-beta.3]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.0.0-beta.2...v2.0.0-beta.3
[2.0.0-beta.2]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.0.0-beta.1...v2.0.0-beta.2
[2.0.0-beta.1]: https://github.com/ce-dot-net/ce-ai-ace/compare/v1.0.0...v2.0.0-beta.1
[1.0.0]: https://github.com/ce-dot-net/ce-ai-ace/releases/tag/v1.0.0
