# ACE Research Summary

## Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models

**Paper**: arXiv:2510.04618v1
**Authors**: Qizheng Zhang¹, Changran Hu², Shubhangi Upasani², Boyuan Ma², et al.
**Institutions**: ¹Stanford University, ²SambaNova Systems, ³UC Berkeley

---

## Executive Summary

ACE (Agentic Context Engineering) is a framework that improves LLM performance by **editing and growing the input context** instead of updating model weights. Context is treated as a living "playbook" maintained by three specialized roles—Generator, Reflector, Curator—with small delta items merged incrementally to avoid brevity bias and context collapse.

### Key Results
- **+10.6%** on AppWorld agent tasks
- **+8.6%** on finance reasoning
- **~86.9%** average latency reduction vs. strong context-adaptation baselines
- On AppWorld leaderboard: ReAct+ACE (59.4%) ≈ IBM CUGA (60.3%, GPT-4.1) using smaller DeepSeek-V3.1

---

## The Problem

### 1. Brevity Bias
Many prompt optimizers prioritize concise, broadly applicable instructions over comprehensive accumulation. For example, GEPA highlights brevity as a strength, but such abstraction can omit domain-specific heuristics, tool-use guidelines, or common failure modes.

### 2. Context Collapse
Methods that rely on monolithic rewriting by an LLM often degrade into shorter, less informative summaries over time, causing sharp performance declines.

**Example**: On AppWorld, a context with 18,282 tokens (66.7% accuracy) collapsed to just 122 tokens (57.1% accuracy) in one rewrite step—worse than baseline (63.7%)!

---

## The Solution: ACE Framework

### Three-Role Architecture

```
┌──────────────┐
│  Generator   │ → Produces reasoning trajectories
└──────┬───────┘
       ↓
┌──────────────┐
│  Reflector   │ → Distills concrete lessons
└──────┬───────┘
       ↓
┌──────────────┐
│   Curator    │ → Converts lessons into delta items
└──────────────┘
```

#### 1. Generator
- Executes tasks and produces trajectories (reasoning/tool calls)
- Exposes helpful vs harmful moves
- In our plugin: **User + Claude Code**

#### 2. Reflector
- Distills concrete lessons from execution traces
- Uses execution feedback and environment signals
- In our plugin: **Sequential-thinking MCP** (LLM-based analysis)

#### 3. Curator
- Converts lessons into typed **delta items** with counters
- Merges them **deterministically** with de-duplication and pruning
- In our plugin: **Pure algorithmic logic** (85% similarity threshold)

---

## Key Innovations

### 1. Incremental Delta Updates

Instead of regenerating contexts in full, ACE incrementally produces compact **delta contexts**: small sets of candidate bullets distilled by the Reflector and integrated by the Curator.

**Structure of a Bullet (Delta Item)**:
```javascript
{
  id: "unique-identifier",
  metadata: {
    helpful_count: 5,
    harmful_count: 1
  },
  content: "Reusable strategy or domain concept"
}
```

**Benefits**:
- ✅ Localization: Only relevant bullets updated
- ✅ Fine-grained retrieval: Focus on pertinent knowledge
- ✅ Incremental adaptation: Efficient merging/pruning
- ✅ Avoids computational cost of full rewrites

### 2. Grow-and-Refine

Beyond incremental growth, ACE ensures contexts remain compact and relevant through periodic or lazy refinement:

- **Grow**: Bullets with new identifiers are appended
- **Refine**: Existing bullets updated in place (increment counters)
- **De-duplicate**: Compare bullets via semantic embeddings
- **Timing**: Proactively (after each delta) or lazily (when context window exceeded)

### 3. Deterministic Merging

The Curator uses **lightweight, non-LLM logic** for merging:
- Semantic similarity (85% threshold) via string comparison
- Counter tracking (helpful/harmful votes)
- Pruning rules (remove <30% confidence after 10+ observations)

**Why deterministic?**
- No variance from LLM rewrites
- Reproducible results
- Lower latency and cost
- Preserves accumulated knowledge

---

## Results

### Agent Benchmarks (AppWorld)

| Method | Test-Normal TGC | Test-Challenge TGC | Average |
|--------|----------------|-------------------|---------|
| ReAct (baseline) | 63.7% | 41.5% | 42.4% |
| ReAct + ACE | **76.2%** | **57.3%** | **59.4%** |

**Key findings**:
- ACE works **without labeled supervision** (uses execution feedback only)
- Matches top production agent (IBM CUGA at 60.3%) using smaller model
- Surpasses CUGA on harder test-challenge split

### Domain-Specific Benchmarks (Finance)

