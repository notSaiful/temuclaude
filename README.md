# Temuclaude

> One question. Many minds. One superior answer. Frontier-level intelligence at 12x lower cost.

## What is Temuclaude?

Temuclaude is an AI orchestration platform that routes your queries to 8 AI models simultaneously, fuses their responses, verifies with code, and quality-checks with self-QA. The result: answers that beat frontier models (Fable 5, GPT-5.5, Gemini 3.1 Pro) at 12x lower cost.

## Live Demo

- **Website**: https://website-gamma-six-86.vercel.app
- **Playground**: https://website-gamma-six-86.vercel.app/playground
- **Pricing**: https://website-gamma-six-86.vercel.app/pricing
- **Models**: https://website-gamma-six-86.vercel.app/models
- **Docs**: https://website-gamma-six-86.vercel.app/docs
- **Benchmarks**: https://website-gamma-six-86.vercel.app/benchmarks

## Model Pool (8 models)

| Model | Role | IQ | Price ($/1M) |
|-------|------|-----|-------------|
| GLM-5.2 | Orchestrator | 51 | $0.58 / $2.19 |
| DeepSeek V4 Pro | Hard Reasoning | 44 | $2.72 / $10.88 |
| Hy3 Preview | Trivial Router | — | $0.063 / $0.21 |
| MiMo-V2.5 | Multimodal | 40 | $0.105 / $0.28 |
| Gemini 3 Flash | Legal/Health | 50 | $0.50 / $3.00 |
| MiniMax M3 | Vision + Creative | 44 | $2.04 / $8.16 |
| Claude Sonnet 5 | Frontier Fallback | 53 | $3.00 / $15.00 |
| Nemotron 3 Ultra | QA Gate (Free) | 38 | FREE |

## Pricing

| Plan | Price | Queries | API |
|------|-------|---------|-----|
| Free | $0 | 50/day | No |
| Pro | $29/mo | 5,000/mo | Yes |
| Pay-as-you-go | $2/$10 per 1M tokens | — | Yes |
| Enterprise | $499/mo | 200,000/mo | Yes (SSO, SLA) |

## vs Frontier Models

| Model | Input $/1M | Output $/1M | vs Temuclaude |
|-------|-----------|------------|-------------|
| Claude Fable 5 | $10.00 | $50.00 | 12x more expensive |
| GPT-5.5 | $5.00 | $30.00 | 7x more expensive |
| Fugu Ultra | $5.00 | $30.00 | 7x more expensive |
| Opus 4.8 | $5.00 | $25.00 | 6x more expensive |
| Gemini 3.1 Pro | $2.00 | $12.00 | 3x more expensive |
| **Temuclaude** | **$2.00** | **$10.00** | **—** |

## Architecture

```
User Query
    ↓
Classify (task type + difficulty)
    ↓
┌──────────────────────────────────────────┐
│  TRIVIAL (60%)  → Hy3 Preview (cheapest)  │
│  MEDIUM (25%)   → Specialist routing      │
│  HARD (13%)     → 10-layer fusion stack   │
│  FRONTIER (2%)  → Claude Sonnet 5 (IQ 53) │
└──────────────────────────────────────────┘
    ↓
10-Layer Stack (hard queries):
1. Web search (knowledge augmentation)
2. MoA 3-layer (propose → cross-review → aggregate)
3. Self-consistency (N samples, PRM-weighted voting)
4. Code verification (sandboxed execution)
5. USVA 4-rubric QA gate
6. Reflexion (retry with feedback)
7. s1 budget forcing (extend short responses)
8. Step-level code verification (rStar-Math)
9. Z3/SMT logical verification
10. Frontier fallback (Claude Sonnet 5 if QA < 0.75)
    ↓
Final Answer
```

## Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS, Framer Motion
- **Backend**: Next.js API Routes (Node.js runtime)
- **Database**: JSON file store (upgrading to Postgres)
- **Payments**: Razorpay (subscriptions, pay-as-you-go)
- **AI Models**: OpenRouter (8-model pool)
- **Hosting**: Vercel
- **CI/CD**: GitHub Actions

## Development

```bash
# Clone
git clone https://github.com/notSaiful/temuclaude-research.git
cd temuclaude-research/website

# Install
npm install

# Environment
cp .env.example .env
# Add your Razorpay and OpenRouter keys to .env

# Run dev server
node node_modules/.bin/next dev -p 3001

# Build
npx next build
```

## Project Structure

```
temuclaude/
├── website/                 # Next.js app (production)
│   ├── app/
│   │   ├── api/             # API routes (payments, usage, keys, chat)
│   │   ├── pricing/         # Pricing page
│   │   ├── playground/      # Playground with usage tracking
│   │   ├── models/          # 8-model pool display
│   │   ├── terms/            # Terms of Service
│   │   ├── privacy/          # Privacy Policy
│   │   └── refunds/          # Refund Policy
│   ├── lib/                 # Shared code (plans, db, razorpay)
│   └── components/          # React components
├── src/                     # Python orchestrator (core engine)
├── benchmarks/              # Benchmark framework
├── tests/                   # Test suites
└── research/                # Research swarm
```

## Status

- **Phase 1-5**: Complete (Python orchestrator, 16 techniques, 84+ tests)
- **Phase 6**: In progress (website, payments, launch)
- **Live**: https://website-gamma-six-86.vercel.app
- **Build**: Passing
- **CI/CD**: GitHub Actions → Vercel

## Author

Mohammad Saiful Haque (Ggs) — built with Hermes Agent. One developer in Nagpur, India, proving that orchestrated models beat any single model at a fraction of the cost.

## License

All Rights Reserved © 2026 Temuclaude