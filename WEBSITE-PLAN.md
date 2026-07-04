# TEMUCLAUDE — WEBSITE, PLAYGROUND & DESIGN PLAN
## Comprehensive Research-Backed Plan for Theme, UI, UX, Playground, Frontend

---

## PART 1: TARGET AUDIENCE EVALUATION

From the marketing session research, our audience breaks into 3 personas:

### Persona A: Individual Developer (60% of traffic)
- **Who**: Solo devs, indie hackers, startup engineers
- **Where**: X/Twitter, Reddit r/LocalLLaMA, GitHub, Hacker News
- **What they want**: 5-minute setup, multi-model support, low cost, self-hosting, open source, good docs
- **What scares them**: Over-abstraction (LangChain fatigue), cost unpredictability, provider lock-in
- **What makes them try**: A playground where they can see Temuclaude beat a single model in 30 seconds
- **Design implication**: Playground must be front and center. No signup wall for first try. Code examples visible immediately.

### Persona B: AI Researcher (20% of traffic)
- **Who**: PhD researchers, AI engineers, people building novel architectures
- **Where**: arXiv, academic conferences, X/Twitter following Karpathy/LeCun
- **What they want**: Determinism, observability, benchmarks with methodology, inspect internals
- **Design implication**: Show orchestration internals visually. Benchmark results with full methodology. "View on GitHub" links everywhere.

### Persona C: Enterprise Team (20% of traffic, 80% of revenue)
- **Who**: Teams at 500+ employee companies building production AI
- **Where**: LinkedIn, enterprise conferences
- **What they want**: Security, compliance, SLAs, cost predictability, self-hosting
- **Design implication**: Enterprise page with compliance badges, security section, dedicated CTA to contact sales

### Key Insight from Research
The #1 growth lever is the "5-minute wow" (Cursor playbook, $0 to $100M ARR). The playground IS the acquisition channel. If a developer can type a question and see Temuclaude's multi-model fusion produce a better answer than a single model — in 30 seconds, no signup — they'll tell others.

---

## PART 2: COMPETITIVE DESIGN ANALYSIS

### Companies Analyzed (with extracted CSS data)

| Company | Theme | Background | Font | Accent | Hero Style |
|---------|-------|-----------|------|--------|-----------|
| Anthropic | Warm light | #FAF9F5 | Anthropic Serif/Sans | Clay #C6613F | Editorial headline |
| OpenRouter | Dark | #090A0B | Inter | (uses favicons) | Stats + model grid |
| Cursor | Warm dark | #14120B | CursorGothic + Berkeley Mono | Orange #F54E00 | Interactive demo |
| v0 (Vercel) | Dark | oklch(14.5% 0 0) | GeistSans | Blue oklch | Prompt-first input |
| Together AI | Light | #FFFFFF | The Future (custom) | Orange #FC4C02 | 3D shapes + stats |
| HuggingFace | Dark navy | rgb(11,15,25) | Source Sans Pro | Yellow | Community grid |
| Linear | Near-black | #08090A | Inter Variable + Berkeley Mono | Indigo #5E6AD2 | Editorial magazine |

### Key Finding
Dark mode dominates (5 of 7 companies). But Anthropic's warm ivory (#FAF9F5) is the most distinctive and memorable. It stands out precisely because it's NOT dark.

### Our Position
Temuclaude should use **warm light minimal** — matching Ggs's preference and differentiating from the dark-mode sea. Anthropic's palette is our foundation, adapted with our own identity.

---

## PART 3: THEME & COLOR PALETTE

### Design Philosophy
"Warm minimalism" — like a well-crafted publication, not a tech-bro dashboard. Warmth signals orchestration (multiple minds collaborating), approachability (open source), and trust (transparency). Every element is intentional. No decoration without purpose.

### Color Palette (exact hex values)

