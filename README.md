# TemuClaude

> One question. Step-aware model routing. One superior answer.

Frontier-quality AI at a fraction of the cost. TemuClaude orchestrates a role-specialized model pool, routes each task and high-value reasoning step to the best available model, verifies math/code with execution, and self-checks hard responses. You get one answer with budget-aware orchestration metadata and a shadow active-budget controller that learns when to continue, verify, debate, stop, or escalate.

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

## Use with Hermes Agent

Configure Hermes with the OpenAI-compatible endpoint `https://temuclaude.com/v1`
and model `temuclaude`. This is the bounded agent route: it uses two
complementary specialists, synthesis when both finish, and a rescue response
when an upstream role is unavailable. For work that needs the full
maximum-quality pipeline, submit an asynchronous job with
`execution: "maximum_quality"` instead of holding one agent turn open.

## Updated Model Stack + Step Router

TemuClaude uses eight active *roles*, not an always-on eight-model ensemble.
The router begins on the least-expensive model expected to succeed and only
adds specialists after uncertainty, verifier failure, or a clear modality need.

| Model | Role | Route policy |
|-------|------|--------------|
| DeepSeek V4 Flash | High-volume worker | Default for simple drafting, extraction, and low-risk steps |
| DeepSeek V4 Pro | Reasoning specialist | Math, technical analysis, and difficult code reasoning |
| GLM-5.2 | Planner + aggregator | Long-horizon planning, orchestration, and synthesis |
| MiniMax M3 | Budget multimodal | Image/video, UI, and long-context work |
| Gemini 3.5 Flash | Premium multimodal | Only when its tools/UI-control capability has expected value |
| GPT-5.6 Luna | Closed-model escalation | Only after a hard response fails the QA gate |
| Grok 4.5 | Coding-agent escalation | Targeted repair for difficult coding-agent work |
| Nemotron 3 Ultra | Independent verifier | Conditional QA and verification, never an always-on panel member |

GPT-5.6 Terra is a disabled emergency fallback. It needs both approved API
access and `TEMUCLAUDE_ENABLE_TERRA_FALLBACK=true`; GPT-5.6 Sol is excluded.
Kimi K2.6 and legacy models remain compatibility fallbacks while they are
evaluated against this stack.

Runtime selection is no longer only whole-query routing. TemuClaude records per-step telemetry for search, verification, consistency, QA gates, debate, post-processing, and formal verification, then uses observed success/cost/progress signals to recommend better step-level model choices when enough evidence exists.

The active budget controller now runs in shadow mode. It records recommended actions (`continue`, `verify`, `debate`, `stop`, `escalate`, `cheap_draft`) alongside cost risk and PRM/verifier state, but runtime gates stay disabled until the benchmark-promotion gate proves quality non-regression and cost savings.

## Pricing

| Plan | Price | Monthly Credits | API |
|------|-------|-----------------|-----|
| Free | $0 | 50K credits (20 queries/day) | Playground |
| Developer | $19/mo | 5M credits | Yes |
| Pro | $49/mo | 25M credits | Yes |
| Max | $149/mo | 100M credits | Yes |
| Enterprise | From $499/mo | 300M credits + contract overages | Yes (SSO, SLA) |

Credits are route-weighted for margin safety: trivial 1x, standard 1.5x, hard multi-model orchestration 4x, frontier fallback 15x, and deep research / long agentic work up to 20x.

## TemuClaude Lite

The Playground exposes two server-validated product profiles. **TemuClaude Pro**
keeps the full step-aware, premium-capable orchestration policy. **TemuClaude
Lite** uses the same task classification, answer trace, safety gates, and
authenticated usage controls with a stricter cost boundary:

| Lite role | Model | Route policy |
|---|---|---|
| Default worker | DeepSeek V4 Flash | Routine queries and first-pass drafting |
| Hard reasoning | Qwen 3.7 Plus | Math, structured reasoning, and agentic work |
| Multimodal / agent specialist | Qwen 3.7 Plus | Long-context, UI, vision, coding, and agent tasks |
| Independent critic | Nemotron 3 Ultra | High-risk, explicit-verification, or 2% hard-task audit sample only |

Lite is a cost-bounded cascade, not a four-model ensemble. It makes one
primary call, permits one same-profile availability fallback, and allows a
single verifier/corrective pass only when the risk gate fires. The target mix
projects about **$0.113/M input** and **$0.371/M output** before provider
discounts, caching, and prompt-token variation. It must not be marketed as a
universal replacement for frontier systems; its quality/cost claim is subject
to the same benchmark-promotion gate as Pro.

## Cost and Frontier Evaluation

| Model | Input $/1M | Output $/1M | vs TemuClaude |
|-------|-----------|------------|-------------|
| Claude Fable 5 | $10.00 | $50.00 | Peak single-model reference |
| GPT-5.6 Luna | $1.00 | $6.00 | General escalation candidate |
| Grok 4.5 | $2.00 | $6.00 | Coding-agent escalation candidate |
| Gemini 3.5 Flash | $1.50 | $9.00 | Premium multimodal candidate |
| GLM-5.2 | $0.54 | $1.76 | Open planning/synthesis route |
| DeepSeek V4 Flash | $0.09 | $0.18 | High-volume worker route |

Public API prices are not a blended TemuClaude cost. Production promotion is
blocked until shadow telemetry shows quality, cost, latency, and reliability
meet the benchmark-promotion gate. TemuClaude does not claim to outperform
Fable 5 until that evaluation has passed.

## Architecture

```
User Query
    ↓
Classify (task type + difficulty)
    ↓
Step-Aware Model Router
    ↓
Shadow Active Budget Controller
    ↓
┌──────────────────────────────────────────┐
│  SIMPLE          → DeepSeek V4 Flash     │
│  SPECIALIST      → DeepSeek Pro / GLM / M3│
│  PREMIUM         → Gemini / Grok / Luna  │
│  EMERGENCY       → Terra (explicit opt-in)│
└──────────────────────────────────────────┘
    ↓
10-Layer Stack (hard queries):
1. Web search (knowledge augmentation)
2. MoA panel + aggregate (third review layer only in max-quality mode)
3. Self-consistency (N samples, PRM-weighted voting)
4. Code verification (sandboxed execution)
5. USVA 5-rubric QA gate
6. Reflexion (retry with feedback)
7. s1 budget forcing (extend short responses)
8. Step-level code verification (rStar-Math)
9. Z3/SMT logical verification
10. Luna escalation after failed QA; Terra only as an explicit emergency fallback
    ↓
Final Answer + Budget/Progress/Failure/Controller Telemetry
```

## Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **Backend**: Next.js API Routes (Node.js runtime)
- **AI Models**: Open-model core plus credential-gated direct specialist routes
- **Email**: Hostinger/Titan SMTP or Resend fallback, plus app OTP and inbound email webhook support
- **Payments**: Manual paid-plan activation now; hosted checkout integration is feature-flagged for later rollout
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
- **Models**: eight active routing roles; premium routes are shadow/promotion-gated
- **Legal**: Terms, Privacy, Refunds all live
- **Email**: OTP, support, welcome, billing, security, marketing, and inbound webhook mail via configurable provider
- **Build**: Passing
- **Tests**: 472+ passing

## Author

Mohammad Saiful Haque — built with Hermes Agent. One developer in Nagpur, India, building measured orchestration that earns quality/cost claims through evaluation. 25% of profit goes to charity.

## License

MIT Licensed — see [LICENSE](LICENSE)
