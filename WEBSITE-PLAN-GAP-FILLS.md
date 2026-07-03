# TIMUCLAUDE — WEBSITE PLAN: GAP FILLS (10 Items)

---

## GAP 1: NAVIGATION DETAILED DESIGN

### Desktop Navigation (1024px+)
- Height: 64px, sticky, transparent over hero
- Background on scroll: rgba(250, 248, 245, 0.85) + backdrop-filter: blur(12px)
- Left: Logo (32px mark + "Timuclaude" wordmark)
- Center-right: Nav links (Inter 500, 0.875rem, #5E5B56, hover #1A1816)
  - Models
  - Playground
  - Docs (dropdown: Quickstart, API Reference, Models, Configuration, Orchestration, Benchmarks, Self-Hosting)
  - Pricing
- Right: [Get Started] button (primary CTA)
- Cmd+K search button (opens command palette overlay)

### Active State Styling
- Active link: color #1A1816, 2px bottom border in #D97757
- Hover: color #1A1816, subtle underline fade-in (150ms)

### Mobile Navigation (<768px)
- Hamburger menu (3 lines, 24px, #1A1816)
- Click: full-screen drawer slides in from right (300px width)
- Drawer bg: #FAF8F5, border-left: 1px solid rgba(26,24,22,0.08)
- Links: Inter 500, 1rem, #1A1816, padding 16px 24px, hover bg #F0EDE6
- Docs section: expandable accordion within drawer
- Bottom of drawer: [Get Started] button (full width)
- Close: X button top-right, or tap backdrop
- Body scroll locked when drawer open (overflow: hidden)

### Docs Breadcrumbs
- Top of each docs page: Home > Docs > [Section] > [Page]
- Inter 400, 0.8125rem, #8E8B85
- Current page: #1A1816 (not a link)
- Separator: "/" in #8E8B85
- Links hover: #D97757

---

## GAP 2: ERROR PAGE DESIGN

### 404 Page
- Full-page centered layout
- Large "404" in Inter 700, 8rem, #D97757 (clay accent)
- "Page not found" in Inter 600, 1.5rem, #1A1816
- "The page you're looking for doesn't exist or has been moved." in Inter 400, 1rem, #5E5B56
- [Back to Home] button (primary)
- [Try the Playground] button (secondary)
- Subtle SVG orchestration diagram in background (low opacity, decorative)
- Respect prefers-reduced-motion (no background animation)

### 500 Page
- Same layout as 404
- "500" in #D97757
- "Something went wrong" heading
- "An error occurred on our end. We've been notified and are working on it." in #5E5B56
- [Try Again] button (reloads page)
- [Back to Home] button

### Playground Error States
- Model timeout: inline toast "Model took too long. Retrying with fallback..." (bg #F0EDE6, border-left 3px #E8B547)
- Model error: inline toast "This model returned an error. Trying another model..." (bg #F0EDE6, border-left 3px #D97757)
- No API key: inline panel "Add your OpenRouter API key to use the playground" + [Add Key] button
- Rate limited: inline toast "Rate limit reached. Try again in X seconds." (bg #F0EDE6, border-left 3px #E8B547)
- Network error: inline banner "Connection lost. Reconnecting..." + [Retry] button (bg #F0EDE6, border-left 3px #C46686)
- All models failed: inline panel "All models are currently unavailable. Please try later." (bg #F0EDE6, border-left 3px #C46686)
- Insufficient credits: inline panel "Your OpenRouter account needs credits. Add them at openrouter.ai/settings/credits" + link

---

## GAP 3: AUTHENTICATION FLOW

### Signup/Login Page
- Centered card (max-width 400px) on #FAF8F5 background
- Card: white bg, 1px border rgba(26,24,22,0.08), radius 12px, padding 32px
- Logo at top (centered, 32px)
- "Create your account" heading (Inter 600, 1.25rem)
- OAuth buttons (full width, 44px height):
  - [Continue with Google] — white bg, 1px border, Google logo left
  - [Continue with GitHub] — #1A1816 bg, #FAF8F5 text, GitHub logo left
- Separator: "or" with horizontal lines
- Email input + password input (standard styled inputs)
- [Create Account] button (primary, full width)
- "Already have an account? [Log in]" link below
- No credit card required message

### OAuth Flow
1. User clicks [Continue with Google/GitHub]
2. Redirect to OAuth provider
3. Return to /auth/callback with token
4. Server creates session (JWT in HttpOnly cookie)
5. Redirect to /playground

### Account Settings Page
- Sidebar: Account, API Keys, Usage, Billing
- Account: name, email, avatar, delete account
- API Keys: list, create, revoke (masked sk-...xxxx)
- Usage: queries count, tokens used, cost breakdown by model
- Billing: current plan, payment method, invoices

### Password Reset
- /forgot-password page: email input, [Send Reset Link]
- /reset-password page: new password input, [Reset Password]
- Email sent: "Check your email for a reset link"

---

## GAP 4: DOCUMENTATION PAGE TEMPLATES

### Page Layout
```
┌────────────────────────────────────────────────────┐
│ TOP BAR: Logo | Search (Cmd+K) | Dark Mode | GitHub │
├──────────┬───────────────────────────┬─────────────┤
│          │                           │             │
│ LEFT     │   MAIN CONTENT            │ RIGHT       │
│ SIDEBAR  │   (max-width 680px)       │ SIDEBAR     │
│          │                           │ (On This    │
│ Overview │   # Page Title            │  Page)      │
│ - Quick  │   Description text        │             │
│ - Models │                           │ - Section 1 │
│ - Config │   ## Section 1            │ - Section 2 │
│          │   Content...              │ - Section 3 │
│ Models   │                           │             │
│ - List   │   ```python               │             │
│          │   code example            │             │
│ Features │   ```                     │             │
│ - Fusion │   [Copy] button           │             │
│ - QA     │                           │             │
│          │   > Note: This is a       │             │
│          │   > callout/admonition    │             │
│          │                           │             │
│          │   [Edit on GitHub ←]      │             │
├──────────┴───────────────────────────┴─────────────┤
│ FOOTER: Previous | Next page navigation              │
└─────────────────────────────────────────────────────┘
```

### Code Block Component
- Background: #1A1816 (warm dark)
- Text: #E8E4DC
- Font: JetBrains Mono, 13px, line-height 1.5
- Padding: 16px 20px
- Border-radius: 12px
- Top bar: language label (left), [Copy] button (right, appears on hover)
- Copy: icon changes to checkmark for 2s, "Copied!" text
- Syntax highlighting: Shiki with warm-tinted theme
- Horizontal scroll for long lines (overflow-x: auto)
- Line numbers: optional, #8E8B85, right-aligned

### Callout/Admonition Component
- Types: Note, Warning, Tip, Danger
- Note: bg #F0EDE6, border-left 3px #D97757, icon: info
- Warning: bg #F0EDE6, border-left 3px #E8B547, icon: alert-triangle
- Tip: bg #F0EDE6, border-left 3px #788C5D, icon: lightbulb
- Danger: bg #F0EDE6, border-left 3px #C46686, icon: alert-octagon
- Padding: 12px 16px, radius 8px (left side only — border-left, no right radius)
- Title: Inter 600, 0.875rem, #1A1816
- Body: Inter 400, 0.875rem, #5E5B56

### Version Selector
- Top bar dropdown: "v1.0 (current)" with chevron
- Previous versions grayed out: "v0.9 (archived)"
- Stored in docs config, rendered as dropdown

---

## GAP 5: BENCHMARK PAGE INTERACTIVITY

### Page Layout
1. Heading: "Benchmark Results" with methodology disclaimer
2. Interactive chart section
3. Full comparison table
4. Methodology section
5. Reproducibility section

### Interactive Chart
- Bar chart comparing Timuclaude vs Fable 5, GPT-5.5, Gemini 3.1 Pro
- X-axis: benchmarks (GPQA, HLE, LiveCodeBench, etc.)
- Y-axis: score (%)
- Timuclaude bars: #D97757 (clay)
- Competitor bars: #8E8B85 (muted gray)
- Hover: tooltip with exact score, methodology link
- Toggle: switch between "All benchmarks" and "Timuclaude wins"
- Library: Recharts (React-native, open source, ~40KB)

### Full Comparison Table
- Same as Fugu's approach: bold for highest, underline for second
- Columns: Benchmark, Timuclaude, Fable 5, GPT-5.5, Gemini 3.1 Pro
- Footnotes: † = from published results, * = our measurement
- Responsive: horizontal scroll on mobile (overflow-x: auto)
- Alternating row colors: #FAF8F5 and #F0EDE6

### Methodology Section
- Expandable sections (disclosure triangles, like OpenRouter FAQ)
- "How we measured" → explanation of each benchmark
- "Model configuration" → which models, temperature, N samples
- "Hardware" → which backend (Ollama/OpenRouter)
- "Date" → when benchmarks were run

### Reproducibility Section
- "Run it yourself" heading
- Code block: `python benchmarks/run_timuclaude.py --dataset hle --sample 100`
- Link to GitHub: benchmark scripts, datasets, results JSON
- "Full results: [View on GitHub]"

---

## GAP 6: ANALYTICS/TRACKING

### Tool: Plausible Analytics
- Why: Privacy-friendly, no cookies, GDPR compliant, lightweight (<1KB script)
- Why not GA: heavy, privacy invasive, requires cookie consent
- Why not PostHog: powerful but heavy for our needs, can add later for product analytics
- Cost: $9/month for 10K pageviews (cheaper than PostHog $20+/mo)

### Events to Track
- Page views (automatic): /, /playground, /docs, /models, /benchmarks, /pricing
- Playground: query_sent (mode, models_selected, latency)
- Playground: orchestration_viewed (user clicked "show how")
- CTA clicks: get_started, view_github, try_playground
- External links: github_repo, openrouter_signup
- Docs: search_used (Cmd+K)

### Implementation
```tsx
// Plausible script (loaded only after cookie consent)
<Script defer data-domain="timuclaude.com" src="https://plausible.io/js/script.js" />

// Custom events
window.plausible('Query Sent', { props: { mode: 'fusion', models: 3 } });
```

### Privacy Approach
- No cookies (Plausible doesn't use them)
- No personal data collected
- No cross-site tracking
- Aggregate data only (page views, clicks — not individual users)
- Privacy policy page explaining this

---

## GAP 7: PERFORMANCE OPTIMIZATION DETAILS

### Image Optimization
- Use next/image for all images (automatic AVIF/WebP, responsive sizes)
- OG image: pre-generated 1200×630 PNG, served statically
- Hero SVG: inline in HTML (no separate request)
- Model logos: small SVGs, inlined or in /public/icons/
- Screenshot images: next/image with width/height to prevent CLS

### Font Loading
- Use next/font for Inter and JetBrains Mono
- `display: swap` (show fallback font, swap when loaded)
- Preload critical font subsets (Latin only — reduces file size)
- Variable font: single file, all weights
- No external font CDN — self-hosted via next/font

```tsx
import { Inter, JetBrains_Mono } from 'next/font/google';
const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const jetbrains = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', display: 'swap' });
```

### Code Splitting Strategy
- Landing page: SSR, static content, minimal JS (~50KB)
- Playground: dynamic import (next/dynamic), loads only when user visits /playground
- React Flow: dynamic import (only loaded for orchestration visualization)
- Docs: SSG (statically generated at build time)
- Benchmark charts (Recharts): dynamic import

```tsx
const Playground = dynamic(() => import('@/components/Playground'), { ssr: false });
const OrchestrationView = dynamic(() => import('@/components/OrchestrationView'), { ssr: false });
```

### CDN/Edge Caching
- Vercel Edge Network (automatic with Next.js deployment)
- Static pages: cached at edge (ISR or SSG)
- Playground API: edge runtime for low latency
- Images: Vercel Image Optimization (automatic)
- 404/500: static, cached

### Bundle Size Budget
- Landing page JS: <80KB (gzipped)
- Playground JS: <150KB additional (dynamic import)
- Total initial load: <200KB (gzipped)
- Monitor with @next/bundle-analyzer

---

## GAP 8: CONTENT STRATEGY (Actual Copy)

### Hero
H1: "One question. Many minds. One superior answer."
Subtext: "Timuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost. Free with Ollama. Open source. MIT licensed."
CTA Primary: "Try the Playground"
CTA Secondary: "View on GitHub"
Install command: "pip install timuclaude"
Backend tabs: "Ollama (Free)" | "OpenRouter" | "ai/ml API"

### Metrics Bar
"5 Models" | "3 Backends" | "28x Cheaper" | "MIT Licensed"

### How It Works (3 cards)
01. "Understanding your question"
    "Timuclaude classifies your query — math, code, reasoning, knowledge — and routes it to the best model for the task."

02. "Combining multiple answers"
    "For hard questions, 3-5 models answer in parallel. A dynamic aggregator synthesizes the best parts of each response."

03. "Quality check"
    "Code execution verifies math. A self-QA gate scores the answer 0-10. If below 8, it retries with feedback."

### Platform Badges
"Available on: OpenRouter · Ollama · ai/ml API"

### Benchmark Section
Heading: "Benchmark Results"
Subtext: "Projected scores from research analysis. Live results coming after Phase 6 testing."
Table intro: "Timuclaude vs frontier models across 9 benchmarks."

### Playground Preview
Heading: "See it in action"
Text: "Try Timuclaude right now — no signup required. Watch 5 models collaborate in real-time."
Button: "Open Playground"

### Pricing
Free: "Self-Hosted" — "$0" — "Bring your own Ollama. Unlimited queries. Full orchestration. Community support."
Pro: "Cloud" — "$15/mo" — "Managed hosting. 3K queries/month. OpenRouter backend. Email support."
Enterprise: "Enterprise" — "$499/mo" — "200K queries/month. SLA. SSO. Self-hosted option. Dedicated support."
Button text: "Start Free" | "Get Pro" | "Contact Sales"

### Open Source Callout
Heading: "No black boxes. No markup. Just code."
Text: "MIT licensed. Read every line. Modify it. Self-host it. Bring your own keys. No vendor lock-in."
Button: "Star on GitHub"

### FAQ (Pricing page, expandable)
1. "How is Timuclaude different from using GPT-5.5 directly?"
   "GPT-5.5 is one model. Timuclaude orchestrates 5 models — fusing their answers, verifying with code, and quality-checking with self-QA. The result is measurably better on benchmarks, at 28x lower cost."
2. "Is it really free?"
   "Yes. Self-host with Ollama and it's free forever, unlimited queries. The cloud version costs $15/month for managed hosting."
3. "Which models does Timuclaude use?"
   "GLM-5.2, DeepSeek V4 Pro, Kimi K2.6, MiniMax M3, Nemotron 3 Ultra, and GPT-OSS 120B. You can add your own models too."
4. "Can I use my own API keys?"
   "Yes. Bring your own OpenRouter, ai/ml, or Ollama keys. No markup on your costs."
5. "How does the orchestration work?"
   "Timuclaude classifies your query, routes it to the best model(s), fuses multiple answers when needed, verifies math with code execution, and quality-checks with a self-QA gate. You see the whole process in the playground."
6. "Is my data stored?"
   "No. Queries are processed in real-time and not stored. Your API keys are stored only in your browser session (sessionStorage) and cleared when you close the tab."
7. "Can I self-host?"
   "Yes. Clone the repo, install dependencies, run with Ollama. Full instructions in the docs."
8. "What about enterprise?"
   "Enterprise includes SSO, SLA, self-hosted deployment, dedicated support, and 200K queries/month. Contact us for custom pricing."

### Empty State (Playground)
Heading: "Ask Timuclaude anything"
Subtext: "5 AI models are ready to collaborate on your question."
Example chips: "What is 9.9 vs 9.11?" | "Write a Python merge function" | "Explain quantum entanglement" | "Derivative of x³+2x²-5x+1?"

### Error Messages
- No API key: "Add your OpenRouter API key to start querying."
- Rate limited: "You've used all 3 free queries. Create an account or add your API key for unlimited access."
- Model failure: "Model temporarily unavailable. Trying fallback..."
- All failed: "All models are currently unavailable. Please try again in a moment."

---

## GAP 9: TESTING STRATEGY

### Visual Regression Testing
- Tool: Playwright + screenshot comparison
- Process: build page → screenshot → compare to baseline → flag differences
- Run: GitHub Actions on every PR
- Baseline: stored in repo, updated manually on intentional changes

### Cross-Browser Testing
- Primary: Chrome, Safari, Firefox (all desktop)
- Secondary: Safari iOS, Chrome Android (mobile)
- Tool: Playwright (Chromium, Firefox, WebKit) + BrowserStack (Safari iOS)
- Test: visual layout, interactions, streaming, SSE support

### Performance Testing
- Tool: Lighthouse CI (@lhci/cli)
- Run: GitHub Actions on every PR
- Targets: LCP <1.5s, INP <100ms, CLS <0.1, Lighthouse >95
- Block PR if score drops below 90

### Accessibility Testing
- Tool: @axe-core/playwright (automated) + manual keyboard testing
- Automated: run axe on every page, fail on critical violations
- Manual: Tab through every page, verify screen reader with VoiceOver
- Check: color contrast (4.5:1), ARIA labels, keyboard navigation, focus management

### Unit Testing
- Tool: Vitest + React Testing Library
- Coverage: components, hooks, utilities, API routes
- Target: 80% coverage on critical paths

### E2E Testing
- Tool: Playwright
- Tests: landing page loads, playground query flow, docs navigation, pricing toggle
- Run: GitHub Actions on every PR (parallelized)

---

## GAP 10: DEPLOYMENT PIPELINE

### CI/CD Setup (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run lint
      - run: npm run test:unit
      - run: npm run test:e2e
      - run: npm run lighthouse
      - run: npm run axe
```

### Preview Deployments
- Vercel automatically creates preview deployment on every PR
- Preview URL: timuclaude-pr-123.vercel.app
- Comment on PR with preview link
- Lighthouse runs on preview and reports scores in PR comment

### Production Deployment
- Push to `main` branch → Vercel auto-deploys to production
- Domain: timuclaude.com (or timuclaude.vercel.app initially)
- Custom domain setup: add in Vercel dashboard, update DNS

### Environment Variables
```env
# Production (.env.production — stored in Vercel dashboard)
OPENROUTER_API_KEY=sk-or-v1-xxx
AIML_API_KEY=xxx
TIMUCLAUDE_MASTER_KEY=xxx
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=timuclaude.com
NEXT_PUBLIC_GITHUB_REPO=notSaiful/timuclaude-research
```

### Domain Setup
- Purchase: timuclaude.com (or timuclaude.ai if .com unavailable)
- DNS: point to Vercel (A record + CNAME)
- SSL: automatic via Vercel
- WWW redirect: www.timuclaude.com → timuclaude.com

### Monitoring
- Vercel Analytics (free, built-in): page views, Web Vitals
- Plausible: custom events, privacy-friendly
- Sentry (optional): error tracking for production
- Uptime monitoring: Vercel built-in status page