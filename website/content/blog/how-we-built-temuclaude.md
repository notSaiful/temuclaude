# How We Built an AI That Targets Fable 5 Quality at Lower Cost

*July 2026 · Mohammad Saiful Haque*

## The Problem

Fable 5 is expensive at $10/$50 per million tokens. For developers building AI-powered products, those prices add up fast — a single complex query can cost dollars, and a day of development can burn through hundreds.

We asked a simple question: **what if you didn't have to choose between quality and cost?**

## The Idea

Instead of using one expensive model, what if you used 8 models together — each with a specific role — and fused their answers into something better than any single model could produce?

This is called **Mixture of Agents (MoA)**, and it's backed by research (arXiv:2406.04692) showing that 3-layer fusion improves AlpacaEval performance. We took this concept and built an adaptive pipeline around it — up to 10 layers for hard queries, a fast path for simple ones.

## The Architecture

When you ask TemuClaude a question, here's what happens:

1. **Classification** — Your query is categorized (math, coding, reasoning, knowledge, etc.) and difficulty is estimated (trivial, medium, hard).

2. **Routing** — Trivial queries route to an efficient model (e.g. DeepSeek V4 Flash). Medium ones route to the best specialist. Only genuinely hard ones trigger the full fusion pipeline.

3. **3-Layer MoA Fusion** (for hard queries):
   - **Layer 1**: GLM-5.2, DeepSeek V4 Pro, and Gemini 3.5 Flash each answer independently
   - **Layer 2**: Each model reviews the others' answers and refines its own
   - **Layer 3**: GLM-5.2 synthesizes all refined answers into one

4. **Code Verification** — For math questions, an independent verifier model (Nemotron 3 Ultra) checks the draft. Our Python research engine additionally runs generated Python in a sandbox and checks it with a Z3/SMT solver for hard queries; the live gateway uses the verifier-model QA gate.

5. **Self-QA Gate** — Every answer is scored on 5 rubrics (logical coherence, factual correctness, completeness, goal alignment, clarity). If it scores below 8/10, TemuClaude retries with reflexion feedback.

6. **Frontier Fallback** — For the hardest queries where all layers fail, the strongest available fallback is called as a safety net.

## The Models

| Model | Role | IQ | Cost ($/1M) |
|-------|------|-----|------------|
| GLM-5.2 | Orchestrator | 51 | $0.91 / $2.86 |
| DeepSeek Pro | Reasoning | 44 | $0.18 / $0.18 |
| Llama 3.3 | Cheap router | 40 | $0.06 / $0.10 |
| Gemini 2.0 Flash | Utility / RAG | 40 | $0.075 / $0.30 |
| Mistral Large 2 | Logic Specialist | 43 | $2.00 / $6.00 |
| Frontier fallback | Safety net | 53 | Provider-dependent |
| MiMo-V2.5 | Multimodal | 40 | $0.06 |
| Z3 Solver | Logical Verifier | — | Local |

The key insight: Arithmetic and coding answers are checked by an independent verifier model. SymPy execution and Z3/SMT solvers run in the Python research runtime for hard Pro queries, not the live gateway. And most queries route to efficient models, making the blended cost far below Fable 5 direct.

## The Results

### Pricing (verified)

| Model | Input $/1M | Output $/1M | vs TemuClaude |
|-------|-----------|------------|-------------|
| Fable 5 direct | $10.00 | $50.00 | Up to 53x more |
| **TemuClaude blended** | **~$0.94** | **~$0.94** | **—** |

### Intelligence

Our benchmark scores are projected from research analysis of MoA stacking effects. We are transparent about this — these are not yet verified by ArtificialAnalysis. We plan to submit for third-party verification soon.

What the research shows: 3-layer MoA fusion (arXiv:2406.04692) reports gains over single models on benchmarks like AlpacaEval, which is why we adopt the pattern. Code verification and self-QA with reflexion are designed to reduce math hallucination and improve hard-problem answers. We have not yet measured our own end-to-end scores, and we will publish verified results rather than claim specific percentages.

## What This Means

For developers: you get one API endpoint, no model selection, Fable 5-level ambition at much lower direct token cost. The orchestration is invisible — you just ask a question and get an answer.

For the community: 25% of every payment goes to charity — food relief, community kitchens, medical clinics, and education programs. Your queries help people.

## Try It

- **Playground** (free, 20 queries/day after sign-in): [temuclaude.com/playground](https://temuclaude.com/playground)
- **API docs**: [temuclaude.com/docs](https://temuclaude.com/docs)
- **GitHub** (MIT licensed): [github.com/notSaiful/temuclaude](https://github.com/notSaiful/temuclaude)

---

*Built by one developer in Nagpur, India, using Hermes Agent. MIT licensed. 25% of profit to charity.*