```css
:root {
  /* Backgrounds — warm ivory, not pure white */
  --bg-primary: #FAF8F5;      /* main page background */
  --bg-secondary: #F0EDE6;    /* card backgrounds, alternate sections */
  --bg-tertiary: #E8E4DC;     /* hover states, input fields */
  --bg-dark: #1A1816;         /* footer, code blocks, dark sections */

  /* Text — warm near-black */
  --text-primary: #1A1816;    /* headings, body */
  --text-secondary: #5E5B56;  /* subtext, descriptions */
  --text-muted: #8E8B85;      /* labels, metadata */
  --text-inverse: #FAF8F5;    /* text on dark backgrounds */

  /* Accents — warm clay/coral (orchestration = warmth) */
  --accent-primary: #D97757;  /* primary CTA, links, highlights */
  --accent-hover: #C56547;    /* hover state for accent */
  --accent-light: #F0D5C8;    /* subtle accent backgrounds */

  /* Secondary accents */
  --accent-fig: #C46686;      /* secondary highlights */
  --accent-olive: #788C5D;    /* success, open-source badge */
  --accent-amber: #E8B547;    /* warnings, premium features */

  /* Borders — subtle, warm */
  --border-subtle: rgba(26, 24, 22, 0.08);   /* card borders */
  --border-default: rgba(26, 24, 22, 0.16);  /* input borders */
  --border-strong: rgba(26, 24, 22, 0.24);   /* emphasis borders */

  /* Shadows — minimal, warm */
  --shadow-sm: 0 1px 2px rgba(26, 24, 22, 0.04);
  --shadow-md: 0 2px 8px rgba(26, 24, 22, 0.06);
  --shadow-lg: 0 8px 24px rgba(26, 24, 22, 0.08);

  /* Radii */
  --radius-sm: 6px;   /* buttons, inputs */
  --radius-md: 12px;  /* cards */
  --radius-lg: 20px;  /* large containers */
  --radius-full: 9999px; /* pills, badges */
}
```

