# Obsolete Files Cleanup Plan

**Context**: MCPs are now auto-installed via `plugin.json`. The old manual installation scripts are obsolete.

## 🗑️ Files to DELETE (No Longer Needed)

### Scripts (7 files)
1. **`scripts/generate-mcp-config.py`** - OBSOLETE
   - Purpose: Generated dynamic MCP config for manual installation
   - Why obsolete: MCPs now in `plugin.json`, auto-installed by Claude Code CLI
   - Used by: `install.sh` (deprecated)

2. **`scripts/mcp-conflict-detector.py`** - OBSOLETE
   - Purpose: Detected conflicts with existing MCPs (especially Serena)
   - Why obsolete: We namespace MCPs as `chromadb-ace` and `serena-ace` - no conflicts!
   - Used by: `generate-mcp-config.py` (also obsolete)

3. **`scripts/check-dependencies.py`** - OBSOLETE
   - Purpose: Checked if uvx and Python installed before manual installation
   - Why obsolete: Claude Code CLI handles dependencies, uvx auto-installs MCPs
   - Used by: `install.sh` (deprecated)

4. **`scripts/detect-mcp-serena.py`** - PROBABLY OBSOLETE
   - Purpose: Unclear - likely related to Serena MCP detection
   - Check usage: If only used by install scripts, DELETE

5. **`scripts/mcp-bridge.py`** - CHECK USAGE
   - Purpose: Bridge for MCP communication?
   - Action: Check if used by `ace-cycle.py` or other runtime scripts
   - If only install-time: DELETE

6. **`scripts/mcp_client.py`** - CHECK USAGE
   - Purpose: MCP client library?
   - Action: Check if used by runtime scripts (`embeddings_engine.py`, etc.)
   - If only install-time: DELETE

### Installation Script (Keep but Simplify)
7. **`install.sh`** - SIMPLIFY
   - Current: Still calls obsolete scripts
   - Action: Remove Steps 1-3 (prerequisites, MCP config), keep only:
     - Create `.ace-memory/` directory
     - Initialize database
     - Show deprecation warning

## 🔍 Files to CHECK (May Still Be Used)

1. **`scripts/mcp-bridge.py`**
   ```bash
   grep -r "mcp-bridge" /path/to/ce-ai-ace --include="*.py" | grep -v ".git"
   ```
   If only in install scripts: DELETE
   If in runtime scripts: KEEP

2. **`scripts/mcp_client.py`**
   ```bash
   grep -r "mcp_client" /path/to/ce-ai-ace --include="*.py" | grep -v ".git"
   ```
   If only in install scripts: DELETE
   If in runtime scripts: KEEP

3. **`scripts/detect-mcp-serena.py`**
   ```bash
   grep -r "detect-mcp-serena" /path/to/ce-ai-ace --include="*.py" | grep -v ".git"
   ```
   If only in install scripts: DELETE

## ✅ Files to KEEP (Still Used)

### Runtime Scripts
- ✅ `scripts/ace-cycle.py` - Main orchestration (runtime)
- ✅ `scripts/embeddings_engine.py` - Semantic similarity (runtime)
- ✅ `scripts/domain_discovery.py` - Auto-domain detection (runtime)
- ✅ `scripts/semantic_pattern_extractor.py` - Pattern extraction (runtime)
- ✅ `scripts/generate-playbook.py` - Playbook generation (runtime)
- ✅ All other `ace-*.py` scripts - Slash commands (runtime)

### Configuration
- ✅ `.claude-plugin/plugin.json` - Plugin config + MCPs
- ✅ `.claude-plugin/marketplace.json` - Marketplace metadata
- ✅ `hooks/hooks.json` - Hook definitions

## 📝 Documentation to UPDATE

### Remove References to Obsolete Scripts
1. **`docs/GAP_ANALYSIS.md`**
   - Remove sections mentioning `generate-mcp-config.py`
   - Remove sections mentioning `mcp-conflict-detector.py`
   - Remove sections mentioning `check-dependencies.py`

2. **`docs/PHASE3_IMPLEMENTATION.md`**
   - Update "Smart MCP Installation" section
   - Change from "dynamic generation" to "plugin.json native"
   - Remove script references

3. **`docs/MCP_AUTO_INSTALL.md`**
   - Update to reflect `plugin.json` approach
   - Remove references to `.mcp.json` (we deleted it)
   - Remove references to obsolete scripts

## 🎯 Simplified Install Flow (After Cleanup)

### For End Users (Recommended)
```bash
/plugin marketplace add ce-dot-net/ce-ai-ace
/plugin install ace-orchestration@ace-plugin-marketplace
# Done! MCPs auto-install from plugin.json
```

### For Developers (Optional `install.sh`)
```bash
./install.sh  # Only creates .ace-memory/ and initializes DB
```

## ⚠️ Migration Steps

1. **Check usage of uncertain files**:
   ```bash
   grep -r "mcp-bridge\|mcp_client\|detect-mcp-serena" scripts/ --include="*.py"
   ```

2. **Delete confirmed obsolete files**:
   ```bash
   rm scripts/generate-mcp-config.py
   rm scripts/mcp-conflict-detector.py
   rm scripts/check-dependencies.py
   # Add others after verification
   ```

3. **Simplify install.sh**:
   - Remove Step 1 (check-dependencies)
   - Remove Step 3 (generate-mcp-config)
   - Keep only .ace-memory/ creation

4. **Update documentation**:
   - Search/replace references to obsolete scripts
   - Update architecture diagrams

5. **Test plugin installation**:
   ```bash
   /plugin install ace-orchestration
   # Verify MCPs auto-install
   # Verify hooks work
   # Verify patterns are detected
   ```

## 📊 Before/After Comparison

### Before (Phase 3 - Manual)
```
User runs: ./install.sh
  ↓ check-dependencies.py (check uvx)
  ↓ mcp-conflict-detector.py (check conflicts)
  ↓ generate-mcp-config.py (write config)
  ↓ Merge into ~/.config/claude-code/config.json
  ↓ Done
```
**Files**: 7 scripts + install.sh

### After (Phase 3+ - Automatic)
```
User runs: /plugin install ace-orchestration
  ↓ Claude Code reads plugin.json
  ↓ Registers chromadb-ace + serena-ace
  ↓ Auto-installs via uvx on first use
  ↓ Done
```
**Files**: plugin.json only

**Result**: -7 files, -200+ lines of code, 100% automatic!

---

**Next Steps**: Execute cleanup after verifying uncertain files
