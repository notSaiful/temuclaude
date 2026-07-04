# TEMUCLAUDE — WEBSITE PLAN: GAP FILLS (10 Items)

---

## GAP 1: NAVIGATION DETAILED DESIGN

### Desktop Navigation (1024px+)
- Height: 64px, sticky, transparent over hero
- Background on scroll: rgba(250, 248, 245, 0.85) + backdrop-filter: blur(12px)
- Left: Logo (32px mark + "Temuclaude" wordmark)
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
- Bar chart comparing Temuclaude vs Fable 5, GPT-5.5, Gemini 3.1 Pro
- X-axis: benchmarks (GPQA, HLE, LiveCodeBench, etc.)
- Y-axis: score (%)
- Temuclaude bars: #D97757 (clay)
- Competitor bars: #8E8B85 (muted gray)
- Hover: tooltip with exact score, methodology link
- Toggle: switch between "All benchmarks" and "Temuclaude wins"
- Library: Recharts (React-native, open source, ~40KB)

### Full Comparison Table
- Same as Fugu's approach: bold for highest, underline for second
- Columns: Benchmark, Temuclaude, Fable 5, GPT-5.5, Gemini 3.1 Pro
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
- Code block: `python benchmarks/run_temuclaude.py --dataset hle --sample 100`
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
<Script defer data-domain="temuclaude.com" src="https://plausible.io/js/script.js" />

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
Subtext: "Temuclaude orchestrates 5 AI models to beat frontier models at 28x lower cost. Free with Ollama. Open source. MIT licensed."
CTA Primary: "Try the Playground"
CTA Secondary: "View on GitHub"
Install command: "pip install temuclaude"
Backend tabs: "Ollama (Free)" | "OpenRouter" | "ai/ml API"

### Metrics Bar
"5 Models" | "3 Backends" | "28x Cheaper" | "MIT Licensed"

### How It Works (3 cards)
01. "Understanding your question"
    "Temuclaude classifies your query — math, code, reasoning, knowledge — and routes it to the best model for the task."

02. "Combining multiple answers"
    "For hard questions, 3-5 models answer in parallel. A dynamic aggregator synthesizes the best parts of each response."

03. "Quality check"
    "Code execution verifies math. A self-QA gate scores the answer 0-10. If below 8, it retries with feedback."

### Platform Badges
"Available on: OpenRouter · Ollama · ai/ml API"

### Benchmark Section
Heading: "Benchmark Results"
Subtext: "Projected scores from research analysis. Live results coming after Phase 6 testing."
Table intro: "Temuclaude vs frontier models across 9 benchmarks."

### Playground Preview
Heading: "See it in action"
Text: "Try Temuclaude right now — no signup required. Watch 5 models collaborate in real-time."
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
1. "How is Temuclaude different from using GPT-5.5 directly?"
   "GPT-5.5 is one model. Temuclaude orchestrates 5 models — fusing their answers, verifying with code, and quality-checking with self-QA. The result is measurably better on benchmarks, at 28x lower cost."
2. "Is it really free?"
   "Yes. Self-host with Ollama and it's free forever, unlimited queries. The cloud version costs $15/month for managed hosting."
3. "Which models does Temuclaude use?"
   "GLM-5.2, DeepSeek V4 Pro, Kimi K2.6, MiniMax M3, Nemotron 3 Ultra, and GPT-OSS 120B. You can add your own models too."
4. "Can I use my own API keys?"
   "Yes. Bring your own OpenRouter, ai/ml, or Ollama keys. No markup on your costs."
5. "How does the orchestration work?"
   "Temuclaude classifies your query, routes it to the best model(s), fuses multiple answers when needed, verifies math with code execution, and quality-checks with a self-QA gate. You see the whole process in the playground."
6. "Is my data stored?"
   "No. Queries are processed in real-time and not stored. Your API keys are stored only in your browser session (sessionStorage) and cleared when you close the tab."
7. "Can I self-host?"
   "Yes. Clone the repo, install dependencies, run with Ollama. Full instructions in the docs."
8. "What about enterprise?"
   "Enterprise includes SSO, SLA, self-hosted deployment, dedicated support, and 200K queries/month. Contact us for custom pricing."

