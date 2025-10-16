# Changelog

All notable changes to the ACE (Agentic Context Engineering) plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/ce-dot-net/ce-ai-ace/compare/v2.3.1...HEAD
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
