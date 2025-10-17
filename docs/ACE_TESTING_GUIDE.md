# ACE Testing Guide - Complete Cycle Validation

*Test plan for validating the TRUE ACE architecture implementation*

## Test Scenarios

### Test 1: Pattern Discovery (Basic)

**Objective**: Verify that Reflector agent discovers patterns from raw code

**Steps**:
1. Write a Python file using subprocess, pathlib, and SQLite
2. Trigger ACE reflection cycle
3. Verify patterns are discovered (not hardcoded!)

**Expected Output**:
```
🔬 ACE Pattern Discovery Request
Analyzing test.py (523 chars). Please invoke the reflector agent to DISCOVER patterns.

Expected discovered patterns:
- discovered-subprocess-usage
- discovered-pathlib-operations
- discovered-sqlite-queries
```

**Success Criteria**:
- ✅ Agent discovers 3+ patterns
- ✅ Patterns have full definition (id, name, description, domain, language)
- ✅ No hardcoded "stripe" or "auth" patterns appear

### Test 2: Bullet Structure

**Objective**: Verify patterns are stored as bullets with IDs and counters

**Steps**:
1. After Test 1, check `.ace-memory/patterns.db`
2. Query: `SELECT bullet_id, helpful_count, harmful_count FROM patterns`

**Expected Output**:
```
[py-00001] | helpful=0 | harmful=0
[py-00002] | helpful=0 | harmful=0
[py-00003] | helpful=0 | harmful=0
```

**Success Criteria**:
- ✅ Bullet IDs generated in ACE format: `[domain-NNNNN]`
- ✅ `helpful_count` and `harmful_count` fields exist
- ✅ Patterns have metadata (observations, successes, failures)

### Test 3: CLAUDE.md Generation

**Objective**: Verify playbook displays bullet IDs prominently

**Steps**:
1. After Test 1, generate playbook: `python3 scripts/generate-playbook.py`
2. Check `CLAUDE.md` content

**Expected Output**:
```markdown
## 🎯 STRATEGIES AND HARD RULES

[py-00001] helpful=0 harmful=0 :: **subprocess module usage**
*Domain: python-stdlib | Language: python | Confidence: 90.0% (9/10)*

Uses Python subprocess module for running external commands...
```

**Success Criteria**:
- ✅ Bullet IDs displayed: `[py-00001]`
- ✅ helpful/harmful counters shown
- ✅ Organized by confidence level
- ✅ Domain taxonomy section (if 10+ patterns)

### Test 4: Pattern Feedback Loop

**Objective**: Verify Generator can tag bullets as helpful/harmful

**Steps**:
1. Create `.ace-memory/feedback.json`:
   ```json
   {
     "helpful": ["py-00001", "py-00003"],
     "harmful": ["py-00002"],
     "neutral": []
   }
   ```
2. Run: `python3 scripts/collect-pattern-feedback.py < /dev/null`
3. Check database: `SELECT bullet_id, helpful_count, harmful_count FROM patterns`

**Expected Output**:
```
[py-00001] | helpful=1 | harmful=0
[py-00002] | helpful=0 | harmful=1
[py-00003] | helpful=1 | harmful=0
```

**Success Criteria**:
- ✅ `helpful_count` incremented for py-00001, py-00003
- ✅ `harmful_count` incremented for py-00002
- ✅ Confidence scores recalculated
- ✅ CLAUDE.md regenerated automatically

### Test 5: Confidence with Feedback

**Objective**: Verify new confidence formula incorporates feedback

**Steps**:
1. After Test 4, check confidence scores
2. Formula: `(successes + helpful) / (observations + helpful + harmful)`

**Expected Calculation**:
```python
# Pattern py-00001:
# Before: confidence = 9/10 = 0.90
# After:  confidence = (9 + 1) / (10 + 1 + 0) = 10/11 = 0.909

# Pattern py-00002:
# Before: confidence = 5/10 = 0.50
# After:  confidence = (5 + 0) / (10 + 0 + 1) = 5/11 = 0.455
```

**Success Criteria**:
- ✅ Helpful feedback increases confidence slightly
- ✅ Harmful feedback decreases confidence
- ✅ Formula matches research paper specification

### Test 6: Curator Merge/Prune

**Objective**: Verify deterministic merge (85%) and prune (30%) logic

**Steps**:
1. Create similar patterns (e.g., "subprocess usage" vs "subprocess module")
2. Trigger reflection
3. Verify patterns merge at 85% similarity

**Expected Behavior**:
```
🔀 Merged: subprocess module usage (92% similar)
```

**Success Criteria**:
- ✅ Similar patterns merged at ≥85% similarity
- ✅ Low confidence patterns (<30%) pruned after 10+ observations
- ✅ Semantic embeddings used (Claude → ChromaDB → Jaccard fallback)

### Test 7: Multi-Epoch Offline Training

**Objective**: Verify 5-epoch training improves patterns

**Steps**:
1. Run: `python3 scripts/offline-training.py --epochs 5 --source test-files`
2. Monitor confidence scores across epochs

**Expected Output**:
```
📚 Epoch 1/5
  Processing 20/20 training examples...
  ✅ Epoch 1 complete:
     Patterns processed: 45
     Patterns refined: 12
     Avg confidence: 65.2% → 67.8%
     Improvement: +2.6% 📈

📚 Epoch 2/5
  ...
```

**Success Criteria**:
- ✅ Avg confidence improves across epochs
- ✅ ~+2.6% improvement (per research paper Table 3)
- ✅ Patterns refined through re-observation
- ✅ Playbook generated after training

### Test 8: Domain Taxonomy Discovery

**Objective**: Verify bottom-up domain discovery (no hardcoded domains)

