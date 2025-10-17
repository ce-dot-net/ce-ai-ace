# ACE TRUE Architecture - Complete Implementation Guide

*Based on research paper analysis via pdfgrep - 2025-10-17*

## Overview

This document describes the TRUE ACE (Agentic Context Engineering) architecture as specified in the research paper, what we've implemented correctly, what's missing, and how pattern self-improvement works.

## Core Concepts from Research Paper

### 1. **Bullets, Not Just Patterns**

From paper (Section 3.1):
> "A core design principle of ACE is to represent context as a collection of structured, itemized **bullets**"

Each bullet consists of:
- **Metadata**: Unique ID, helpful counter, harmful counter
- **Content**: Strategy, domain concept, or common failure mode

**In our domain**: Coding patterns = bullets
- Pattern: "subprocess module usage" = one bullet
- Pattern: "pathlib for file operations" = another bullet

### 2. **The Complete ACE Cycle**

```
┌─────────────────────────────────────────────────────────────┐
│  1. GENERATOR: Write code using playbook (CLAUDE.md)        │
│     - Uses existing bullets as guidance                      │
│     - Produces reasoning trajectory                          │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  2. EXECUTION: Run code, gather feedback                     │
│     - Test results (passed/failed)                           │
│     - Error logs                                             │
│     - Performance metrics                                    │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  3. REFLECTOR: Discover patterns & analyze effectiveness     │
│     - Read raw code                                          │
│     - DISCOVER what patterns exist (imports, APIs, etc.)     │
│     - Tag existing bullets as helpful/harmful/neutral        │
│     - Create NEW bullets for discovered patterns             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  4. CURATOR: Merge, prune, deduplicate                       │
│     - Merge bullets at 85% similarity                        │
│     - Prune bullets below 30% confidence                     │
│     - Deterministic (non-LLM) algorithm                      │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  5. UPDATE PLAYBOOK: Generate CLAUDE.md with bullets         │
│     - Delta updates (add new, update existing)               │
│     - Include bullet IDs for feedback tracking               │
│     - Organized by domain/confidence                         │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  6. GENERATOR FEEDBACK: Tag bullets during next execution    │
│     - Generator highlights: "This bullet was helpful!"       │
│     - Increment helpful_count or harmful_count               │
│     - Guides pattern self-improvement                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     └──────────► LOOP BACK TO STEP 1
```

## Current Implementation Status

### ✅ Correctly Implemented (v2.3.9)

1. **Agent-Based Pattern Discovery** (`ace-cycle.py`)
   - ✅ Reflector agent discovers patterns from raw code
   - ✅ No hardcoded keyword matching
   - ✅ Outputs structured pattern definitions
   - ✅ File: `agents/reflector.md` fully rewritten

2. **Bullet Structure** (`ace-cycle.py` database schema)
   - ✅ `bullet_id` field: `[py-00001]`, `[js-00023]`
   - ✅ `helpful_count` and `harmful_count` fields present
   - ✅ Unique IDs, metadata, content

3. **Curator Algorithm** (`ace-cycle.py`)
   - ✅ Merge at 85% similarity (semantic embeddings)
   - ✅ Prune at 30% confidence after 10 observations
   - ✅ Deterministic, non-LLM logic

4. **Multi-Epoch Offline Training** (`offline-training.py`)
   - ✅ 5 epochs default (from paper Table 3: +2.6% improvement)
   - ✅ Revisits training data for progressive learning
   - ✅ Tracks pattern evolution across epochs

5. **Domain Taxonomy Discovery** (`domain_discovery.py`)
   - ✅ Bottom-up discovery (no hardcoded domains)
   - ✅ Agent-based analysis
   - ✅ Three levels: concrete, abstract, principles

### ❌ Missing Components

1. **Generator Feedback Loop** ⚠️ HIGH PRIORITY
   - ❌ No mechanism to tag bullets during task execution
   - ❌ `helpful_count` and `harmful_count` not incremented
   - ❌ Pattern self-improvement incomplete

2. **Playbook Usage Tracking**
   - ❌ CLAUDE.md generated but not tracked
   - ❌ No visibility into which patterns are actually used

3. **Post-Execution Feedback Hook**
   - ❌ No hook to ask "Which patterns helped/hurt?"
   - ❌ Missing: `PostTaskCompletion` hook

### ⚠️ Partially Implemented

1. **CLAUDE.md Playbook Generation** (`generate-playbook.py`)
   - ✅ Generates playbook from patterns
   - ⚠️ Bullet IDs present but not prominently displayed
   - ❌ Missing usage instructions for feedback

## Pattern Self-Improvement Mechanism

### How It Should Work (from Paper)

From Section 3.1:
> "When solving new problems, the Generator highlights which bullets were useful or misleading, providing feedback that guides the Reflector in proposing corrective updates."

### Implementation Plan