| Method | FiNER | Formula | Average |
|--------|-------|---------|---------|
| Base LLM | 70.7% | 67.5% | 69.1% |
| ACE | **78.3%** | **85.5%** | **81.9%** |

**Key findings**:
- +8.6% average over strong baselines
- Comprehensive playbooks capture domain-specific concepts
- Effective with ground-truth labels or execution-only feedback

### Efficiency Gains

**Offline (AppWorld)**:
- **-82.3%** latency vs. GEPA
- **-75.1%** rollouts vs. GEPA

**Online (FiNER)**:
- **-91.5%** latency vs. Dynamic Cheatsheet
- **-83.6%** token cost vs. Dynamic Cheatsheet

---

## Design Principles

### 1. Contexts as Playbooks

> "We argue that contexts should function not as concise summaries, but as comprehensive, evolving playbooks—detailed, inclusive, and rich with domain insights."

Unlike humans who benefit from concise generalization, LLMs are more effective when provided with long, detailed contexts and can distill relevance autonomously.

### 2. Prevent Context Collapse

**Problem**: Iterative rewriting erodes details over time
**Solution**: Incremental delta updates with structured bullets

### 3. Avoid Brevity Bias

**Problem**: Compression drops domain-specific heuristics
**Solution**: Accumulate and organize, don't compress

### 4. Leverage Execution Feedback

**Problem**: Fine-tuning requires labeled data
**Solution**: Use natural signals (test results, code execution, API responses)

---

## Implementation Notes for Plugin

### Pattern Structure
```javascript
{
  id: "py-001",
  name: "Use TypedDict for configs",
  regex: /class\s+\w*Config\w*\(TypedDict\)/,
  domain: "python-typing",
  type: "helpful|harmful",
  description: "What this pattern does",
  observations: 10,
  successes: 8,
  failures: 1,
  neutrals: 1,
  confidence: 0.8,  // successes / observations
  insights: [
    {
      timestamp: "2025-10-14T...",
      insight: "Specific observation from Reflector",
      recommendation: "When to use/avoid",
      confidence: 0.9,
      appliedCorrectly: true
    }
  ],
  lastSeen: "2025-10-14T..."
}
```

### Thresholds (from paper)
- **Similarity threshold**: 85% (for merging patterns)
- **Prune threshold**: 30% (minimum confidence after 10 observations)
- **Confidence threshold**: 70% (for high-confidence classification)

### Curator Algorithm (Deterministic)
```javascript
function curate(newPattern, existingPatterns) {
  // 1. Find most similar pattern (same domain + type)
  const bestMatch = findMostSimilar(newPattern, existingPatterns);

  // 2. MERGE if >= 85% similar
  if (bestMatch.similarity >= 0.85) {
    return { action: 'merge', targetId: bestMatch.id };
  }

  // 3. PRUNE if low confidence (< 30% after 10+ obs)
  if (newPattern.observations >= 10 && confidence < 0.3) {
    return { action: 'prune' };
  }

  // 4. CREATE new pattern
  return { action: 'create' };
}
```

---

## Limitations

From the paper:

1. **Depends on Reflector quality**: If the Reflector fails to extract meaningful insights, context becomes noisy
2. **Not all tasks benefit**: Some tasks (e.g., HotPotQA, Game of 24) prefer concise instructions
3. **Feedback quality matters**: Without reliable signals (test results, execution outcomes), adaptation can degrade
4. **Context window constraints**: Eventually hits model's context limit (mitigated by grow-and-refine)

---

## Future Directions

1. **Selective unlearning**: Remove outdated or incorrect information (privacy/legal compliance)
2. **Online/continuous learning**: Adapt to distribution shifts without weight updates
3. **Multi-modal contexts**: Extend to images, audio, video
4. **Cross-model knowledge transfer**: Share playbooks across different LLMs
5. **Automated pattern discovery**: Learn new patterns beyond predefined set

---

## Citations

```bibtex
@article{zhang2025ace,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and Ma, Boyuan and Hong, Fenglu and Kamanuru, Vamsidhar and Rainton, Jay and Wu, Chen and Ji, Mengmeng and Li, Hanchen and Thakker, Urmish and Zou, James and Olukotun, Kunle},
  journal={arXiv preprint arXiv:2510.04618},
  year={2025}
}
```

---

## References

- **Paper**: https://arxiv.org/abs/2510.04618
- **AppWorld Leaderboard**: https://appworld.dev/leaderboard
- **Dynamic Cheatsheet**: https://github.com/suzgunmirac/dynamic-cheatsheet
- **GEPA**: DSPy implementation
- **MIPROv2**: DSPy implementation

---

**This research summary guides the implementation of the ACE plugin for Claude Code CLI.**
