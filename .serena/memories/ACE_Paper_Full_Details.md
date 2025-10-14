# ACE Paper - Full Technical Details (arXiv:2510.04618v1)

## Paper Location
- **Original PDF**: `/Users/ptsafaridis/Downloads/2510.04618v1.pdf`
- **Project Copy**: `docs/ACE_Paper_2510.04618v1.pdf`
- **MarkTechPost Summary**: `docs/ACE_MarkTechPost_Summary.pdf`
- **arXiv Link**: https://arxiv.org/abs/2510.04618

## Abstract (Full)

Large language model (LLM) applications such as agents and domain-specific reasoning increasingly rely on **context adaptation**—modifying inputs with instructions, strategies, or evidence, rather than weight updates.

Prior approaches improve usability but often suffer from:
1. **Brevity bias** - drops domain insights for concise summaries
2. **Context collapse** - iterative rewriting erodes details over time

Building on Dynamic Cheatsheet's adaptive memory, ACE treats contexts as **evolving playbooks** that accumulate, refine, and organize strategies through modular generation, reflection, and curation.

ACE prevents collapse with structured, incremental updates that preserve detailed knowledge and scale with long-context models.

## Related Work - Key Comparisons

### Dynamic Cheatsheet (DC)
- Test-time learning with adaptive external memory
- Continuously updates memory with inputs/outputs
- **Limitation**: Can suffer from context collapse with full rewrites
- **ACE Improvement**: Incremental delta updates prevent collapse

### GEPA (Genetic-Pareto)
- Reflective prompt evolution via natural language
- Maintains Pareto frontier of prompts
- **Limitation**: Brevity bias, compresses away details
- **ACE Improvement**: Grow-and-refine accumulates details

### MIPROv2
- Bayesian optimization of instructions + demonstrations
- **Limitation**: Focuses on optimization, not accumulation
- **ACE Improvement**: Continuous playbook evolution

### Reflexion
- Reflects on failures to improve planning
- **Limitation**: Single-turn reflection
- **ACE Improvement**: Multi-turn refinement with structured roles

## Method Details

### ACE Workflow (Detailed)

```
Input: Query Q, Current Context C
Output: Updated Context C'

1. Generator(Q, C) → Trajectory T
   - Produces reasoning steps
   - Tool calls and outputs
   - Execution results

2. Reflector(T) → Insights I (iterative refinement)
   - Round 1: Initial analysis
   - Round 2-N: Refine insights
   - Extract lessons from T

3. Curator(I, C) → Delta Context ΔC
   - Convert insights to bullets
   - Assign IDs and counters
   - Non-LLM merging logic

4. Merge(C, ΔC) → C' (deterministic)
   - Match bullets by ID
   - Increment counters
   - Deduplicate by embeddings
   - Lazy pruning when needed

Return C'
```

### Bullet Structure (Memory Entry)

```javascript
{
  // Metadata
  id: "unique-identifier-abc123",
  helpful_count: 5,
  harmful_count: 1,
  domain: "agent-planning",
  
  // Content
  content: "When authenticating fails, try phone number instead of email as username. Check API documentation for correct parameters. Do not proceed with workarounds.",
  
  // Tracking
  created_at: "2025-10-01T...",
  last_updated: "2025-10-14T...",
  observations: 6,
  success_rate: 0.83
}
```

### Merging Algorithm (Non-LLM)

```python
def merge_delta(context, delta_context):
    """Deterministic merging without LLM"""
    
    for bullet in delta_context:
        # 1. Check if ID exists
        if bullet.id in context.bullets:
            # Update existing
            context.bullets[bullet.id].helpful_count += bullet.helpful_count
            context.bullets[bullet.id].harmful_count += bullet.harmful_count
            context.bullets[bullet.id].last_updated = now()
        else:
            # 2. Check semantic similarity
            similar = find_similar(bullet, context.bullets, threshold=0.85)
            
            if similar:
                # Merge into similar bullet
                merge_into(similar, bullet)
            else:
                # 3. Append as new bullet
                context.bullets.append(bullet)
    
    # 4. Deduplicate (semantic embeddings)
    context.bullets = deduplicate(context.bullets)
    
    # 5. Lazy prune (if context too large)
    if len(context) > MAX_CONTEXT_SIZE:
        context.bullets = prune_low_confidence(context.bullets)
    
    return context
```

