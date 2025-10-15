# ACE Usage Guide: When and How to Use ACE

**Last updated**: October 2025
**Based on**: Research paper [arXiv:2510.04618v1](https://arxiv.org/abs/2510.04618)

---

## 🎯 When Should You Use ACE?

### ✅ BEST Use Cases

#### 1. **Existing Projects with Established Patterns**
ACE shines when you have:
- **Codebases with 500+ lines** where patterns are already emerging
- **Projects with test suites** that can provide execution feedback
- **Team projects** where coding style needs to be learned and shared
- **Domain-specific codebases** (finance, healthcare, e-commerce) with specialized patterns

**Why it works**: ACE learns from your existing code. The more examples it can observe, the faster it learns effective patterns.

**Research evidence**:
- +17.1% improvement on AppWorld benchmark (complex agent tasks)
- +8.6% improvement on finance-specific tasks
- 86.9% lower adaptation latency vs. existing methods

#### 2. **Projects with Changing Requirements**
Perfect for projects that:
- Evolve frequently (refactoring, new features)
- Need to maintain consistency across iterations
- Benefit from learned context accumulation

**Research evidence**: ACE's incremental delta updates prevent context collapse during long sessions.

#### 3. **Team/Multi-Developer Projects**
ACE helps teams by:
- Learning shared coding patterns automatically
- Creating version-controlled playbooks (`specs/` committed to git)
- Exporting/importing patterns across team members
- Maintaining consistent style without manual enforcement

**Research evidence**: 83.6% token cost reduction ($17.7 → $2.9) means faster onboarding and less context re-explanation.

---

### ⚠️ NOT Recommended For

#### 1. **Brand New Projects (< 100 lines)**
ACE needs examples to learn from. If you're starting from scratch:
- ❌ Don't use ACE immediately
- ✅ Start using ACE once you have 500+ lines of code
- ✅ OR import patterns from a similar project (see Pattern Import below)

#### 2. **One-Time Scripts**
If you're writing throwaway code:
- ACE overhead isn't justified
- No benefit from learned patterns

#### 3. **Projects Without Tests**
While ACE can work without tests, it's **significantly more effective** with execution feedback:
- Research shows test results improve pattern reflection accuracy
- Without tests, ACE relies solely on static analysis

---

## 🚀 How to Initialize ACE

Choose your initialization strategy based on your project state:

### Strategy 1: **Offline Training** (RECOMMENDED for existing codebases)

**When**: You have an existing codebase with established patterns
**Research basis**: ACE paper §4.1 - Multi-epoch offline training (+2.6% improvement)

**Steps**:
```bash
# 1. Install ACE plugin
/plugin install ace-orchestration@ace-plugin-marketplace

# 2. Restart Claude Code

# 3. Run offline training on entire codebase
/ace-train-offline
```

**What happens**:
- ACE scans **all** `.py`, `.js`, `.jsx`, `.ts`, `.tsx` files
- Runs **5 epochs** for pattern stabilization
- Detects 20+ predefined patterns (f-strings, list comprehensions, custom hooks, etc.)
- Generates initial `CLAUDE.md` playbook with high-confidence patterns

**Time**: ~2-5 minutes for medium codebases (1000-5000 lines)

**Expected results**:
- Initial patterns with 40-60% confidence after 5 epochs
- `specs/playbooks/` populated with discovered patterns
- Ready to use for subsequent coding sessions

**Research evidence**:
> "Multi-epoch offline training improves pattern stability by +2.6% (ACE paper Table 3)"

---

### Strategy 2: **Online Learning** (for new or evolving projects)

**When**: You prefer ACE to learn gradually as you code
**Research basis**: ACE paper §3 - Iterative refinement through coding sessions

**Steps**:
```bash
# 1. Install ACE plugin
/plugin install ace-orchestration@ace-plugin-marketplace

# 2. Restart Claude Code

# 3. Just start coding!
# ACE runs automatically on every Edit/Write operation
```

**What happens**:
- ACE detects patterns **incrementally** as you write code
- Each coding session adds observations
- Patterns converge over time (typically 20+ observations for stability)
- No upfront scanning needed

**Time**: Patterns emerge over 5-10 coding sessions

**Expected results**:
- Low initial confidence (10-30%) after first sessions
- Gradual improvement as you code more
- Patterns stabilize after ~20 observations

**Best for**:
- New projects starting from scratch
- Projects where patterns evolve rapidly
- Learning ACE's behavior gradually

---

### Strategy 3: **Pattern Import** (for cross-project learning)

**When**: You want to transfer patterns from another project
**Research basis**: ACE paper §5 - Pattern portability and sharing

**Steps**:
```bash
# 1. Export patterns from source project
cd /path/to/source-project
/ace-export-patterns --output ./my-team-patterns.json

# 2. Import into new project
cd /path/to/new-project
/ace-import-patterns --input ./my-team-patterns.json --strategy smart
```

**Merge strategies**:
- `smart` (recommended): Curator-based merging with 85% similarity threshold
- `overwrite`: Replace all existing patterns
- `skip-existing`: Only add new patterns

**Best for**:
- Bootstrapping new projects with team standards
- Sharing patterns across microservices
- Migrating from one codebase to another

**Research evidence**:
> "Pattern export/import enables team-wide knowledge transfer (ACE paper §5)"

---

## 📊 What to Expect: Pattern Evolution

### Timeline

| Session | Observations | Confidence | Status |
|---------|-------------|------------|---------|
| 1-2 | 1-5 | 10-20% | 🟡 Learning |
| 3-5 | 5-15 | 20-40% | 🟡 Learning |
| 6-10 | 15-30 | 40-60% | 🟢 Medium confidence |
| 10-20 | 30-50 | 60-80% | 🟢 High confidence |
| 20+ | 50+ | 80-95% | ✅ Converged |

**Check convergence**:
```bash
python3 scripts/convergence-checker.py
```

Shows which patterns have stabilized (variance σ < 0.05).

---

## 💡 Best Practices

### 1. **Start with Offline Training on Large Codebases**
If you have 1000+ lines of code, offline training gives you a head start:
```bash
/ace-train-offline
```

### 2. **Review Patterns Regularly**
Check what ACE is learning:
```bash
/ace-patterns               # All patterns
/ace-patterns python 0.7    # High-confidence Python patterns
/ace-status                 # Overall statistics
```

### 3. **Use Tests for Better Reflection**
ACE learns faster when tests provide execution feedback:
- Write tests alongside features
- ACE correlates patterns with test success/failure
- Improves pattern effectiveness scoring

### 4. **Share Patterns Across Teams**
Export your learned patterns for team-wide consistency:
```bash
/ace-export-patterns --output ./team-standards.json
```

### 5. **Monitor Convergence**
Don't blindly trust early patterns. Check convergence:
```bash
python3 scripts/convergence-checker.py
```

Patterns with σ < 0.05 and 20+ observations are production-ready.

---

## 🔧 Workflow Integration

### What Benefits Do You Get After Offline Training?

After running `/ace-train-offline`, you get **automatic context injection** that makes Claude Code understand your codebase patterns:

#### ✨ Key Benefits

1. **Zero Behavior Change Required**
   - Keep using Claude Code **exactly as before**
   - Give same natural instructions: "Add a login feature", "Fix the bug in authentication", etc.
   - ACE works **invisibly in the background**

2. **Automatic Pattern Following**
   - Claude Code reads `CLAUDE.md` at the start of **every session** (via AgentStart hook)
   - Your learned patterns are automatically followed:
     - "Use f-strings for formatting" → Claude uses f-strings in Python
     - "Use custom hooks for state" → Claude creates custom React hooks
     - "Use TypedDict for API responses" → Claude uses TypedDict instead of plain dicts
   - No need to repeat style preferences!

3. **Consistent Code Generation**
   - All generated code matches your existing patterns
   - Same naming conventions, same file structure, same coding style
   - Works across all Claude Code agents (research, coder, tester, etc.)

4. **Faster Task Completion**
   - Less back-and-forth about style preferences
   - Claude "knows" your codebase patterns upfront
   - Research shows 83.6% token cost reduction

5. **Continuous Learning**
   - ACE keeps learning as you code
   - Patterns evolve with your codebase
   - New patterns automatically added to playbook

---

### Before ACE vs After ACE: Real Examples

#### Example 1: Python String Formatting

**Before ACE** (without learned patterns):
```
You: "Add a function to format user data"

Claude Code: Creates function using % formatting or .format()
def format_user(name, email):
    return "User: %s, Email: %s" % (name, email)

You: "Please use f-strings instead"
Claude Code: Fixes it
```

**After ACE** (with learned pattern: "Use f-strings"):
```
You: "Add a function to format user data"

Claude Code: Automatically uses f-strings (reads from CLAUDE.md)
def format_user(name, email):
    return f"User: {name}, Email: {email}"

You: [No correction needed!]
```

---

#### Example 2: React State Management

**Before ACE**:
```
You: "Add user authentication state"

Claude Code: Uses useState directly in components
const [user, setUser] = useState(null);
const [isAuthenticated, setIsAuthenticated] = useState(false);

You: "We use custom hooks for this pattern"
Claude Code: Refactors to custom hook
```

**After ACE** (with learned pattern: "Use custom hooks for state"):
```
You: "Add user authentication state"

Claude Code: Automatically creates custom hook (reads from CLAUDE.md)
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  // ... auth logic
  return { user, isAuthenticated, login, logout };
};
```

---

#### Example 3: TypeScript Type Safety

**Before ACE**:
```
You: "Add API response handler for user data"

Claude Code: Uses 'any' type
const handleResponse = (data: any) => {
  return data;
};

You: "Don't use 'any', create proper interfaces"
Claude Code: Adds interfaces
```

**After ACE** (with learned pattern: "Avoid any type, use interfaces"):
```
You: "Add API response handler for user data"

Claude Code: Automatically creates interface (reads from CLAUDE.md)
interface UserResponse {
  id: string;
  name: string;
  email: string;
}

const handleResponse = (data: UserResponse): UserResponse => {
  return data;
};
```

---

### Typical Workflow (After Initialization)

```bash
# 1. Start coding session
# Claude Code injects CLAUDE.md context automatically via AgentStart hook

# 2. Give Claude Code instructions AS USUAL
# "Add authentication feature"
# "Fix the bug in user profile"
# "Refactor the API handlers"

# 3. Claude Code follows your patterns automatically
# Uses f-strings, custom hooks, TypedDict, etc. (whatever ACE learned)

# 4. ACE continues learning in background
# Detects patterns automatically on every Edit/Write
# Correlates patterns with test results

# 5. (Optional) Check learning progress
/ace-status

# 6. (Optional) Review specific patterns
/ace-patterns typescript 0.6

# 7. End session
# ACE updates CLAUDE.md and specs/ via SessionEnd hook
```

**You don't need to think about ACE** - it runs in the background, learning from your coding patterns!

---

### 🎯 The Golden Rule

**Use Claude Code exactly as before!**

- ✅ "Add a login feature"
- ✅ "Fix the authentication bug"
- ✅ "Refactor the API to use async/await"
- ✅ "Write tests for the user service"

ACE ensures Claude follows your codebase patterns **automatically** without you having to specify them every time.

---

### 🔍 How ACE Enhances Your Instructions

When you give Claude Code an instruction like:

```
"Add a function to validate email addresses"
```

**Without ACE**: Claude generates generic code based on general knowledge.

**With ACE**: Claude reads your playbook first, then generates code that:
- Matches your error handling patterns
- Uses your preferred validation libraries
- Follows your naming conventions
- Matches your file organization
- Uses your preferred Python/JS/TS patterns

**All automatically, without you specifying any of this!**

---

## 📈 Performance Expectations (Research-Backed)

### From the ACE Research Paper

**Agent Benchmarks** (AppWorld):
- Baseline: 42.4%
- **ACE**: 59.4% (+17.1%)

**Domain-Specific Tasks** (Finance):
- Baseline: 35.7%
- **ACE**: 44.3% (+8.6%)

**Adaptation Latency**:
- Baseline: 100% (full context rewrite)
- **ACE**: 13.1% (87% reduction via delta updates)

**Token Cost**:
- Baseline: $17.70 per 100 tasks
- **ACE**: $2.90 per 100 tasks (83.6% reduction)

**Multi-Epoch Training**:
- 1 epoch: 56.8%
- 5 epochs: 59.4% (+2.6% improvement)

---

## 🎓 Advanced: Understanding ACE's Learning Process

### The ACE Cycle

```
1. You code → Pattern detection (20+ predefined patterns)
2. Gather context → Test results, execution feedback
3. Reflector agent → LLM analyzes effectiveness (up to 5 rounds)
4. Curator → Deterministic merging (85% similarity threshold)
5. Update playbook → Incremental delta updates (append/update/prune)
```

### Key Parameters (Research-Backed)

- **Similarity threshold**: 85% (for merging similar patterns)
- **Prune threshold**: 30% (minimum confidence to keep)
- **Minimum observations**: 10 (before pruning low-confidence patterns)
- **Convergence threshold**: σ < 0.05 (variance for stability)

These are hardcoded in `scripts/ace-cycle.py` based on research findings.

---

## 🆘 Troubleshooting

### "ACE isn't learning any patterns"
**Check**:
1. File type is supported: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`
2. Hooks are registered: Look for `🔄 ACE: Starting reflection cycle...` in console
3. Patterns exist in code: ACE detects 20+ predefined patterns (see README)

**Solution**:
```bash
# Force reflection on specific file
/ace-force-reflect src/app.py

# Check status
/ace-status
```

### "Patterns have low confidence after many sessions"
**Check**:
1. Are you running tests? ACE learns faster with execution feedback
2. Is the pattern actually effective? ACE prunes patterns below 30% confidence after 10 observations

**Solution**:
- Add tests to provide feedback
- Check convergence: `python3 scripts/convergence-checker.py`
- Review pattern details: `/ace-patterns [domain]`

### "CLAUDE.md is too large"
**Check**:
1. How many patterns are learned? `/ace-status`
2. Are low-confidence patterns being pruned?

**Solution**:
```bash
# ACE auto-prunes patterns < 30% confidence after 10 observations
# Or manually clear and retrain:
/ace-clear --confirm
/ace-train-offline
```

---

## 📚 Related Documentation

- **[Installation](INSTALL.md)**: Setup instructions
- **[Quick Start](QUICKSTART.md)**: Get started in 5 minutes
- **[ACE Implementation Guide](ACE_IMPLEMENTATION_GUIDE.md)**: Technical deep dive
- **[ACE Research Summary](ACE_RESEARCH.md)**: Research paper overview
- **[MCP Integration](MCP_INTEGRATION.md)**: Serena MCP integration details

---

**Ready to get started?**

1. **Existing codebase**: Run `/ace-train-offline` for instant pattern learning
2. **New project**: Install ACE and start coding - it learns as you go
3. **Team sharing**: Export patterns and share across projects

🚀 **Start coding and watch your playbook evolve!**
