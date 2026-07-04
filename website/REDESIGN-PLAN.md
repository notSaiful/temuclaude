# TEMUCLAUDE — HERO & DESIGN REDESIGN PLAN
## Based on direct CSS extraction from Stripe, Linear, Anthropic, Framer

---

## KEY FINDINGS FROM LIVE SITES

### Typography (The biggest issue)
- **Stripe**: H1 38px, weight 300 (LIGHT!), letter-spacing -0.76px
- **Linear**: H1 64px, weight 510 (variable font), letter-spacing -1.4px
- **Anthropic**: Custom "Anthropic Sans" font, editorial layout
- **Framer**: EB Garamond serif + Geist sans, H1 at 60% opacity (soft, not loud)

**OUR PROBLEM**: Our H1 is 36-56px, weight 600 (SEMIBOLD). Too heavy. Too loud. 
**FIX**: H1 should be weight 300-400, larger size, tighter letter-spacing. Premium = light, not bold.

### Stat Counters
- **Stripe**: 48px, weight 300 (LIGHT), letter-spacing -0.96px. No animation — just large, clean numbers.
- **Linear**: No visible stat counters on homepage.

**OUR PROBLEM**: Our counters show "0" and animate up. This looks cheap when they don't trigger.
**FIX**: Either fix the counter to trigger reliably, OR follow Stripe's approach — just show the number, no animation. Large, light, clean.

### Hero Animation
- **Stripe**: No flashy animation. Clean fade-in. The premium feel comes from typography and spacing, not motion.
- **Linear**: Product screenshot as hero (their app UI). No orchestration diagram. The hero IS the product.
- **Anthropic**: Editorial layout, text-driven, no diagram. Warm background, clean typography.
- **Framer**: Subtle gradient backgrounds, soft text opacity.

**OUR PROBLEM**: Our SVG orchestration diagram is too basic — circles and lines that look like a school project.
**FIX**: Replace with either:
  A) A gradient mesh background (CSS only, no SVG) — like Framer/Vercel
  B) A clean product screenshot of the playground
  C) A more sophisticated animated visual using CSS gradients and blur effects

### Card Design
- **Stripe**: No traditional cards. Uses full-width sections with subtle dividers.
- **Linear**: Uses "FIG 0.2" editorial annotations. Product screenshots. No card boxes.
- **Anthropic**: Card-like sections with warm background, subtle borders, lots of padding.

**OUR PROBLEM**: Our cards are white boxes with thin borders. Basic.
**FIX**: Add depth — subtle gradient backgrounds, layered shadows, hover lift with smooth easing. Follow Anthropic's warm card approach.

### Section Spacing
- **Stripe**: Very generous. Sections breathe. 80-120px padding.
- **Linear**: Even more generous. Full-height sections.
- **Anthropic**: Editorial spacing. Text gets room to breathe.

**OUR PROBLEM**: Our sections are too tight (py-20 = 80px). 
**FIX**: Increase to py-24 (96px) or py-32 (128px) for hero and key sections.

### Color Treatment
- **Stripe**: Dark text on light bg. Green accent (rgb(129,184,26)). Very minimal color.
- **Linear**: Dark theme (rgb(8,9,10)). White text. No accent color visible.
- **Anthropic**: Warm ivory (#FAF9F5). Dark text. Clay/sage accents. Very warm.
- **Framer**: Dark gradient. Soft white text at 60% opacity.

**OUR PROBLEM**: Our clay accent (#D97757) is used too sparingly. 
**FIX**: Use clay more confidently — in the H1 accent word, in card hover states, in section dividers, in the CTA button.

---

## REDESIGN SPECIFICATIONS

### Hero Section (Complete Redesign)
1. **Background**: Warm ivory with a subtle radial gradient (clay tint fading to transparent at edges). No SVG diagram in hero.
2. **H1**: 64px (desktop), weight 300, letter-spacing -1.4px, color #1A1816. Accent word "superior" in clay #D97757. Three lines, generous line-height (1.1).
3. **Subtext**: 18px, weight 400, color #5E5B56, max-width 540px, line-height 1.5.
4. **CTAs**: Primary (dark bg, light text, no border), Secondary (transparent, thin border, clay hover). Both 44px height, 16px font, px-6 py-2.5.
5. **Install command**: Dark bg, mono font, subtle. Below CTAs. Not prominent.
6. **Animation**: 
   - H1: word-by-word fade in + 8px slide up, staggered 100ms, ease [0.25,1,0.5,1], duration 0.6s
   - Subtext: fade in + slide up, delay 0.4s
   - CTAs: fade in + slide up, delay 0.6s
   - Install: fade in, delay 0.8s
   - NO orchestration diagram in hero (move it to a dedicated section below)
7. **Spacing**: pt-40 pb-32 (generous top space for nav, generous bottom breathing room)

### Orchestration Section (New — replaces diagram in hero)
1. **Full-width section** with warm secondary background (#F0EDE6)
2. **Heading**: "Five minds. One answer." — 40px, weight 400, letter-spacing -0.88px
3. **Visual**: Animated CSS-based orchestration visualization (NOT basic SVG circles):
   - 5 gradient circles (clay tones) with backdrop-filter blur
   - Connected by animated lines (CSS animation, not SVG)
   - Data pulses flowing along lines (CSS @keyframes, not SVG animateMotion)
   - Central hub with subtle glow (box-shadow, not SVG)
   - All GPU-accelerated (transform, opacity only)
4. **Below visual**: 3-step explanation cards with more depth

### Stats Section (Redesign)
1. **No animated counters** — follow Stripe's approach
2. Large numbers: 48px, weight 300, letter-spacing -0.96px, color #D97757
3. Labels: 14px, weight 400, color #5E5B56
4. Generous spacing between stats (gap-12)
5. Subtle divider above and below (1px border at 8% opacity)

### Model Presentation (Landing page "Powered by" section)
1. **Replace plain text with dots** → use a horizontal scroll of model "pills"
2. Each pill: model name in medium weight, subtle bg, clay hover
3. Or: a clean grid of 5 model cards with:
   - Model name (18px, weight 500)
   - Role label (12px, uppercase, muted)
   - Subtle gradient background (not flat white)
   - No border — use shadow instead for depth
   - Hover: slight lift (-translate-y-1), deeper shadow, clay-tinted glow

### Card Design (All cards across site)
1. **Background**: subtle gradient — linear-gradient(135deg, #FFFFFF, #FAF8F5) instead of flat #FFFFFF
2. **Border**: 1px solid rgba(26,24,22,0.06) — barely visible
3. **Shadow**: 0 1px 3px rgba(26,24,22,0.04) — more subtle than current
4. **Hover shadow**: 0 4px 16px rgba(26,24,22,0.08) — noticeable but soft
5. **Hover transform**: -translate-y-0.5 (2px lift, not 4px)
6. **Border-radius**: 16px (larger, more modern)
7. **Transition**: all 0.3s cubic-bezier(0.25,1,0.5,1) — slower, smoother

### Section Spacing
1. Hero: pt-40 pb-32 (160px top, 128px bottom)
2. Regular sections: py-24 (96px) — increased from py-20 (80px)
3. Stats bar: py-12 (48px) — generous
4. Between sections: no artificial dividers — use background color alternation

### Easing & Duration
- All transitions: 0.3s cubic-bezier(0.25,1,0.5,1) — consistent
- Scroll reveals: 0.6s with same easing
- Stagger delays: 80ms between items
- No bounce, no elastic — smooth spring only