### De-duplication Strategy

Uses **semantic embeddings** (not just string matching):

```python
def deduplicate(bullets):
    """Remove semantically similar bullets"""
    embeddings = embed_all(bullets)  # Sentence embeddings
    
    clusters = []
    processed = set()
    
    for i, bullet in enumerate(bullets):
        if i in processed:
            continue
            
        # Find all similar bullets (cosine similarity > 0.85)
        similar_indices = find_similar_embeddings(
            embeddings[i], 
            embeddings, 
            threshold=0.85
        )
        
        # Merge all similar into one representative
        representative = merge_bullets([bullets[j] for j in similar_indices])
        clusters.append(representative)
        processed.update(similar_indices)
    
    return clusters
```

## Experimental Setup

### Baselines

1. **Base LLM** - No context engineering
2. **ICL (In-Context Learning)** - Few/many-shot examples
3. **MIPROv2** - Bayesian prompt optimization
4. **GEPA** - Genetic-Pareto prompt evolution
5. **Dynamic Cheatsheet (DC)** - Adaptive memory

### Model Used
- **DeepSeek-V3.1** (non-thinking mode)
- Used for ALL roles (Generator, Reflector, Curator)
- Isolates context effects from model capabilities

### Hyperparameters

**ACE Configuration**:
- Batch size: 1 (per-sample delta construction)
- Max Reflector refinement rounds: 5
- Max offline epochs: 5
- Similarity threshold: 0.85
- Prune threshold: 0.3 confidence after 10 observations

**Evaluation Metrics**:
- AppWorld: TGC (Task Goal Completion), SGC (Scenario Goal Completion)
- Finance: Exact match accuracy
- Efficiency: Latency (seconds), rollouts (count), token cost ($)

## Detailed Results

### AppWorld - Ablation Studies

| Method | TGC (Test-Normal) | SGC (Test-Normal) | Average |
|--------|------------------|------------------|---------|
| ReAct baseline | 63.7 | 42.9 | 42.4 |
| + ACE w/o Reflector or multi-epoch | 70.8 | 55.4 | 55.1 |
| + ACE w/o multi-epoch | 72.0 | 60.7 | 56.8 |
| + ACE (full) | **76.2** | **64.3** | **59.4** |

**Key Findings**:
- Reflector adds +4.3% (comparing row 2 vs row 1)
- Multi-epoch adds +2.6% (comparing row 3 vs row 2)
- Both together: +17.0% total improvement

### Finance - With/Without Ground Truth

| Setting | GT Labels | FiNER | Formula | Average |
|---------|-----------|-------|---------|---------|
| Offline | ✓ | 78.3 | 85.5 | 81.9 |
| Offline | ✗ | 71.1 | 83.0 | 77.1 |
| Online | ✓ | 76.7 | 76.5 | 76.6 |
| Online | ✗ | 67.3 | 78.5 | 72.9 |

**Key Findings**:
- Ground truth labels help (+4-5%)
- But execution feedback alone still improves (+8% over baseline)
- Online adaptation works well with good feedback

### Cost & Latency Analysis

**Offline (AppWorld)**:
| Method | Latency (s) | # Rollouts |
|--------|------------|-----------|
| GEPA | 53,898 | 1,434 |
| ACE | **9,517** (-82.3%) | **357** (-75.1%) |

**Online (FiNER)**:
| Method | Latency (s) | Token Cost ($) |
|--------|------------|---------------|
| DC (CU) | 65,104 | 17.7 |
| ACE | **5,503** (-91.5%) | **2.9** (-83.6%) |

**Why ACE is faster**:
- Non-LLM merging (deterministic)
- Localized updates (not full rewrites)
- Cached embeddings for deduplication

## AppWorld Leaderboard (Sept 20, 2025)

| Method | LLM | Test-Normal TGC | Test-Challenge TGC | Average |
|--------|-----|----------------|-------------------|---------|
| IBM CUGA | GPT-4.1 | 73.2 | 57.6 | 60.3 |
| ReAct + ACE | DeepSeek-V3.1 | **68.5** | **57.3** | **59.4** |
| LOOP | Qwen2.5-32B | 72.6 | 47.2 | 53.8 |
| ReAct baseline | GPT-4o | 48.8 | 30.2 | 36.0 |

