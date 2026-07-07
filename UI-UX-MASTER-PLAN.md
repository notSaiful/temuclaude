# TemuClaude UI/UX Master Plan

## The Goal

Make temuclaude.com the best-looking AI API product on the web. Not "good for an indie project" — best in class. The bar is Linear, Vercel, Anthropic. A dev lands on the page and thinks "this is legit" before they even read a word.

## Where We Are Now

**Strengths:**
- Warm Anthropic-inspired palette (cream #FAF8F5, ink #1A1816, orange #E25822) — distinctive, not generic
- Framer Motion animations with staggered reveals
- Working fusion pipeline card in hero (just shipped)
- Clear section structure: hero → features → how it works → models → benchmarks → pricing → footer
- Custom keyframes (shimmer, glowPulse, nodePulse, drawLine, dataFlow)
- Responsive, accessible (prefers-reduced-motion, semantic HTML)

**Weaknesses:**
- Inter font — the #1 tell of generic AI design. Every SaaS uses it.
- Feature cards are standard equal-height grid — no visual hierarchy or personality
- Pricing section is plain text with two buttons — no cards, no tiers, no visual weight
- No social proof (testimonials, usage stats, trust signals)
- No micro-interactions beyond basic card hover lift
- No background depth (just flat radial gradients)
- Footer is a basic link grid — no personality
- No scroll-triggered storytelling — sections just stack statically
- No grain/texture overlay — the page feels digitally flat
- Navigation is functional but not sticky/polished

## The Plan — 7 Phases

### Phase 1: Foundation (Typography + Texture)
**Time:** 2 hours
**Impact:** High — changes the entire feel of the site instantly

**1a. Typography upgrade**
- Replace Inter with a distinctive sans for body: **Source Sans 3** (warm, humanist, free on Google Fonts)
- Add a display serif for hero headline only: **Newsreader** (warm, editorial, matches Anthropic's serif personality)
- Keep JetBrains Mono for code blocks (already good)
- Font weight contrast: hero at 300, body at 400, labels at 600 — extreme contrast
- Hero headline: Newsreader 300 at 64px, line-height 1.05 — book-title presence
- Section headings: Newsreader 400 at 36-42px
- Body: Source Sans 3 400 at 16-17px, line-height 1.60 (Anthropic's relaxed reading rhythm)
- Labels/badges: Source Sans 3 600 at 12px, letter-spacing 0.04em

**1b. Grain texture overlay**
- Add a fixed-position SVG noise overlay at 3% opacity across the entire page
- Creates organic texture — the page feels like paper, not a screen
- One line of CSS, zero performance cost
- This is the single cheapest "premium feel" upgrade that exists

**1c. Ring shadow system (from Claude design system)**
- Replace current box-shadow drops with Anthropic's ring shadow pattern:
  `0px 0px 0px 1px rgba(26,24,22,0.08)` for cards
  `0px 0px 0px 1px rgba(26,24,22,0.16)` for hover states
- Whisper shadow for elevated cards: `rgba(26,24,22,0.05) 0px 4px 24px`
- This creates depth without the heavy "material design" shadow look

---

### Phase 2: Hero Perfection
**Time:** 1.5 hours
**Impact:** Critical — first impression, highest-traffic area

**2a. Polish the fusion pipeline card**
- Add subtle entrance animation: card fades in with slight upward motion (already have this)
- Add magnetic effect to the "Try Free" CTA button — it pulls toward the cursor slightly
- Add a subtle grain texture inside the terminal card for organic feel
- Animate the metadata numbers counting up (QA 9.4, $0.012) when they appear

**2b. Hero headline refinement**
- Split the headline into lines with staggered reveal:
  Line 1: "Frontier-quality AI." (fade in, 0ms)
  Line 2: "Fraction of the cost." (orange accent, fade in, 150ms)
  Line 3: "One API call." (fade in, 300ms)
- Use Newsreader serif at 300 weight — gives it editorial gravitas
- Add text-balance for the headline (prevents ugly line breaks)

**2c. Background depth**
- Replace flat radial gradients with a layered approach:
  Layer 1: Subtle dot grid pattern (SVG, very low opacity)
  Layer 2: Two radial gradients (warm orange glow + olive glow, existing colors)
  Layer 3: Grain overlay from Phase 1
- This creates atmospheric depth without being distracting

**2d. Code snippet upgrade**
- Add a subtle terminal title bar (red/yellow/green dots) to the curl example
- Add syntax highlighting with the accent colors already in the design system
- Add a copy button that appears on hover

---

### Phase 3: Feature Section → Bento Grid
**Time:** 3 hours
**Impact:** High — this is where devs decide if the product is real

**Current state:** 6 equal cards in a 3-column grid. Generic.

**New approach:** Bento grid (Apple-style modular layout)
- The "3 models answer, 1 wins" card stays large (2x2 space) — it's the hero feature
- "Math that can't lie" card: medium (1x2, tall)
- "Self-checking" card: small (1x1)
- "Radically cheap" card: wide (2x1) with animated price counters
- "25% profit → charity" card: medium (1x1) with the olive gradient
- "Open source" card: small (1x1)
- Staggered reveal on scroll (cards pop in one by one)
- Hover: card scales 1.02 + border shifts to accent-primary + whisper shadow deepens
- Each card gets a subtle icon in the brand color (not generic emoji)

**Source:** Search 21st.dev for "bento grid" and "feature section" components. Install the best-rated one as a base, customize colors to match the warm palette.

---

### Phase 4: Social Proof Section (NEW)
**Time:** 2 hours
**Impact:** High — trust is the #1 missing element for a new API product

**Current state:** No social proof anywhere. A dev landing here has no reason to trust this is real.

**Add a "trusted by builders" section between features and how-it-works:**

**4a. Usage stats strip**
- Three large numbers with labels:
  "472 tests passing" (green accent)
  "8 models fused" (orange accent)
  "$0.05/M cached" (amber accent)
- Numbers count up on scroll (animated, satisfying)
- Mono font for numbers (tabular-nums)

**4b. Testimonial cards (3 cards)**
- Pull from early users / beta testers (or write placeholder copy for now)
- Each card: quote, name, role, avatar
- Card design: Ivory background, ring shadow, 8px radius
- Subtle hover lift

**4c. GitHub stats badge**
- "MIT Licensed · Open Source · ★ X stars" badge
- Links to the repo
- Small but visible — devs care about this

**Source:** Search 21st.dev for "testimonial" and "stats" components.

---

### Phase 5: Pricing Section Overhaul
**Time:** 2.5 hours
**Impact:** Critical — this is where conversion happens

**Current state:** "$0.50 per million tokens. That's it." + two buttons. Too minimal — devs can't compare or understand what they get.

**New approach:** 3-tier pricing cards

**5a. Pricing cards**
- Free tier: $0 — 20 queries/day, no signup, community support
- Starter tier: $5/mo — 5,000 queries/mo, email support, priority routing
- Pro tier: $25/mo — 50,000 queries/mo, API key, usage dashboard, priority support
- "Starter" card highlighted with accent-primary border + "Popular" badge
- Monthly/annual toggle with smooth price animation
- Each card: price, query limit, key features list with checkmarks, CTA button

**5b. Token cost comparison strip**
- Below the cards: "vs. Claude API: $15/M tokens · vs. GPT-5.5: $30/M tokens · TemuClaude: $0.50/M"
- Visual bar chart showing the cost difference
- This is the "no-brainer" moment for devs

**5c. FAQ accordion**
- 5-6 common questions:
  "How are you this cheap?" / "Is quality really frontier-level?" / "Can I use this in production?"
  "What if I exceed my plan?" / "Do you store my data?" / "How does the fusion work?"
- Smooth accordion animation (height auto, not max-height hack)
- Use Framer Motion AnimatePresence for clean enter/exit

**Source:** Search 21st.dev for "pricing section" — there are 49 options. Look for one with 3-tier cards + toggle. "Pricing Interaction" (1k installs) or "Creative Pricing" (679 installs) look best.

---

### Phase 6: Navigation + Footer Polish
**Time:** 1.5 hours
**Impact:** Medium — but affects every page

**6a. Sticky navigation**
- Make navbar sticky with backdrop-blur when scrolling
- Add subtle border-bottom on scroll (transparent at top)
- Add a small "Try Free" CTA button in the nav (always visible)
- Add the Spark logo SVG (from logo-spark-orange.html) next to "TemuClaude" wordmark
- Mobile: hamburger menu with slide-in panel

**6b. Footer upgrade**
- Replace basic 4-column grid with a more designed layout:
  Top: Spark logo + tagline ("Small input. Frontier output.")
  Middle: 4 columns (Product, Resources, Connect, Legal) — keep existing links
  Bottom: "Built by Mohammad Saiful Haque · MIT Licensed" + GitHub link
  Add a subtle top border with the warm cream color
  Background: slightly darker cream (#F0EDE6) for visual separation

---

### Phase 7: Micro-Interactions + Polish
**Time:** 2 hours
**Impact:** Medium — the difference between "good" and "premium"

**7a. Magnetic CTA buttons**
- Primary CTA buttons (Try Free, Start Free) pull toward cursor slightly
- 0.3x pull factor, 300ms spring easing
- Subtle but satisfying — makes buttons feel alive

**7b. Scroll progress indicator**
- Thin 2px orange bar at the top of the page
- Fills as you scroll — gives a sense of progress through a long page
- Disappears when at top

**7c. Section entrance animations**
- Each section's heading fades in + slides up 12px on scroll
- Use Framer Motion useInView hook (already have StaggerReveal component)
- Consistent timing: 0.5s duration, cubic-bezier(0.25, 1, 0.5, 1) easing

**7d. Number animations**
- All stats/benchmarks/prices animate from 0 to their value on scroll
- Use Framer Motion's animate() with ease-out, 1.2s duration
- tabular-nums for clean digit alignment

**7e. Focus states**
- All interactive elements get visible focus rings (2px solid accent-primary, 2px offset)
- Keyboard navigation tested across the whole page
- This is an accessibility requirement, not just polish

---

## 21st.dev Integration

### Setup (5 minutes)
```bash
npm i -g @21st-dev/cli
21st login
```

### Component Search Plan (by phase)

| Phase | Search Terms | What to Install |
|-------|-------------|-----------------|
| 3 | "bento grid", "feature section" | 1 bento grid component |
| 4 | "testimonial", "stats counter" | 1 testimonial component + 1 stats component |
| 5 | "pricing section", "pricing cards" | 1 pricing component with 3 tiers |
| 6 | "navbar", "footer" | 1 navbar + 1 footer component |
| 7 | "magnetic button", "scroll progress" | 1 scroll progress component |

Total: ~7 component installs. Free tier allows 2/day, so this takes 4 days OR one Pro upgrade ($9/mo for unlimited). Recommend Pro for a week — do everything in one session.

### After installing each component:
1. Strip their design tokens (colors, fonts, radii)
2. Replace with TemuClaude's design system values
3. Verify it matches the warm Anthropic aesthetic
4. Test responsive behavior
5. Test reduced-motion fallback

---

## Design System Reference (from Anthropic Claude template)

These are the exact values to use across all components, from the popular-web-designs skill's claude.md template:

**Colors (already in your Tailwind config — verify these match):**
- Page bg: #FAF8F5 (parchment — you have this)
- Card surface: #FFFFFF → #FAF8F5 gradient (you have this)
- Primary text: #1A1816 (warm near-black — you have this)
- Secondary text: #5E5B56 (olive gray — you have this)
- Tertiary text: #8E8B85 (stone gray — you have this)
- Brand accent: #E25822 (terracotta — you have this, slightly more saturated than Anthropic's #c96442)
- Olive: #788C5D, Fig: #C46686, Amber: #E8B547 (you have all these)
- Border subtle: rgba(26,24,22,0.08) (you have this)
- Border default: rgba(26,24,22,0.16) (you have this)

**Typography (NEW — needs updating):**
- Display/Hero: Newsreader, weight 300, 64px, line-height 1.05
- Section headings: Newsreader, weight 400, 36-42px, line-height 1.20
- Body: Source Sans 3, weight 400, 16-17px, line-height 1.60
- Labels: Source Sans 3, weight 600, 12px, letter-spacing 0.04em
- Code: JetBrains Mono, weight 400, 15px (keep existing)

**Shadows (NEW — needs updating):**
- Card default: `0px 0px 0px 1px rgba(26,24,22,0.08)` (ring, not drop)
- Card hover: `0px 0px 0px 1px rgba(26,24,22,0.16)` + `rgba(26,24,22,0.05) 0px 4px 24px`
- Button hover: ring shadow with ring-warm color

**Border radius (verify):**
- Buttons: 8px (you have 8px — good)
- Cards: 16px (you have 16px — good)
- Hero containers: 24-32px (if applicable)

---

## What NOT to Do

From the ui-skills and elite-frontend-design constraints:

- ❌ No GSAP/ScrollTrigger — Framer Motion only (already in the project)
- ❌ No custom cursors — devs hate them, hurts usability
- ❌ No 3D/WebGL — performance cost not worth it for an API product
- ❌ No glassmorphism — doesn't work on light warm backgrounds
- ❌ No gradients as primary visual — the warm palette creates depth through tone, not gradients
- ❌ No animating layout properties (width, height, top, left) — only transform and opacity
- ❌ No animation over 200ms for interaction feedback (hover, click)
- ❌ No h-screen — use h-dvh for mobile correctness
- ❌ No pure black (#000) or pure white (#fff) — use tinted versions
- ❌ No cool blue-grays — every gray must have warm undertones
- ❌ No heavy drop shadows — ring shadows only
- ❌ No geometric/tech illustrations — organic, hand-drawn-feeling if any

---

## Execution Order

Day 1 (if Pro) or Days 1-2 (if free tier):
1. Install 21st.dev CLI + login
2. Phase 1: Foundation (typography + texture + shadows) — 2h
3. Phase 2: Hero perfection — 1.5h
4. Phase 3: Bento grid features (install 21st.dev component first) — 3h

Day 2 (if Pro) or Days 3-4 (if free tier):
5. Phase 4: Social proof section (install components) — 2h
6. Phase 5: Pricing overhaul (install component) — 2.5h
7. Phase 6: Nav + footer polish — 1.5h

Day 3 (if Pro) or Days 5-6 (if free tier):
8. Phase 7: Micro-interactions — 2h
9. Full QA pass: responsive, accessibility, reduced-motion, performance
10. Deploy to staging → review → production

**Total: ~14.5 hours of work. 3 days if Pro, 6 days if free tier.**

---

## Success Metrics

After implementation, verify:
- [ ] Lighthouse performance score > 90
- [ ] Lighthouse accessibility score > 95
- [ ] All animations respect prefers-reduced-motion
- [ ] Mobile layout tested at 375px, 768px, 1024px
- [ ] No layout shift (CLS < 0.1)
- [ ] Font loading doesn't block render (font-display: swap)
- [ ] Every interactive element has a visible focus state
- [ ] The page feels warm, premium, and distinctive — not "AI slop"

The end result: a dev lands on temuclaude.com and within 3 seconds thinks "this is a serious, well-built product." They see the fusion pipeline working, they see real pricing, they see social proof, they see polished typography and micro-interactions. They click Try Free.