# 🧪 ACE Plugin - Test Prompt for Claude Code

Copy and paste this into your Claude Code CLI session to test all Phase 3-5 features.

---

## 📋 **Test Prompt** (Copy Everything Below)

```
I want to test the ACE plugin Phase 3-5 features. Please help me:

1. First, run the automated test suite:
   python3 tests/test-phase-3-5.py

2. Create a Python file called test_ace_features.py with the following patterns that ACE should detect:

```python
from typing import TypedDict
from dataclasses import dataclass
from pathlib import Path

# Pattern 1: TypedDict for configs (py-001)
class ServerConfig(TypedDict):
    host: str
    port: int
    timeout: float

# Pattern 2: Dataclass for models (py-002)
@dataclass
class User:
    id: int
    name: str
    email: str

# Pattern 3: Context managers (py-004)
def read_config(path: Path) -> ServerConfig:
    with open(path, 'r') as f:
        data = f.read()
    return ServerConfig(host="localhost", port=8080, timeout=30.0)

# Pattern 4: F-strings (py-005)
def greet(user: User) -> str:
    return f"Hello, {user.name}! Your ID is {user.id}"

# Pattern 5: List comprehension (py-006)
def get_active_users(users: list[User]) -> list[str]:
    return [u.name for u in users if u.email]

# Pattern 6: Pathlib (py-007)
config_path = Path.cwd() / "config.json"

# Anti-pattern: Bare except (py-003) - should be flagged
def unsafe_operation():
    try:
        result = 1 / 0
    except:  # This is a bare except - anti-pattern!
        pass
```

3. After creating the file, check:
   - Did ACE detect the patterns?
   - Was CLAUDE.md updated with delta (not full rewrite)?
   - Check the console output for "🔄 Computing playbook delta..."

4. Verify the results:
   ```bash
   # Check patterns detected
   sqlite3 .ace-memory/patterns.db "SELECT bullet_id, name, confidence, observations FROM patterns"

   # Check CLAUDE.md was updated
   cat CLAUDE.md | grep -A2 "py-"

   # Check embeddings cache
   ls -lh .ace-memory/embeddings-cache.json

   # Check delta history
   cat .ace-memory/playbook-history.txt 2>/dev/null || echo "No delta history yet"
   ```

5. Test epoch management:
   ```bash
   python3 scripts/epoch-manager.py stats
   ```

6. Show me the results of all checks above so I can verify Phase 3-5 is working correctly!
```

---

## ✅ **Expected Results**

### Step 1: Automated Tests
```
🧪 ACE Plugin - Phase 3-5 Test Suite
======================================================================
🧪 Testing: Database migration (Phase 2)
   ✅ PASS
🧪 Testing: Embeddings engine
   ✓ Semantic similarity: 0.817
   ✓ Backend: Local
   ✅ PASS
🧪 Testing: Delta updater
   ✅ PASS
🧪 Testing: Epoch manager
   ✅ PASS
🧪 Testing: Serena detector
   ✅ PASS
🧪 Testing: Hooks configuration
   ✓ All 5 hooks configured
   ✅ PASS
...
📊 Test Results: 9 passed, 0 failed
✅ All tests passed! Plugin is ready to use.
```

### Step 2: File Creation
Claude should create the file successfully.

### Step 3: ACE Cycle Output
```
🔄 ACE: Starting reflection cycle for test_ace_features.py
🔍 Detected 7 pattern(s): py-001, py-002, py-003, py-004, py-005, py-006, py-007
🧪 Evidence: none
💡 Reflection complete
🔄 Computing playbook delta...
📊 Delta: +7 ~0 -0
  ✨ Added [py-00001] to section 'STRATEGIES AND HARD RULES'
  ✨ Added [py-00002] to section 'STRATEGIES AND HARD RULES'
  ...
✅ Delta applied successfully
✅ ACE cycle complete (7 patterns processed)
```

### Step 4: Database Check
```
[py-00001]|Use TypedDict for configs|0.0|1
[py-00002]|Use dataclasses for data structures|0.0|1
[py-00003]|Avoid bare except|0.0|1
...
```

### Step 5: CLAUDE.md Check
```markdown
## 🎯 STRATEGIES AND HARD RULES

[py-00001] helpful=0 harmful=0 :: **Use TypedDict for configs**
*Domain: python-typing | Language: python | Confidence: 0.0% (0/1)*

Define configuration with TypedDict for type safety and IDE support
```

### Step 6: Embeddings Cache
```
-rw-r--r-- 1 user staff 29K Oct 14 14:30 embeddings-cache.json
```

### Step 7: Epoch Stats
```
📊 Epoch Statistics

Epoch    Status       Patterns   Avg Conf     Duration
======================================================================
1        running      7          0.00         Running...
```

---

## 🎯 **What This Tests**

✅ **Phase 3 - Delta Updates**:
- CLAUDE.md updated incrementally (not full rewrite)
- Delta computation shown: `+7 ~0 -0`
- History logged

✅ **Phase 3 - Semantic Embeddings**:
- Embeddings engine working (Local backend)
- Cache created and used
- Pattern similarity calculated with embeddings

✅ **Phase 4 - Multi-Epoch**:
- Epochs table exists
- Epoch 1 running
- Pattern tracking active

✅ **Phase 5 - Serena Integration**:
- Hybrid detector functional
- Falls back to regex (Serena symbolic detection ready when needed)

✅ **All 5 Hooks**:
- AgentStart: CLAUDE.md injection (runs on agent start)
- PreToolUse: Pattern validation (runs before Edit/Write)
- PostToolUse: ACE cycle (runs after Edit/Write) ← **Main hook**
- AgentEnd: Output analysis (runs on agent end)
- SessionEnd: Cleanup (runs on session end)

---

## 🐛 **Troubleshooting**

If something doesn't work:

1. **No patterns detected?**
   ```bash
   # Check if file was actually created
   ls -l test_ace_features.py

   # Manually trigger ACE cycle
   echo "# trigger" >> test_ace_features.py
   ```

2. **Delta updates not working?**
   ```bash
   # Check symlink
   ls -la scripts/playbook_delta_updater.py

   # Should show: playbook_delta_updater.py -> playbook-delta-updater.py
   ```

3. **Embeddings failing?**
   ```bash
   # Install local backend
   pip install sentence-transformers
   ```

4. **Hooks not running?**
   ```bash
   # Restart Claude Code (hooks require restart)
   ```

---

## 🚀 **Success Criteria**

- ✅ All automated tests pass (9/9)
- ✅ 7 patterns detected from test file
- ✅ CLAUDE.md updated with delta (not full rewrite)
- ✅ Embeddings cache created (~29KB)
- ✅ Database has patterns with bullet_id
- ✅ Epoch 1 running
- ✅ Console shows delta computation messages

**If all checks pass, Phase 3-5 is fully operational! 🎉**