**Key Achievement**:
- ACE with smaller model ≈ top production agent with GPT-4.1
- Surpasses IBM CUGA on harder test-challenge split
- Shows context engineering can match/exceed larger models

## Discussion Points

### Longer Context ≠ Higher Serving Cost

Modern serving optimizations make long contexts practical:
- **KV cache reuse** - Cache repeated context prefixes
- **KV cache compression** - Compress older context
- **KV cache offload** - Move to CPU/disk when not needed

**Amortized cost** decreases as context is reused across queries.

### Implications for Continuous Learning

ACE enables:
1. **Online adaptation** - Learn from distribution shifts
2. **No fine-tuning needed** - Context updates are cheaper
3. **Selective unlearning** - Remove outdated info easily
4. **Human oversight** - Contexts are interpretable

Contrast with weight updates:
- Expensive (GPU time)
- Opaque (hard to interpret)
- Difficult to undo (catastrophic forgetting)

### When ACE Works Best

✅ **Good fit**:
- Multi-step agents (tool use, planning)
- Domain-specific tasks (finance, legal, medical)
- Repeated similar queries (reuse playbook)
- Execution feedback available (tests, APIs)

❌ **Poor fit**:
- Single-turn questions (no accumulation benefit)
- Novel/rare tasks (no pattern reuse)
- No feedback signals (can't verify effectiveness)
- Already-optimal prompts (diminishing returns)

## Limitations & Future Work

### Limitations

1. **Reflector quality dependency**
   - Bad insights → noisy context
   - Requires reasonably capable LLM
   - Fallback: use execution outcomes only

2. **Feedback quality matters**
   - Without tests/outcomes, can degrade
   - Garbage in, garbage out
   - Mitigate: Higher confidence thresholds

3. **Context window limits**
   - Eventually hits model's max context
   - Mitigate: Aggressive pruning, summarization

4. **Not universal**
   - Some tasks prefer concise prompts
   - One-shot tasks don't benefit
   - Need to detect task type

### Future Work

1. **Automated pattern discovery**
   - Learn new patterns beyond predefined
   - Cluster similar code behaviors
   - Extract reusable templates

2. **Multi-modal contexts**
   - Images, diagrams, audio
   - Richer playbooks
   - Better for visual domains

3. **Cross-model transfer**
   - Share playbooks across LLMs
   - Model-agnostic strategies
   - Collaborative learning

4. **Hierarchical playbooks**
   - Organize by abstraction level
   - Domain → subdomain → specific
   - Better retrieval

5. **Human-in-the-loop**
   - Approve/reject bullets
   - Correct misclassifications
   - Guide learning direction

## Citation

```bibtex
@article{zhang2025ace,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and Ma, Boyuan and Hong, Fenglu and Kamanuru, Vamsidhar and Rainton, Jay and Wu, Chen and Ji, Mengmeng and Li, Hanchen and Thakker, Urmish and Zou, James and Olukotun, Kunle},
  journal={arXiv preprint arXiv:2510.04618},
  year={2025}
}
```

## Implementation Checklist (✅ = Done in Plugin)

- ✅ Three-role architecture (Generator, Reflector, Curator)
- ✅ Incremental delta updates
- ✅ Deterministic curator (non-LLM)
- ✅ Semantic similarity merging (85% threshold)
- ✅ Confidence-based pruning (30% threshold, 10 observations)
- ✅ Grow-and-refine mechanism
- ✅ Execution feedback (test results)
- ✅ Itemized bullets with counters
- ✅ Multi-epoch refinement (optional)
- ✅ Comprehensive playbooks (not summaries)
- ⚠️ Semantic embeddings for dedup (using string similarity instead - faster)
- ⚠️ Lazy pruning (using session-end pruning instead)

## Key Takeaways for Plugin

1. **Deterministic curator is critical** - No LLM variance
2. **85% similarity threshold** - Research-validated
3. **Incremental updates only** - Never full rewrites
4. **Execution feedback sufficient** - No labels needed
5. **Comprehensive > concise** - Accumulate details
6. **Multi-epoch helps** - Revisit training data
7. **Reflector quality matters** - Use structured prompts
8. **Context window management** - Prune proactively