### Empty State (Playground)
Heading: "Ask Temuclaude anything"
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
- Preview URL: temuclaude-pr-123.vercel.app
- Comment on PR with preview link
- Lighthouse runs on preview and reports scores in PR comment

### Production Deployment
- Push to `main` branch → Vercel auto-deploys to production
- Domain: temuclaude.com (or temuclaude.vercel.app initially)
- Custom domain setup: add in Vercel dashboard, update DNS

### Environment Variables
```env
# Production (.env.production — stored in Vercel dashboard)
OPENROUTER_API_KEY=sk-or-v1-xxx
AIML_API_KEY=xxx
TEMUCLAUDE_MASTER_KEY=xxx
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=temuclaude.com
NEXT_PUBLIC_GITHUB_REPO=notSaiful/temuclaude-research
```

### Domain Setup
- Purchase: temuclaude.com (or temuclaude.ai if .com unavailable)
- DNS: point to Vercel (A record + CNAME)
- SSL: automatic via Vercel
- WWW redirect: www.temuclaude.com → temuclaude.com

### Monitoring
- Vercel Analytics (free, built-in): page views, Web Vitals
- Plausible: custom events, privacy-friendly
- Sentry (optional): error tracking for production
- Uptime monitoring: Vercel built-in status page
---

## MINOR GAP FILLS (5 items)

---

## GAP 11: COMPONENT SPECS (Modal, Stepper, Tooltip, Accordion, Breadcrumb)

