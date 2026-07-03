# 3D Website Research — Agent Findings (Rounds 5-6)
## Complete Technical + Philosophical Analysis

## Key Findings from Both Agents

### Agent 1: Technical Analysis (20+ sites examined with console inspection)

**Critical discovery: Anthropic uses Webflow + GSAP + Lottie — NO WebGL at all.**
The most premium AI company (maker of Claude) achieves their polished feel through 2D animation, not 3D rendering. This validates our SVG + CSS + Framer Motion approach.

**Technology distribution from real sites:**
- ~40% use no-code/video approach (Framer, Webflow + pre-rendered video)
- ~60% use real WebGL (Three.js direct or via React Three Fiber)
- Anthropic: Webflow + GSAP + Lottie (NO WebGL)
- Linear: CSS animations only (NO WebGL)
- Cula: Framer + video (NO WebGL)

**Budget recommendation for Timuclaude:**
- Phase 1 (MVP): GSAP + SVG orchestration diagram + CSS animations — $5-10K, 2-3 weeks
- Phase 2 (Enhancement): Add Spline 3D hero element + 3D icons — +$3-8K, +1-2 weeks
- Phase 3 (Full 3D): R3F custom orchestration with particle data flow — +$15-30K, +4-6 weeks
- Recommended: Stay at Phase 2 ($8-18K total, 3-5 weeks)

**Spline is the easiest path to real 3D:**
- No-code visual editor (like Figma for 3D)
- Export as web component: `<spline-viewer url="...">`
- ~50KB viewer runtime
- Can be done by UI designers, not just developers

**React Three Fiber code for orchestration diagram (if we go full 3D):**
- AgentNode component with Float animation
- DataFlow component with particles traveling along bezier curves
- Warm materials: meshStandardMaterial with #D4A574, #C97B50, #E8D5C4
- Soft lighting: ambientLight #FFF8F0 + directionalLight #FFE4C4

### Agent 2: Design Philosophy (Awwwards SOTD analysis)

**Award winners use 2-color palettes (extreme restraint):**
- NRG: #FFC20E (warm yellow) + #261D26 (warm dark) — 2 colors
- Units: #0072E3 (blue) + #FFB200 (warm amber) — 2 colors
- IVRESS: #000000 (black) — 1 color

**Awwwards evaluation criteria:**
- Design: 40% | Usability: 30% | Creativity: 20% | Content: 10%
- SOTD winners score 7.0-7.5/10 (not perfect, but strong Design + Creativity)

**SOTD common patterns:**
1. Scroll-triggered 3D animations (dominant pattern)
2. Mouse/cursor interactions (all winners)
3. Microinteractions on every element
4. Loading as designed experience (not generic spinner)
5. Storytelling-driven (3D serves narrative)
6. Fullscreen immersive experiences
7. 2-color palettes (extreme restraint)
8. Dev Award component (code quality matters)

**3D shape personality mapping:**
- Soft/rounded → approachable, friendly, human
- Sharp/geometric → technical, precise, innovative (Together AI uses hexagon)
- Transparent/glassy → modern, premium, honest
- Matte/soft → warm, accessible

**Warm colors in 3D:**
- Warm colors advance visually (appear closer) — natural depth hierarchy
- Warm lighting creates emotional warmth
- 2-color palette lets 3D form/texture/lighting do the heavy lifting

**2026 trend: 3D as "design material" not technical showcase**
- Figma Config 2026: "Code is material, just like images, vectors and design layers"
- Line between 3D design and 3D development is blurring
- Evolution: technical showcase → brand differentiation → narrative tool → design material

**Common mistakes to avoid:**
1. 3D for 3D's sake (must serve narrative)
2. Overcomplicated scenes (restraint wins)
3. Ignoring mobile
4. Poor performance (>3s load = users leave)
5. No loading state
6. Inaccessible 3D (no 2D fallback)
7. Ignoring prefers-reduced-motion
8. Text on busy 3D backgrounds
9. Disorienting camera movements
10. No clear navigation

**How to brief a developer for 3D:**
1. Brand personality & narrative (what story?)
2. 3D scope (hero only? full scroll?)
3. Color palette & materials (HEX values, matte/glossy/transparent)
4. Interaction specs (scroll, hover, cursor, click)
5. Technical requirements (devices, performance budget, fallback)
6. Content & copy (ready before building)
7. Reference sites (3-5 examples with specific likes)
8. Deliverables & timeline

## Impact on Timuclaude Plan

These findings reinforce our existing approach:

1. **SVG + CSS + Framer Motion is correct** — Anthropic (the most premium AI brand) uses GSAP + Lottie, not WebGL
2. **2-color palette validated** — our warm ivory (#FAF8F5) + clay (#D97757) is exactly the restraint award winners use
3. **Warm colors advance in 3D** — our clay accent will naturally pop against the ivory background
4. **Optional Spline for Phase 2** — if we want real 3D later, Spline is the easiest path (no-code, ~50KB)
5. **Progressive enhancement required** — always provide 2D fallback
6. **prefers-reduced-motion** — must respect this (already in our plan)
7. **Loading as design** — skeleton screens with shimmer (already in our plan)
8. **Performance budget** — <200KB initial bundle, <1.5s LCP (already in our plan)