**Steps**:
1. Accumulate 10+ patterns
2. Trigger domain discovery
3. Check `.ace-memory/domain_taxonomy.json`

**Expected Output**:
```json
{
  "concrete": {
    "python-subprocess": {
      "patterns": ["py-00001", "py-00005"],
      "description": "External command execution patterns",
      "evidence": ["scripts/ace-cycle.py", "scripts/offline-training.py"]
    }
  },
  "abstract": {
    "safe-external-calls": {
      "instances": ["python-subprocess", "python-requests"],
      "description": "Patterns for safely calling external systems"
    }
  },
  "principles": {
    "defensive-programming": {
      "applied_in": ["safe-external-calls", "error-handling"],
      "description": "Defensive coding practices"
    }
  }
}
```

**Success Criteria**:
- ✅ Domains discovered from actual patterns (not hardcoded)
- ✅ Three levels: concrete, abstract, principles
- ✅ Agent-based discovery (domain-discoverer agent)
- ✅ CLAUDE.md includes taxonomy section

### Test 9: PostTaskCompletion Hook

**Objective**: Verify hook triggers after task completion

**Steps**:
1. Complete a coding task
2. Check if hook runs: `hooks/PostTaskCompletion.sh`
3. Verify feedback request appears

**Expected Output**:
```
🔄 ACE Generator Feedback Request

Task completed. Please provide feedback on which patterns from CLAUDE.md helped or hurt.

Available bullets: ["py-00001", "py-00002", "py-00003"]
```

**Success Criteria**:
- ✅ Hook triggers after task completion
- ✅ Feedback request displayed
- ✅ Bullet IDs extracted from CLAUDE.md
- ✅ Manual feedback via `.ace-memory/feedback.json` works

### Test 10: Complete End-to-End Cycle

**Objective**: Validate full ACE cycle from code → feedback → improvement

**Scenario**:
1. **Day 1**: Write code using subprocess
2. **ACE**: Discovers "subprocess usage" pattern → `[py-00001]`
3. **Day 2**: Use CLAUDE.md to guide new task
4. **Feedback**: Tag `[py-00001]` as helpful
5. **ACE**: Increments helpful_count, boosts confidence
6. **Day 3**: Pattern appears higher in playbook
7. **Continuous**: Pattern self-improves over time

**Success Criteria**:
- ✅ Pattern discovered from code
- ✅ Bullet stored with ID
- ✅ CLAUDE.md generated
- ✅ Feedback collected
- ✅ Confidence updated
- ✅ Playbook re-ranked
- ✅ Pattern improves over time

## Manual Test Commands

```bash
# Test 1: Pattern Discovery
cd /path/to/project
echo 'import subprocess; subprocess.run(["ls"])' > test.py
python3 plugins/ace-orchestration/scripts/ace-cycle.py < /dev/null

# Test 2: Check Database
sqlite3 .ace-memory/patterns.db "SELECT bullet_id, helpful_count, harmful_count FROM patterns"

# Test 3: Generate Playbook
python3 plugins/ace-orchestration/scripts/generate-playbook.py

# Test 4: Test Feedback
echo '{"helpful":["py-00001"],"harmful":[],"neutral":[]}' > .ace-memory/feedback.json
python3 plugins/ace-orchestration/scripts/collect-pattern-feedback.py < /dev/null

# Test 5: Check Updated Confidence
sqlite3 .ace-memory/patterns.db "SELECT bullet_id, confidence, helpful_count FROM patterns"

# Test 7: Offline Training
python3 plugins/ace-orchestration/scripts/offline-training.py --epochs 5 --source test-files

# Test 8: Domain Discovery
/ace-orchestration:ace-status  # Check if 10+ patterns
# Domain discovery triggers automatically
```

## Success Metrics

### Pattern Discovery
- ✅ 3+ patterns discovered from 50 lines of code
- ✅ 0 hardcoded patterns appear
- ✅ Pattern definitions include all required fields

### Bullet Structure
- ✅ Bullet IDs in ACE format: `[domain-NNNNN]`
- ✅ helpful/harmful counters functional
- ✅ Metadata tracked (observations, confidence)

### Feedback Loop
- ✅ Feedback increments counters
- ✅ Confidence recalculated correctly
- ✅ CLAUDE.md updates automatically

### Self-Improvement
- ✅ Helpful patterns gain confidence
- ✅ Harmful patterns lose confidence
- ✅ Patterns self-improve over 5+ observations

### Multi-Epoch
- ✅ +2-3% improvement per research paper
- ✅ Convergence after 3-5 epochs
- ✅ Patterns refined progressively

## Known Limitations

### From Research Paper (Appendix B)
> "A potential limitation of ACE is its reliance on a reasonably strong Reflector: if the Reflector fails to extract meaningful insights, the quality of the context will suffer."

**Our Mitigation**:
- Use Sonnet 4.5 for Reflector (strong model)
- Iterative refinement (5 rounds)
- Multi-epoch offline training
- Human feedback as fallback

### Current Implementation
- ⚠️ PostTaskCompletion hook requires manual feedback (`.ace-memory/feedback.json`)
- ⚠️ No automatic feedback collection yet (future: agent-based)
- ⚠️ Domain discovery requires 10+ patterns threshold

## Next Steps

1. ✅ Run Test 1-6 manually
2. ✅ Fix any issues discovered
3. ✅ Run Test 7-10 for full validation
4. ✅ Document results
5. ✅ Create release v2.3.9

## Conclusion

This test plan validates the TRUE ACE architecture as specified in the research paper:
- Agent-based pattern discovery (not hardcoded)
- Bullet structure with feedback counters
- Generator feedback loop for self-improvement
- Multi-epoch offline training
- Bottom-up domain taxonomy

All core components have been implemented and are ready for testing.