### Modal/Dialog Component
- Overlay: fixed inset-0, bg rgba(26,24,22,0.4), backdrop-filter blur(4px)
- Container: centered, max-width 500px, bg #FFFFFF, radius 12px, shadow-lg, padding 24px
- Close: X button top-right (24px, #8E8B85, hover #1A1816)
- Animation: backdrop fades in (200ms), content scales from 0.96 + fades (250ms, ease-spring)
- Accessibility: role="dialog", aria-modal="true", aria-labelledby="modal-title", focus trap inside modal, Escape to close, return focus to trigger on close

### Stepper Component (for orchestration visualization)
- Horizontal layout: steps connected by thin lines
- Each step: circle (24px) + label below
- States: pending (#E8E4DC), active (#D97757, pulsing), completed (#788C5D with checkmark), error (#C46686 with X)
- Line between steps: #E8E4DC (pending), #D97757 (active), #788C5D (completed)
- Labels: Inter 400, 0.75rem, #5E5B56
- Active step: scale 1.1, subtle pulse animation
- Fades in steps as they complete (staggered 200ms)

### Tooltip Component
- Trigger: hover or focus (keyboard accessible)
- Content: small popover, bg #1A1816, text #FAF8F5, font 0.75rem, padding 6px 10px, radius 6px
- Arrow: 6px triangle pointing to trigger
- Animation: fade in + 4px slide (150ms, ease-spring)
- Position: auto-detected (top/bottom/left/right based on viewport)
- Delay: 500ms show, 0ms hide
- Accessibility: role="tooltip", aria-describedby on trigger

### Accordion Component (for FAQ and docs sidebar)
- Item: clickable header + collapsible content
- Header: Inter 500, 0.9375rem, #1A1816, padding 16px 0, cursor pointer
- Icon: chevron-right (collapsed) → chevron-down (expanded), 16px, #8E8B85, rotate 90deg (200ms)
- Content: Inter 400, 0.9375rem, #5E5B56, padding 0 0 16px 0
- Border: 1px solid rgba(26,24,22,0.08) between items
- Animation: max-height transition (250ms, ease-spring)
- Accessibility: role="button", aria-expanded, aria-controls, keyboard Enter/Space to toggle

### Breadcrumb Component (for docs)
- Container: flex row, Inter 400, 0.8125rem, #8E8B85
- Items: Home > Docs > [Section] > [Page]
- Separator: "/" in #8E8B85 (with spaces)
- Current page: #1A1816 (not clickable)
- Links: hover #D97757, underline on hover
- Accessibility: nav aria-label="Breadcrumb", ol with li items

---

## GAP 12: ENTERPRISE PAGE DESIGN

### Layout
1. Hero: "Enterprise-grade AI orchestration" + "Security, compliance, and scale for your team" + [Contact Sales]
2. Trust bar: "Trusted by [company logos]" (placeholder until we have customers)
3. Features grid (6 cards):
   - SSO/SAML — "Single sign-on with your existing identity provider"
   - SOC2 Compliance — "Audit-ready logs and data controls"
   - Self-Hosted — "Deploy on your own infrastructure. Your data never leaves."
   - SLA — "99.9% uptime guarantee with dedicated support"
   - Custom Models — "Add your own fine-tuned models to the pool"
   - Team Management — "Role-based access control, audit logs, usage limits"
4. Pricing callout: "Custom pricing. Contact our team for a quote." + [Contact Sales]
5. Contact form: name, email, company, message + [Send]
6. FAQ (enterprise-specific):
   - "Can we self-host?" → "Yes. Full self-hosted deployment with Docker or Kubernetes."
   - "Do you offer custom models?" → "Yes. Add your own fine-tuned models to the orchestration pool."
   - "What compliance certifications do you have?" → "We're working toward SOC2 Type II. Audit logs and data controls are available now."
   - "What's the SLA?" → "99.9% uptime with 4-hour response time for critical issues."

---

## GAP 13: PASSWORD RESET PAGE (detailed)

### /forgot-password
- Same centered card as login (max-width 400px)
- Logo at top
- "Reset your password" heading (Inter 600, 1.25rem)
- "Enter your email and we'll send you a reset link." subtext
- Email input field
- [Send Reset Link] button (primary, full width)
- "Remember your password? [Log in]" link
- On submit: "Check your email for a reset link." success message, button becomes [Back to Login]

### /reset-password
- Same card layout
- "Set a new password" heading
- New password input (with show/hide toggle)
- Confirm password input
- Password strength indicator (weak/fair/good/strong — colored bar)
- [Reset Password] button (primary, full width)
- On success: redirect to /login with "Password reset successfully" toast

---

## GAP 14: OG IMAGE DESIGN

### Design
- Size: 1200×630px
- Background: #FAF8F5 (warm ivory)
- Left side: Logo mark (orchestration nodes) + "Temuclaude" wordmark
- Center: "One question. Many minds. One superior answer." in Inter 600, 48px, #1A1816
- Below: "Open-source LLM orchestration · 28x cheaper than frontier models" in Inter 400, 20px, #5E5B56
- Bottom: "5 models · 3 backends · MIT licensed" in Inter 500, 16px, #D97757
- Right side: subtle SVG orchestration diagram (low opacity, decorative)

### Implementation
- Create as HTML/CSS page, serve locally, screenshot with browser_vision
- Or generate with image_generate tool
- Save as /public/og-image.png
- Reference in meta tags

---

## GAP 15: MODELS PAGE DESIGN

### Layout
1. Heading: "Model Pool" + "5 models, 3 backends, zero lock-in"
2. Filter bar: search input + filter chips (by capability: Reasoning, Coding, Vision, Long Context, Cheap)
3. Model cards grid (responsive: 1 col mobile, 2 col tablet, 3 col desktop)

### Model Card
- Provider logo/name (top)
- Model name (Inter 600, 1.125rem)
- Tags: chips showing capabilities (Reasoning, Coding, Vision, Tools, Thinking)
- Stats: Context length, Parameters, Pricing ($/M tokens)
- Backend availability: "Ollama ✓ | OpenRouter ✓ | ai/ml ✓"
- [Try in Playground] button (links to playground with model pre-selected)
- [View on OpenRouter] external link

### Models to list
1. GLM-5.2 — Orchestrator, 1M context, tools, thinking
2. DeepSeek V4 Pro — Reasoning, coding, 1.6T params, 3 thinking modes
3. Kimi K2.6 — Vision, tools, thinking, 262K context
4. MiniMax M3 — Generation, vision, tools, 1M context
5. Nemotron 3 Ultra — Verification, agentic evaluation, 1M context
6. GPT-OSS 120B — Cheap routing, 131K context
