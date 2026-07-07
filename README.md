# TemuClaude

> One question. Eight minds. One superior answer.

Frontier-quality AI at a fraction of the cost. TemuClaude orchestrates 8 AI models in parallel, fuses their best answers, verifies math with code execution, and self-checks every response. You get one answer — smarter than any single model, at 6-25x lower cost.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Website](https://img.shields.io/website?url=https://temuclaude.com)](https://temuclaude.com)
[![GitHub stars](https://img.shields.io/github/stars/notSaiful/temuclaude)](https://github.com/notSaiful/temuclaude)

## Live

- **Website**: https://temuclaude.com
- **Playground**: https://temuclaude.com/playground
- **Pricing**: https://temuclaude.com/pricing
- **Docs**: https://temuclaude.com/docs
- **Benchmarks**: https://temuclaude.com/benchmarks
- **Models**: https://temuclaude.com/models

## Model Pool (8 models)

| Model | Role | IQ | Context |
|-------|------|-----|---------|
| GLM-5.2 | Orchestrator + Aggregator | 51 | 1M |
| DeepSeek V4 Pro | Hard Reasoning + Math | 44 | 1M |
| Hy3 Preview | Trivial Router (cheapest) | — | 262K |
| Gemini 3 Flash | Legal + Health | 50 | 1M |
| MiniMax M3 | Vision + Creative | 44 | 1M |
| MiMo-V2.5 | Multimodal | 40 | 1M |
| Claude Sonnet 5 | Frontier Fallback (2%) | 53 | 1M |
| Nemotron 3 Ultra | QA Gate (FREE) | 38 | 128K |

## Pricing

| Plan | Price | Queries | API |
|------|-------|---------|-----|
| Free | $0 | 20/day | Playground |
| Developer | $15/mo | 50,000/mo | Yes |
| Pro | $49/mo | 500,000/mo | Yes |
| Pay-as-you-go | $0.50/$2.00 per 1M tokens | — | Yes |
| Enterprise | $499/mo | Unlimited | Yes (SSO, SLA) |

## vs Frontier Models

| Model | Input $/1M | Output $/1M | vs TemuClaude |
|-------|-----------|------------|-------------|
| Claude Fable 5 | $10.00 | $50.00 | 20-25x more |
| GPT-5.5 | $5.00 | $30.00 | 10-15x more |
| Claude Sonnet 5 | $3.00 | $15.00 | 6-7.5x more |
| Gemini 3.5 Flash | $1.50 | $9.00 | 3-4.5x more |
| GLM-5.2 | $1.40 | $4.40 | 2.2-2.8x more |
| **TemuClaude** | **$0.50** | **$2.00** | **—** |

Blended cost: ~$0.05/MTok (60% free models + 30% cheap + 10% premium).

## Architecture

```
User Query
    ↓
Classify (task type + difficulty)
    ↓
┌──────────────────────────────────────────┐
│  TRIVIAL (60%)  → Hy3 Preview (cheapest) │
│  MEDIUM (30%)   → Specialist routing     │
│  HARD (10%)     → 10-layer fusion stack  │
│  FRONTIER (2%)  → Claude Sonnet 5        │
└──────────────────────────────────────────┘
    ↓
10-Layer Stack (hard queries):
1. Web search (knowledge augmentation)
2. MoA 3-layer (propose → cross-review → aggregate)
3. Self-consistency (N samples, PRM-weighted voting)
4. Code verification (sandboxed execution)
5. USVA 5-rubric QA gate
6. Reflexion (retry with feedback)
7. s1 budget forcing (extend short responses)
8. Step-level code verification (rStar-Math)
9. Z3/SMT logical verification
10. Frontier fallback (Claude Sonnet 5 if QA < 0.75)
    ↓
Final Answer + Full Orchestration Metadata
```

## Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **Backend**: Next.js API Routes (Node.js runtime)
- **AI Models**: OpenRouter (8-model pool)
- **Email**: Resend (automated transactional + marketing)
- **Payments**: Razorpay (subscriptions, pay-as-you-go)
- **Hosting**: Vercel (Mumbai region)
- **Autonomous System**: Hasan (23-daemon research swarm)

## Development

```bash
# Clone
git clone https://github.com/notSaiful/temuclaude.git
cd temuclaude/website

# Install
npm install

# Environment
cp .env.example .env
# Add OPENROUTER_API_KEY and RESEND_API_KEY to .env

# Run dev server
npm run dev

# Build
npm run build
```

## Project Structure

```
temuclaude/
├── website/                 # Next.js app (production)
│   ├── app/
│   │   ├── api/             # API routes (chat, email, payments, usage)
│   │   ├── pricing/         # Pricing page
│   │   ├── playground/      # Playground with usage tracking
│   │   ├── models/          # 8-model pool display
│   │   ├── docs/            # Full documentation
│   │   ├── benchmarks/      # Benchmark results
│   │   ├── terms/           # Terms of Service
│   │   ├── privacy/         # Privacy Policy
│   │   └── refunds/         # Refund Policy
│   ├── lib/                 # Shared code (email, plans, db)
│   └── components/          # React components
├── src/                     # Python orchestrator (core engine)
├── benchmarks/              # Benchmark framework
├── tests/                   # Test suites
└── research/                # Hasan autonomous research swarm
```

## Status

- **Website**: Live at temuclaude.com
- **Models**: 8 models deployed via OpenRouter
- **Legal**: Terms, Privacy, Refunds all live
- **Email**: 8 automated email types via Resend
- **Build**: Passing
- **Tests**: 472+ passing

## Author

Mohammad Saiful Haque — built with Hermes Agent. One developer in Nagpur, India, proving that orchestrated models beat any single model at a fraction of the cost. 25% of profit goes to charity.

## License

MIT Licensed — see [LICENSE](LICENSE)