# Deep Research Report: LLM Reasoning Enhancement Breakthroughs

## Research Date: 2026-07-03
## Source: Research Agent 2 (deleg_020d3f19)
## Status: COMPREHENSIVE

---

## 1. MCTS / TREE SEARCH FOR LLMS

### rStar-Math (Microsoft, Jan 2025) — arXiv:2501.04519
- Small language models (7B/3.8B) rival OpenAI o1 via MCTS-guided "deep thinking" at test time
- Uses policy SLM + process reward model (PPM) SLM, both iteratively self-evolved
- Code-augmented CoT data synthesis via MCTS rollouts → verified reasoning trajectories
- Novel PPM training using pairwise preference (not absolute scores)
- Results:
  - Qwen2.5-Math-7B: 58.8% → 90.0% on MATH benchmark (+31.2%)
  - Phi3-mini-3.8B: 41.4% → 86.4% on MATH (+45%)
  - Surpasses o1-preview by +4.5% on MATH, +0.9% on AIME
- INTEGRATION: HIGH PRIORITY — MCTS + PPM is the architecture Timuclaude already planned

### RAP (Reasoning via Planning) — arXiv:2305.14992
- LLM serves as both world model AND reasoning agent; MCTS explores reasoning tree
- LLaMA-33B surpasses CoT on GPT-4 with 33% relative improvement
- INTEGRATION: YES — "LLM as world model" framing for step-state prediction

### Key GitHub Repos:
- queelius/mcts-reasoning — MCTS LLM reasoning with advanced sampling (updated Jun 2026)
- billyvinning/langchain-mcts — MCTS-SR in LangGraph, MIT license
- xinzhel/lits-llm — Modular tree search + chain reasoning, ACL 2026
- ManqingLiu/doubly-robust-mcts — Variance-minimizing, reduces sample count
- Saksham4796/momentum-guided-test-time-search — Momentum + MLX KV-cache on GSM8K
- JianChengXingYun/Em-Mcts — Dual-loop with meta-prompt evolution + global memory

### MCTS-LLM Core Loop:
1. Selection: UCB1 to pick promising node
2. Expansion: Generate K candidate next-steps via LLM (temp ~0.7)
3. Evaluation: PRM scores each step (0-1)
4. Backpropagation: Update visit counts and Q-values
5. Termination: Max depth reached or answer found
Key: Use code execution to verify intermediate math steps

---

## 2. PROCESS REWARD MODELS (PRMs)

### "Let's Verify Step by Step" (OpenAI, May 2023) — arXiv:2305.20050
- Process supervision (per-step) vs outcome supervision (final answer)
- PRM800K dataset: 800K step-level human feedback labels
- PRM assigns +/-/neutral for each reasoning step
- At inference: generate N solutions, PRM scores each step, select highest aggregate
- Results: 78% on MATH test set
- INTEGRATION: HIGH — Upgrade self-QA gate to PRM scoring each step

### OmegaPRM (Google, June 2024) — arXiv:2406.06592
- Automated MCTS-based collection of process supervision data
- Divide-and-conquer MCTS identifies first error in CoT via binary search
- 1.5M annotations collected automatically (no human labels)
- Weighted self-consistency at inference (PRM-weighted voting)
- Results:
  - Gemini Pro: 51% → 69.4% on MATH500 (+18.4%)
  - Gemma2-27B: 42.3% → 58.2% on MATH500, 74.0% → 92.2% on GSM8K
- INTEGRATION: VERY HIGH — Auto-generate PRM training data via MCTS, use PRM for weighted selection

### V-STaR (Feb 2024) — arXiv:2402.06457
- Uses both correct AND incorrect self-generated solutions to train DPO-based verifier
- Iterative: better reasoner → better verifier → better reasoner
- Results: 4% to 17% test accuracy improvement on code generation and math
- INTEGRATION: YES — DPO-based verifier is simpler, leverages multi-model setup

### ConsistPRM — aayambansal/ConsistPRM (Feb 2026)
- Z3 SMT solver for ground-truth verification of logical reasoning
- Z3-verified labels critical for training consistency-aware PRMs

### PRM Integration for Timuclaude:
- Option A (Simple): LLM-as-verifier scores each step 0-1, add to self-QA gate
- Option B (Advanced): Train small PRM (1.5B) on OmegaPRM-style auto-generated data via DPO
- Option C (Hybrid): Code execution for math/code steps + LLM verifier for text reasoning
- At inference: weighted self-consistency (OmegaPRM pattern)
  score(solution) = sum(PRM(step_i)) / num_steps; select argmax over N solutions

---

## 3. CHAIN-OF-THOUGHT VARIANTS

### Tree of Thoughts (Princeton, May 2023) — arXiv:2305.10601
- Generalizes CoT to explore multiple reasoning paths as a tree
- LM generates "thoughts", self-evaluates, uses BFS/DFS to search
- Game of 24: GPT-4 CoT solves 4%, ToT achieves 74% (+70 pp)
- INTEGRATION: YES — Simpler than MCTS, good "easy" search mode

### Graph of Thoughts (Aug 2023) — arXiv:2308.09687
- Extends ToT to arbitrary graph structure (merge, refine, feedback loops)
- Sorting quality +62% over ToT, 31% cost reduction
- INTEGRATION: MEDIUM — For complex multi-step problems

### Self-Refine (March 2023) — arXiv:2303.17651
- Same LLM generates, critiques, refines iteratively (no training)
- ~20% absolute improvement across 7 diverse tasks
- INTEGRATION: ALREADY PARTIALLY IMPLEMENTED — extend to multi-round