### Why This Palette
- #FAF8F5 is softer than pure white — reduces eye strain, feels crafted
- #D97757 (clay/coral) is warm and human — not cold corporate blue
- Warm grays (#5E5B56, #8E8B85) feel more natural than pure gray
- 8% opacity borders are invisible until you need them (Anthropic pattern)
- Minimal shadows (0.04-0.08 opacity) — depth without heaviness

---

## PART 4: TYPOGRAPHY

### Font Stack

```css
:root {
  /* Primary sans-serif — Inter (free, variable, industry standard) */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;

  /* Monospace — JetBrains Mono (free, excellent for code) */
  --font-mono: 'JetBrains Mono', 'SF Mono', Monaco, monospace;

  /* Optional serif for editorial sections — Source Serif Pro */
  --font-serif: 'Source Serif Pro', Georgia, serif;
}
```

### Typography Scale (responsive with clamp)

```css
:root {
  /* Fluid sizing — scales smoothly from mobile to desktop */
  --text-h1: clamp(2.25rem, 2rem + 2vw, 3.5rem);      /* 36-56px */
  --text-h2: clamp(1.75rem, 1.5rem + 1.5vw, 2.5rem);   /* 28-40px */
  --text-h3: clamp(1.25rem, 1.1rem + 0.8vw, 1.625rem); /* 20-26px */
  --text-body: 1rem;      /* 16px */
  --text-small: 0.875rem; /* 14px */
  --text-mono: 0.8125rem; /* 13px for code */

  /* Weights */
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* Line heights */
  --leading-tight: 1.15;   /* headings */
  --leading-normal: 1.6;   /* body */
  --leading-relaxed: 1.75; /* long-form prose */

  /* Letter spacing */
  --tracking-tight: -0.025em; /* headings (modern, compact) */
  --tracking-normal: 0;       /* body */
  --tracking-wide: 0.025em;   /* labels, buttons */
}
```

### H1 Style
- Font: Inter, 600 weight
- Size: clamp(2.25rem, 2rem + 2vw, 3.5rem)
- Letter-spacing: -0.025em
- Line-height: 1.15
- Color: #1A1816

### Code Blocks
- Font: JetBrains Mono, 13px
- Line-height: 1.5
- Background: #1A1816 (dark warm)
- Text: #E8E4DC
- Padding: 16px 20px
- Border-radius: 12px
- Copy button top-right (appears on hover)

---

## PART 5: LOGO CONCEPT

### Design Direction
Abstract geometric mark suggesting **orchestration** — multiple elements working together under one conductor.

### Concept: "The Conductor"
- 3-5 small circles (representing individual LLM models) arranged in an arc
- Connected by thin lines to a central larger circle (the orchestrator/Temuclaude)
- Like a network graph or constellation
- Solid color, no gradients
- Works at 16px (favicon) to billboard scale

### Logo Color
- Primary: #D97757 (warm clay) for the nodes and lines
- Or: #1A1816 (warm near-black) for monochrome contexts
- On dark backgrounds: #FAF8F5 (ivory)

### Logo Variations
1. **Full lockup**: Logo mark + "Temuclaude" wordmark (Inter 600, -0.02em)
2. **Mark only**: Just the orchestration nodes (favicon, social avatar)
3. **Monochrome**: Single color version for documentation/printing
4. **Animated**: Nodes pulse/connect sequentially (for website hero, loading states)

### Wordmark
- Font: Inter, 600 weight
- Letter-spacing: -0.02em
- Color: #1A1816
- The "T" could subtly echo the orchestration pattern (optional)

---

## PART 6: UI COMPONENTS

### Buttons
```css
/* Primary CTA — solid dark */
.btn-primary {
  background: #1A1816;
  color: #FAF8F5;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  letter-spacing: 0.025em;
  transition: all 150ms cubic-bezier(.25, 1, .5, 1);
}
.btn-primary:hover {
  background: #2A2826;  /* slightly lighter */
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(26, 24, 22, 0.12);
}

/* Secondary CTA — outline */
.btn-secondary {
  background: transparent;
  color: #1A1816;
  border: 1px solid rgba(26, 24, 22, 0.16);
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 500;
}
.btn-secondary:hover {
  border-color: #D97757;
  color: #D97757;
}

/* Accent CTA — warm clay (for playground "Run" button) */
.btn-accent {
  background: #D97757;
  color: #FFFFFF;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 600;
}
.btn-accent:hover {
  background: #C56547;
}
```

### Cards
```css
.card {
  background: #FFFFFF;  /* or #F0EDE6 for alternate sections */
  border: 1px solid rgba(26, 24, 22, 0.08);
  border-radius: 12px;
  padding: 24px;
  transition: all 200ms cubic-bezier(.25, 1, .5, 1);
}
.card:hover {
  border-color: rgba(26, 24, 22, 0.16);
  box-shadow: 0 4px 16px rgba(26, 24, 22, 0.06);
  transform: translateY(-2px);
}
```

### Input Fields
```css
.input {
  background: #FAF8F5;
  border: 1px solid rgba(26, 24, 22, 0.16);
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 0.875rem;
  color: #1A1816;
  transition: border-color 150ms;
}
.input:focus {
  outline: none;
  border-color: #D97757;
  box-shadow: 0 0 0 3px rgba(217, 119, 87, 0.12);
}
```

### Navigation
- Height: 64px (sticky, transparent over hero, solid on scroll)
- Background: rgba(250, 248, 245, 0.8) with backdrop-filter: blur(12px)
- Logo left, nav links center-right, CTA button right
- Nav links: Inter 500, 0.875rem, color #5E5B56, hover #1A1816
- Cmd+K search (like Linear, v0, Cursor all have)

---

## PART 7: WEBSITE STRUCTURE

### Pages
1. **/** — Landing page (hero + features + benchmarks + pricing + footer)
2. **/playground** — Interactive playground (THE key page)
3. **/docs** — Documentation (Quickstart, API, Models, Guides)
4. **/models** — Model pool listing (all available models with specs)
5. **/benchmarks** — Benchmark results (live, with methodology)
6. **/pricing** — Detailed pricing page
7. **/enterprise** — Enterprise landing page
8. **/github** — Redirect to GitHub repo

### Landing Page Layout

```
┌─────────────────────────────────────────┐
│ NAV: Logo  | Models  Playground  Docs  Pricing  | [Get Started] │
├─────────────────────────────────────────┤
│                                         │
│         HERO SECTION                    │
│  "One question. Many minds.             │
│   One superior answer."                 │
│                                         │
│  [Try the Playground]  [View on GitHub] │
│                                         │
│  [Animated orchestration diagram]       │
│  (SVG: 5 model nodes connecting to      │
│   central hub, data flowing)            │
│                                         │
├─────────────────────────────────────────┤
│  TRUST BAR                              │
│  "Powered by: GLM-5.2 | DeepSeek V4 |   │
│   Kimi K2.6 | MiniMax M3 | Nemotron"    │
│  (model logos/names in a row)           │
├─────────────────────────────────────────┤
│  STATS BAR                              │
│  28x cheaper | 5 models | 3 backends |  │
│  Open source | MIT license              │
├─────────────────────────────────────────┤
│  HOW IT WORKS (3 cards)                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │ 1. Route│ │ 2. Fuse │ │ 3. Verify│   │
│  │ Classify│ │ 3+ models│ │ Code+QA │   │
│  │ + route │ │ answer  │ │ gate    │   │
│  └─────────┘ └─────────┘ └─────────┘    │
├─────────────────────────────────────────┤
│  BENCHMARK RESULTS (grid of cards)      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │GPQA  │ │HLE   │ │GDPval│ │MRCR  │   │
│  │95-98%│ │45-55%│ │1824+ │ │0.8-1 │   │
│  │vs 94%│ │vs 53%│ │vs1783│ │vs .76│   │
│  └──────┘ └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────────────┤
│  PLAYGROUND PREVIEW                     │
│  [Screenshot or live mini-playground]    │
│  "Try it now — no signup required"      │
│  [Open Playground →]                    │
├─────────────────────────────────────────┤
│  PRICING (3 tiers)                      │
│  ┌────────┐ ┌────────┐ ┌────────┐      │
│  │ Free   │ │ Pro    │ │Enterprise│    │
│  │ $0     │ │ $15/mo │ │ $499/mo │     │
│  │Self-host│ │Managed│ │ SLA+SSO│      │
│  └────────┘ └────────┘ └────────┘      │
├─────────────────────────────────────────┤
│  OPEN SOURCE CALLOUT                    │
│  "MIT licensed. Read the code.          │
│   Contribute. Self-host."               │
│  [GitHub stars count] [Contribute →]    │
├─────────────────────────────────────────┤
│  FOOTER                                 │
│  Product | Resources | Company |        │
│  GitHub | MIT License | Built by Ggs    │
└─────────────────────────────────────────┘
```

---

## PART 8: PLAYGROUND DESIGN

### The Playground is Our Differentiator
No competitor shows the orchestration happening. OpenRouter's Fusion page shows models side by side but doesn't show voting, code verification, or self-QA. Our playground shows EVERYTHING — the user sees the magic happening.

### Playground Layout

```
┌──────────────────────────────────────────────────────┐
│ NAV (compact)                                         │
├────────────┬─────────────────────────────────────────┤
│            │                                          │
│  SIDEBAR   │         MAIN CHAT AREA                   │
│            │                                          │
│  [New Chat]│  ┌──────────────────────────────────┐   │
│            │  │ User: What is the derivative of   │   │
│  Recent:   │  │ x^3 + 2x^2 - 5x + 1?              │   │
│  - Math Q  │  └──────────────────────────────────┘   │
│  - Code Q  │                                          │
│  - Reason  │  ┌──────────────────────────────────┐   │
│            │  │ Temuclaude:                       │   │
│  Examples: │  │                                   │   │
│  - 9.9 vs  │  │  The derivative is 3x² + 4x - 5  │   │
│    9.11    │  │                                   │   │
│  - Car Wash│  │  [Show how this answer was built →]│  │
│  - Code fix│  └──────────────────────────────────┘   │
│            │                                          │
│  Settings: │  ┌──────────────────────────────────┐   │
│  Mode:     │  │ [Type a question...]       [Run] │   │
│  [Quick]   │  └──────────────────────────────────┘   │
│  [Fusion]  │                                          │
│  [Verify]  │                                          │
│            │                                          │
│  Models:   │                                          │
│  [✓] GLM   │                                          │
│  [✓] DS V4 │                                          │
│  [✓] Kimi  │                                          │
│  [ ] Mini  │                                          │
│  [ ] Nemo  │                                          │
│            │                                          │
│  Advanced: │                                          │
│  Temp: 0.7 │                                          │
│  Max tok:  │                                          │
│  8192      │                                          │
│            │                                          │
└────────────┴─────────────────────────────────────────┘
```

### "Show How This Answer Was Built" — Our Unique Feature
When the user clicks this, a panel expands showing the orchestration in real-time:

```
┌──────────────────────────────────────────────────────┐
│  HOW THIS ANSWER WAS BUILT                            │
│                                                       │
│  Step 1: TASK CLASSIFICATION                          │
│  ┌──────────────────────────────────────────────┐    │
│  │ Classified as: math (trivial tier)            │    │
│  │ Routed to: gpt-oss-120b (cheap model)         │    │
│  │ Latency: 1.2s                                 │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Step 2: MODEL RESPONSE                               │
│  ┌──────────────────────────────────────────────┐    │
│  │ gpt-oss-120b responded:                      │    │
│  │ "The derivative of x^3 + 2x^2 - 5x + 1 is    │    │
│  │  3x^2 + 4x - 5, computed using the power     │    │
│  │  rule for each term..."                       │    │
│  │                                               │    │
│  │ Confidence: High                              │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Step 3: CODE VERIFICATION                           │
│  ┌──────────────────────────────────────────────┐    │
│  │ Generated Python code:                        │    │
│  │ >>> from sympy import *                       │    │
│  │ >>> x = symbols('x')                          │    │
│  │ >>> diff(x**3 + 2*x**2 - 5*x + 1, x)         │    │
│  │ 3*x**2 + 4*x - 5                              │    │
│  │                                               │    │
│  │ ✓ Verified: Code output matches model answer │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Step 4: SELF-QA GATE                                 │
│  ┌──────────────────────────────────────────────┐    │
│  │ Verifier (nemotron-3-ultra) scored: 9/10     │    │
│  │ "Correct application of power rule.           │    │
│  │  Clear step-by-step explanation."             │    │
│  │ ✓ Passed (threshold: 8)                       │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Total latency: 3.4s | Cost: $0.002                   │
└──────────────────────────────────────────────────────┘
```

### For Fusion Mode (hard questions)
The panel shows ALL models answering in parallel:

```
┌──────────────────────────────────────────────────────┐
│  FUSION ORCHESTRATION                                 │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ GLM-5.2     │  │ DeepSeek V4 │  │ Kimi K2.6   │  │
│  │             │  │             │  │             │  │
│  │ "3x² + 4x  │  │ "3x² + 4x  │  │ "3x² + 4x  │  │
│  │  - 5"       │  │  - 5"       │  │  - 5"       │  │
│  │             │  │             │  │             │  │
│  │ ✓ Correct   │  │ ✓ Correct   │  │ ✓ Correct   │  │
│  │ 1.2s        │  │ 2.1s        │  │ 1.8s        │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                       │
│  Aggregator (DeepSeek V4 Pro):                        │
│  "All three models agree: 3x² + 4x - 5.              │
│   The derivative was computed using the               │
│   power rule for each term..."                        │
│                                                       │
│  Self-consistency: 3/3 agree (100% confidence)        │
│  Code verification: ✓ Verified                        │
│  Self-QA: 10/10                                       │
│                                                       │
│  Total: 4.2s | Cost: $0.019 | 3 models + 1 aggregator│
└──────────────────────────────────────────────────────┘
```

### Playground Controls

**Mode Selector (3 options):**
1. **Quick** — Single model, fast, cheapest (trivial/medium tier)
2. **Fusion** — Multi-model fusion + aggregator (hard tier)
3. **Verify** — Fusion + code verification + self-QA (hardest tier)

**Model Selector:**
- Checkboxes for each model (GLM-5.2, DeepSeek V4 Pro, Kimi K2.6, etc.)
- In Quick mode: single dropdown
- In Fusion mode: checkboxes (pick 3-5)
- "Auto-select best models" button (uses our task classifier)

**Parameters:**
- Temperature slider (0.0 - 1.0, default 0.7 for Fusion)
- Max tokens input (default 8192)
- System prompt (optional, collapsible)

**Example Prompts** (clickable chips, like OpenRouter):
- "What is 9.9 vs 9.11 — which is larger?" (reasoning test)
- "Write a Python function to merge two sorted lists" (coding test)
- "Explain quantum entanglement in simple terms" (knowledge test)
- "Solve: A train leaves Boston at 60mph..." (math test)

### Streaming Responses
- Text appears word-by-word as the model generates
- Uses Server-Sent Events (SSE) for real-time streaming
- "Typing indicator" (three animated dots) while waiting for first token
- Copy button appears after response completes
- "Show orchestration" button appears after response completes

### No Signup Required for First Try
The user can type a question and get a response WITHOUT creating an account. This is critical for the "5-minute wow." After 3 free queries, show a gentle prompt to create an account or self-host with Ollama.

---

## PART 9: FRONTEND TECH STACK

### Recommended Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | Next.js 14+ (App Router) | Industry standard, SSR/SSG, API routes, React Server Components |
| **Styling** | Tailwind CSS 4 | Utility-first, matches our design system, responsive |
| **Components** | shadcn/ui (Radix primitives) | Accessible, customizable, not a heavy UI library |
| **Icons** | Lucide React | Open source, consistent line icons, tree-shakeable |
| **Fonts** | Inter (variable) + JetBrains Mono | Both free, variable, industry standard |
| **Code highlighting** | Shiki | VS Code-quality highlighting, supports many languages |
| **Markdown rendering** | react-markdown + remark-gfm | For rendering model responses with formatting |
| **Animation** | Framer Motion | React-native, spring physics, scroll-triggered reveals |
| **State management** | Zustand | Simple, no boilerplate, works great with Next.js |
| **API calls** | Native fetch + Server-Sent Events | SSE for streaming responses, fetch for REST |
| **Deployment** | Vercel | Same as Next.js, instant deploys, edge network |

### Performance Requirements

| Metric | Target | Why |
|--------|--------|-----|
| **LCP** (Largest Contentful Paint) | < 1.5s | First impression speed |
| **FID/INP** (Interaction) | < 100ms | Playground must feel instant |
| **CLS** (Layout Shift) | < 0.1 | No janky shifts |
| **TTFB** (Time to First Byte) | < 200ms | Server response speed |
| **Lighthouse score** | 95+ | SEO + quality signal |
| **Bundle size** | < 200KB (initial) | Fast first load |
| **Streaming first token** | < 500ms | Playground responsiveness |

### Performance Techniques
1. **Server Components** for static content (landing page, docs)
2. **Dynamic imports** for playground (load only when needed)
3. **Edge runtime** for API routes (global low latency)
4. **Font optimization**: `next/font` with `display: swap`
5. **Image optimization**: `next/image` with AVIF/WebP
6. **Code splitting**: Playground loads separately from landing page
7. **Prefetch**: Links to playground prefetched on hover
8. **CSS**: Tailwind purges unused styles, critical CSS inlined

---

## PART 10: ANIMATION & MICRO-INTERACTIONS

### Easing
```css
--ease-spring: cubic-bezier(0.25, 1, 0.5, 1);      /* natural, organic */
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);     /* material design */
--ease-in: cubic-bezier(0.4, 0, 1, 1);             /* exiting */
```

### Timing
```css
--duration-fast: 150ms;     /* hover, focus, button press */
--duration-normal: 250ms;   /* overlays, modals, panels */
--duration-slow: 400ms;     /* page transitions, large reveals */
```

### Micro-Interactions
- **Button hover**: background darkens, translateY(-1px), shadow appears (150ms)
- **Card hover**: border darkens, shadow increases, translateY(-2px) (200ms)
- **Link hover**: underline fades in from left to right (150ms)
- **Input focus**: border color transitions to accent, ring appears (150ms)
- **Copy button**: icon changes from copy to checkmark, fades back after 2s
- **Tab switch**: content slides 8px + fades (250ms)
- **Modal open**: backdrop fades in (200ms), content scales from 0.96 + fades (250ms)

### Scroll-Triggered Reveals
- IntersectionObserver-based
- Fade in + 12px slide up
- Staggered 50ms between cards in a grid
- Only trigger once (no re-animation on scroll back)

### Hero Animation (Orchestration Diagram)
- SVG-based (not a video — for performance)
- 5 model nodes (small circles) arranged in an arc
- 1 central hub (Temuclaude logo mark)
- Animated connection lines (draw in from node to hub)
- Data "pulses" travel along the lines (small dots moving)
- Loops every 4 seconds
- Respects `prefers-reduced-motion`

### Playground Loading States
- Skeleton screens (not spinners) for response loading
- "Typing indicator" (3 animated dots) while waiting for first token
- Progress bar for Fusion mode showing each model's status:
  - "GLM-5.2: responding..." (pulsing)
  - "DeepSeek V4: responding..." (pulsing)
  - "Kimi K2.6: done ✓" (completed)
  - "Aggregating..." (spinner)

---

## PART 11: DOCUMENTATION DESIGN

### Docs Structure
- **Quickstart**: 5-minute guide (install, configure, first query)
- **API Reference**: OpenAI-compatible endpoint, parameters, examples
- **Models**: Available models, capabilities, pricing
- **Configuration**: LiteLLM config, environment variables, backends
- **Orchestration**: How Fusion works, self-consistency, code verification
- **Self-Improvement**: Self-QA gate, skills, adaptive routing, GEPA
- **Benchmarks**: Methodology, datasets, results, reproducibility
- **Self-Hosting**: Ollama setup, Docker deployment, Fly.io

### Docs Design
- Left sidebar: searchable hierarchical nav (like Linear, v0)
- Right sidebar: "On this page" table of contents
- Main content: max-width 680px, 16px font, 1.6 line-height
- Code blocks: JetBrains Mono, copy button, syntax highlighting (Shiki)
- "Edit on GitHub" link on every page
- Cmd+K command palette for search
- Light mode primary, dark mode toggle (for long reading sessions)
- Built with Fumadocs or Docusaurus (both support custom branding)

---

## PART 12: TIPS & TRICKS FROM RESEARCH

### From Cursor ($0 → $100M ARR, zero marketing budget)
1. The product IS the acquisition channel — if it works in 5 minutes, they tell others
2. Founder-led content beats brand accounts 10x
3. Video demos outperform text announcements
4. Subtle CTAs ("try the playground") work better than "Sign up now!"
5. Reply to every comment in the first 1-2 hours (algorithm boost)

### From Anthropic (most distinctive design)
6. Warm light (#FAF8F5) stands out against the dark-mode sea
7. Serif typography for editorial feel, sans for UI
8. Inline links in headlines make the H1 interactive
9. Named color swatches (clay, coral, fig, olive) create a design language

### From Linear (most polished)
10. "FIG 0.2" annotations treat screenshots like design publication figures
11. Comprehensive easing system (10+ named easings) for precise motion
12. Inter Variable with stylistic sets (ss03) for alternate glyphs
13. 12-column grid with very precise spacing

### From v0 (best playground-first approach)
14. The prompt input IS the hero — no traditional marketing copy above the fold
15. Template gallery with video previews drives engagement
16. "Prompt. Build. Publish." — 3-step flow shown visually

### From OpenRouter (best Fusion UI)
17. Quality/Budget/Fast/Custom mode toggles for Fusion
18. Model selector chips with provider favicons
19. Pre-built test prompts (9.9 vs 9.11, Strawberry Test, Car Wash Test)
20. Chat memory controls and tools selector in the input area

### From Developer Tool Research
21. 5-minute quickstart or they leave — README quality drives GitHub stars
22. Open source is the #1 acquisition channel — every successful AI company has this
23. Benchmarks with methodology build technical credibility
24. Community testimonials > marketing copy
25. No corporate-speak — developers see through it instantly
26. Free tier must be genuinely useful, not a limited trial
27. "No credit card required" removes the biggest signup friction
28. Bottom-up adoption (devs try free) → enterprise conversion (devs bring to teams)

---

## PART 13: IMPLEMENTATION PRIORITY

### Phase 1: Landing Page (Day 1-2)
- Hero with animated orchestration SVG
- Trust bar (model names)
- Stats bar
- How it works (3 cards)
- Benchmark results (grid)
- Pricing (3 tiers)
- Open source callout
- Footer

### Phase 2: Playground (Day 3-5)
- Chat interface with streaming
- Mode selector (Quick/Fusion/Verify)
- Model selector
- "Show how this answer was built" panel
- Example prompts
- No-signup first try (3 free queries)

### Phase 3: Documentation (Day 6-7)
- Quickstart guide
- API reference
- Models page
- Configuration guide
- "Edit on GitHub" links

### Phase 4: Polish (Day 8-10)
- Scroll-triggered animations
- Cmd+K search
- Mobile responsive
- Dark mode toggle (for docs)
- SEO optimization (meta tags, sitemap, robots.txt)
- Performance audit (Lighthouse 95+)

---

## SUMMARY

Temuclaude's website should be warm, minimal, and crafted — like Anthropic's but with its own identity. The playground is the star: no signup wall, streaming responses, and the unique "show how this answer was built" panel that reveals our orchestration magic. Warm ivory (#FAF8F5) background, clay accent (#D97757), Inter + JetBrains Mono typography, animated SVG orchestration diagram in the hero, and a 3-mode playground (Quick/Fusion/Verify) that shows the user exactly how multiple models collaborate to produce a superior answer.

The design stands out because every other AI company uses dark mode. We use warm light. Every other company hides their internals. We show them. Every other company requires signup. We let you try first.

That's the plan, brother. Shall I start building?