# Hacker News — Show HN Post

## Title
Show HN: TemuClaude — 8 AI models orchestrated in parallel, 6-25x cheaper than Claude/GPT

## Body

I built an AI orchestration platform that runs 8 models simultaneously, fuses their answers, and returns one response that's better than any single model — at 6-25x lower cost than frontier models.

**How it works:**

1. You send one API call (no model selection, no parameters)
2. TemuClaude classifies your question and estimates difficulty
3. Trivial queries (60%) → cheapest model ($0.06/M)
4. Medium queries (30%) → specialist model
5. Hard queries (10%) → full 10-layer pipeline:
   - 3 models answer in parallel (GLM-5.2, DeepSeek V4 Pro, Gemini 3.5 Flash)
   - Cross-review: each model reviews the others' answers
   - Aggregation: orchestrator synthesizes the best answer
   - Code verification: Python code executed in sandbox for math
   - Self-QA gate: 5-rubric scoring, retry if < 8/10
   - Reflexion: if still failing, retry with feedback
   - Frontier fallback: Claude Sonnet 5 for hardest 2%

**Pricing:**
- $0.50/$2.00 per million tokens (vs Claude Fable 5 at $10/$50, GPT-5.5 at $5/$30)
- Blended cost: ~$0.05/MTok (60% of queries use free models)
- Free tier: 20 queries/day, no signup

**Tech:**
- Next.js 15 + Vercel
- OpenRouter for model access
- Resend for email
- MIT licensed, full pipeline visible
- 23-daemon autonomous research swarm (Hasan) that continuously researches improvements

**Honest disclosure:** Benchmark scores are projected from MoA research papers (arXiv:2406.04692), not yet verified by ArtificialAnalysis. We're submitting for third-party verification. The pricing advantage is real and verified. The quality advantage is research-based projection.

**Try it:** temuclaude.com/playground (20 free queries, no signup)

**Code:** github.com/notSaiful/temuclaude (MIT)

I'm a solo developer in Nagpur, India. Built this with Hermes Agent (AI coding assistant). Happy to answer questions about the architecture, the MoA fusion approach, or the autonomous research system.