### Reflexion (March 2023) — arXiv:2303.11366
- Verbal self-reflection stored in episodic memory
- 91% pass@1 on HumanEval (vs GPT-4's 80%)
- INTEGRATION: HIGH — Per-session reflection log, retry with reflection context

---

## 4. TEST-TIME COMPUTE SCALING

### "Scaling LLM Test-Time Compute Optimally" (Google DeepMind, Aug 2024) — arXiv:2408.03314
- Two mechanisms: Search against dense PRM, Adaptive response updating
- Compute-optimal strategy allocates compute adaptively per prompt difficulty
- 4x efficiency improvement over best-of-N baseline
- On problems where smaller model has some success, test-time compute outperforms 14x larger model
- INTEGRATION: CRITICAL — Adaptive: Easy→N=3 self-consistency, Medium→best-of-N+PRM, Hard→MCTS

### ATTS: Adaptive Test-Time Scaling — waelantar/ATTS_Complete_Free_Package
- 6-stage pipeline: difficulty estimation → mode selection → generation → USVA verification → escalation → refinement
- Pass@k sampling estimates difficulty d∈[1,10]
- d<4 → DIRECT (150 tokens), d<7 → THINKING (500 tokens), else → DEEP (1000 tokens)
- 28% token savings with only 2% accuracy cost
- INTEGRATION: EXCELLENT FIT — Fork and adapt this repo

### DeepSeek-R1 (Jan 2025) — arXiv:2501.12948
- Pure RL incentivizes reasoning — self-verification, backtracking emerge naturally
- Confirms verification + self-correction loops are the right architecture

### Collaborative Parallel Thinking (CPT)
- Branches share intermediate discoveries during MCTS search
- Better accuracy-latency Pareto frontier on HMMT/AIME
- INTEGRATION: Share discovered facts across search branches

### s1: Simple Test-Time Scaling — arXiv:2501.19393
- Budget forcing: append "Wait" to force more reasoning
- 1,000 samples fine-tuning achieves competitive results
- INTEGRATION: YES — Extremely simple (just append "Wait" token)

---

## 5. VERIFICATION & SELF-CHECKING

### Multi-Layer Verification Strategy for Timuclaude:
- Layer 1: Code execution (already implemented) — execute generated code, check output
- Layer 2: Step-level PRM verification — score each reasoning step 0-1, flag low-scoring steps
- Layer 3: Cross-model verification — Model A generates, Model B verifies (different families)
- Layer 4: Z3/SMT for logical verification — encode as SMT constraints, check satisfiability
- Layer 5: Reflexion memory — On failure, generate verbal reflection, store, retry

---

## 6. BEST-OF-N AND REJECTION SAMPLING

### Weighted Self-Consistency (OmegaPRM)
- Instead of uniform majority vote, weight each solution by PRM score
- answer = argmax_a Σ PRM(solution_i) * [answer_i == a]
- Gemini Pro MATH500: 51% → 69.4%
- INTEGRATION: HIGH — Simple modification to existing self-consistency

### Rejection Sampling with Difficulty Estimation (ATTS)
- Pass@k → difficulty estimate → adaptive N (easy: N=1, medium: N=5, hard: N=20+)
- 28% token savings, 2% accuracy cost
- INTEGRATION: HIGH — Fork waelantar/ATTS_Complete_Free_Package

---

## 7. REASONING WITH TOOLS

### Toolformer (Meta, Feb 2023) — arXiv:2302.04761
- LLMs self-train to use external tools (calculator, QA, search, translation, calendar)
- INTEGRATION: YES — Extend tool verification to calculator, search, code interpreter

### Code-Augmented CoT (rStar-Math)
- Each reasoning step includes executable code that verifies the step
- Key to rStar-Math's 90% on MATH
- INTEGRATION: HIGH — Extend from final-answer verification to per-step

---

## PRIORITY RECOMMENDATIONS FOR TIMUCLAUDE

### Tier 1: Immediate High-Impact (Low Effort)
1. PRM-Weighted Self-Consistency — replace majority vote with PRM-weighted vote (~50 LOC, +10-18% math)
2. Adaptive Compute Allocation (ATTS) — difficulty estimation → mode selection (~fork repo, 28% token savings)
3. Reflexion Memory — verbal reflection on failures, retry with context (~100 LOC, +10-20% hard problems)

### Tier 2: Medium Effort, High Impact
4. Step-Level Code Verification — extend tool verification to per-step (+15-30% math/code)
5. Tree of Thoughts for Medium Problems — BFS with self-evaluation (+70 pp on search-heavy)

### Tier 3: High Effort, Frontier-Level Impact
6. Full MCTS + PPM (rStar-Math architecture) — 500-1000 LOC, match o1-preview level
7. Collaborative Parallel Thinking — share discoveries across MCTS branches

### KEY REPOS TO REFERENCE
| Repo | Description |
|------|-------------|
| queelius/mcts-reasoning | MCTS for LLM with fluent API |
| billyvinning/langchain-mcts | MCTS-SR in LangGraph |
| xinzhel/lits-llm | Modular tree search + chain reasoning (ACL 2026) |
| waelantar/ATTS_Complete_Free_Package | Adaptive test-time scaling pipeline |
| ThreeSR/Awesome-Inference-Time-Scaling | 100+ paper list on TTC |
| NJUxlj/prm-reproduce | PRM reproduction |
| aayambansal/ConsistPRM | Z3-verified PRM training |
| Hritikd/hermes | TTC engine with PRM + MCTS |
| Saksham4796/momentum-guided-test-time-search | Momentum MCTS on GSM8K |