#### Phase 1: Pattern Discovery (COMPLETED ✅)
```python
# ace-cycle.py - invoke_reflector_agent()
# Reflector discovers patterns from code
discovered_patterns = [
    {
        "id": "discovered-subprocess-usage",
        "name": "subprocess module usage",
        "helpful_count": 0,  # Will be incremented by feedback
        "harmful_count": 0,
        ...
    }
]
```

#### Phase 2: Bullet Feedback (TODO ❌)
```python
# NEW: Post-task feedback collection
# After Claude uses CLAUDE.md to solve a task:
def collect_pattern_feedback(task_result, patterns_used):
    """
    Ask Claude: Which patterns from CLAUDE.md were helpful/harmful?

    Returns:
        {
            "helpful_bullets": ["[py-00001]", "[py-00003]"],
            "harmful_bullets": ["[py-00002]"],
            "neutral_bullets": ["[py-00004]"]
        }
    """
    # Implementation needed
    pass

def update_pattern_feedback(feedback):
    """
    Increment helpful_count or harmful_count in database.
    """
    for bullet_id in feedback['helpful_bullets']:
        # UPDATE patterns SET helpful_count = helpful_count + 1
        pass
    for bullet_id in feedback['harmful_bullets']:
        # UPDATE patterns SET harmful_count = harmful_count + 1
        pass
```

#### Phase 3: Self-Improvement (TODO ❌)
```python
# Reflector uses feedback to refine patterns
def refine_patterns_based_on_feedback():
    """
    Patterns with high harmful_count get:
    - Lower confidence scores
    - Marked for review/pruning
    - Additional analysis by Reflector

    Patterns with high helpful_count get:
    - Higher confidence scores
    - Promoted in playbook
    - Used as examples for similar patterns
    """
    pass
```

## Database Schema (Current)

```sql
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    bullet_id TEXT UNIQUE NOT NULL,      -- [py-00001]
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    language TEXT NOT NULL,
    observations INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    neutrals INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,     -- ✅ Present but not used!
    harmful_count INTEGER DEFAULT 0,     -- ✅ Present but not used!
    confidence REAL DEFAULT 0.0,
    last_seen TEXT,
    created_at TEXT
);
```

## Next Steps to Complete ACE

### 1. Implement Generator Feedback Hook

**File**: `hooks/PostTaskCompletion.py` (NEW)
- Triggered after each task completion
- Asks Claude to tag bullets
- Updates `helpful_count`/`harmful_count`

### 2. Update Playbook Generation

**File**: `scripts/generate-playbook.py`
- Prominently display bullet IDs: `[py-00001]`
- Add usage instructions for feedback
- Group by helpful_count (show most helpful first)

### 3. Enhance Reflector Prompts

**File**: `agents/reflector.md`
- Add: "Review existing bullets and tag as helpful/harmful"
- Include: Bullet tagging in output format

### 4. Add Confidence Scoring Based on Feedback

**File**: `ace-cycle.py` - New function
```python
def calculate_confidence_with_feedback(pattern):
    """
    Confidence = (successes + helpful_count) / (observations + helpful_count + harmful_count)

    This combines:
    - Observation-based confidence (successes/failures)
    - Usage-based feedback (helpful/harmful tags)
    """
    numerator = pattern['successes'] + pattern['helpful_count']
    denominator = pattern['observations'] + pattern['helpful_count'] + pattern['harmful_count']
    return numerator / max(denominator, 1)
```

### 5. Test Complete Cycle

**Scenario**:
1. Write code → Reflector discovers patterns
2. Generate CLAUDE.md with bullet IDs
3. Next task uses CLAUDE.md
4. Collect feedback on which bullets helped
5. Update database
6. Verify confidence scores improve over time

## Key Research Paper Quotes

### On Bullets & Feedback
> "The concept of a bullet consists of (1) metadata, including a unique identifier and counters tracking how often it was marked **helpful or harmful**; and (2) content, capturing a small unit such as a reusable strategy, domain concept, or common failure mode."
>
> "When solving new problems, the **Generator highlights which bullets were useful or misleading**, providing feedback that guides the Reflector in proposing corrective updates."

### On Delta Updates
> "Rather than regenerating contexts in full, ACE incrementally produces compact **delta contexts**: small sets of candidate bullets distilled by the Reflector and integrated by the Curator."

### On Multi-Epoch Training
> "We set the maximum number of Reflector refinement rounds and the maximum number of **epochs in offline adaptation to 5**."
>
> Table 3 shows multi-epoch training adds **+2.6% improvement**.

## Conclusion

**What we got right**:
- Agent-based pattern discovery (not hardcoded!)
- Bullet structure with IDs and counters
- Curator merge/prune logic
- Multi-epoch offline training

**What we're missing**:
- Generator feedback loop (THE critical piece!)
- Actually using `helpful_count`/`harmful_count`
- Post-task feedback collection

**The fix**: Implement the Generator feedback mechanism so patterns can self-improve based on actual usage, completing the TRUE ACE cycle from the research paper.
