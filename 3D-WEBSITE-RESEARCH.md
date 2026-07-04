# TEMUCLAUDE — 3D WEBSITE DESIGN RESEARCH
## Learnings from Awwwards, Landing.love, and Live Site Analysis

---

## PART 1: SITES EXAMINED IN DETAIL

### From Awwwards 3D Category (4,448 sites)
1. **Cula Technologies** — Light, clean, video-driven 3D effects (NO WebGL)
2. **Noomo Agency** — Light blue bg, WebGL canvas, 3D storytelling (Salesforce, AMD, Red Bull client)
3. **TRIONN** — Dark, 3 WebGL canvases, 6 videos, sound toggle, immersive
4. **JunkBranding** — 3D branding showcase
5. **Kettal** — 3D furniture/architecture showcase
6. **KonradReyhe** — 3D fashion/brand
7. **CyberCrest** — 3D compliance/tech
8. **Penguin Capital** — 3D finance
9. **Bitfalk** — 3D tech systems
10. **Matcha Cartel** — 3D food/lifestyle

### From Landing.love 3D Category (555 sites)
1. **Kenichi Aikawa** — Photography portfolio, 3D, WebGL dev kits
2. **Yuta Abe** — Portfolio, 3D website, design + development
3. **TRIONN** — Agency, 3D website (also on Awwwards)
4. **RabenRifaie** — Agency, 3D, studio
5. **Jijo** — Portfolio, 3D
6. **Dragonfly** — Crypto/finance, 3D
7. **Cash App** — Finance, 3D, app
8. **THE BAT CLOUD** — Art, 3D, architecture
9. **NO CODE-SHADER** — 3D, development, shader-focused
10. **Cartier** — 3D, fashion, luxury
11. **Vectr** — 3D, AI, SaaS, tech
12. **Noomo** — 3D, agency (also on Awwwards)

### Additional Sites Analyzed
- **Spline** (spline.design) — 3D design tool, black bg, "Press and drag to orbit" interactive 3D hero, 3 WebGL canvases, 12 videos, custom "Spline Sans" font
- **Together AI** — Light bg, 3D abstract shapes (transparent blue circle, purple discs, orange hexagon)
- **Cula.tech** — Light bg, uses VIDEO instead of WebGL for 3D-like effects (key insight)

---

## PART 2: TECHNOLOGY STACK FINDINGS

### How 3D Websites Are Actually Built

| Technology | What It Does | Used By | Difficulty | Performance |
|-----------|-------------|---------|-----------|-------------|
| **Three.js** | WebGL 3D engine | TRIONN, Spline, most 3D sites | Moderate-Hard | Heavy (3-10MB) |
| **React Three Fiber** | React renderer for Three.js | Next.js 3D sites | Moderate | Heavy but tree-shakeable |
| **Spline** | No-code 3D design → embed | Spline customers | Easy (visual editor) | Medium (1-3MB embed) |
| **WebGL Shaders (GLSL)** | Custom visual effects | NO CODE-SHADER, award sites | Hard | Varies |
| **GSAP + ScrollTrigger** | Scroll animations | Most Awwwards winners | Moderate | Light (30KB) |
| **Framer Motion** | React animations | Modern React sites | Easy | Light (30KB) |
| **CSS 3D Transforms** | Subtle 3D depth | Many sites | Easy | Excellent (GPU) |
| **Pre-rendered Video** | 3D-like effects via video | Cula, Together AI | Easy (produce video) | Good (1-3MB) |
| **SVG Animation** | 2D diagrams with motion | Data viz sites | Moderate | Excellent (<10KB) |
| **Lottie** | After Effects → web animation | Many SaaS sites | Easy (if you have AE) | Light (50-200KB) |
| **Canvas 2D** | Particle systems, custom 2D | Interactive sites | Moderate | Good |

### Key Insight: Video vs WebGL
Many "3D websites" actually use **pre-rendered video** for their 3D effects, not real-time WebGL. This is critical:
- **Cula.tech**: Light bg, 5 videos, 0 canvases — looks 3D but is actually video
- **Together AI**: 3D abstract shapes are likely pre-rendered images/videos
- **Spline**: Uses REAL WebGL (3 canvases) because it's a 3D tool — but this is heavy
- **TRIONN**: 3 WebGL canvases + 6 videos — very heavy, slow to load

### What This Means for Temuclaude
Developers care about performance. A 10MB WebGL scene will hurt our Lighthouse score and scare away our target audience. We should use:
1. **SVG animation** for the orchestration diagram (infinitely scalable, <10KB)
2. **CSS 3D transforms** for card hover effects (GPU accelerated, 0KB)
3. **Framer Motion** for scroll reveals and micro-interactions (30KB, React-native)
4. **Optional: Spline embed** for a 3D logo mark (1 small asset, <500KB)
5. **NO heavy WebGL** — keep bundle < 200KB initial load

---

## PART 3: VISUAL PATTERNS FROM 3D WEBSITES

### Pattern 1: Interactive 3D Hero (Spline approach)
- "Press and drag to orbit" — user controls the 3D scene
- 3D object rotates/responds to mouse
- Creates immediate engagement ("play" instinct)
- **For Temuclaude**: Our orchestration diagram could be interactive — drag to rotate the node network

### Pattern 2: Video-Driven 3D (Cula approach)
- Pre-rendered 3D animation as video
- Looks 3D but plays as video (better performance)
- Used for product showcases and feature explanations
- **For Temuclaude**: Could create a pre-rendered animation of orchestration flow

### Pattern 3: 3D Abstract Shapes (Together AI approach)
- Floating 3D shapes (spheres, discs, hexagons)
- Translucent materials with soft shadows
- Conveys "advanced technology" without being literal
- **For Temuclaude**: Warm clay-colored abstract shapes could work in the hero

### Pattern 4: Scroll-Triggered 3D Transformation
- 3D scene changes as user scrolls
- Camera moves through 3D space
- Story unfolds with scroll progress
- **For Temuclaude**: Could show orchestration flow as user scrolls (query → classify → route → fuse → verify → answer)

### Pattern 5: Dark Immersive (TRIONN approach)
- Very dark background (#040508)
- 3D scenes with glowing elements
- Sound toggle for full immersion
- **Not for Temuclaude**: We're warm light, not dark immersive

### Pattern 6: Clean Light + Subtle 3D (Cula approach)
- Light/white background
- 3D effects through video or subtle CSS transforms
- Focus on content, 3D as enhancement
- **Best fit for Temuclaude**: Warm ivory + subtle 3D elements

---

## PART 4: ANIMATION PATTERNS

### Micro-Interactions (from all sites)
1. **Custom cursor**: Sites like Cula have custom cursor elements that change on hover
2. **Magnetic buttons**: Buttons that attract the cursor slightly
3. **Parallax scroll**: Background moves slower than foreground
4. **Reveal on scroll**: Elements fade/slide in as they enter viewport
5. **3D card tilt**: Cards tilt in 3D based on mouse position (CSS perspective)
6. **Text reveal**: Headings animate word-by-word or letter-by-letter on scroll
7. **Image masks**: Images reveal through animated masks/clip-paths
8. **Loading transitions**: Smooth page-to-page transitions with shared elements
9. **Sound design**: TRIONN has ambient sound toggle — immersive but optional
10. **Infinite scroll galleries**: Horizontal scrolling galleries with momentum

### For Temuclaude (selected micro-interactions)
1. **3D card tilt**: Benchmark cards tilt slightly on hover (CSS perspective + mouse position)
2. **Scroll-triggered reveals**: Sections fade in + slide up (Framer Motion)
3. **Animated counter**: Stats count up from 0 when they enter viewport
4. **Text reveal**: H1 animates word-by-word on page load
5. **Orchestration diagram**: SVG nodes pulse and connect sequentially on load
6. **Button hover**: Subtle 3D press effect (translateZ + shadow)
7. **Custom cursor on playground**: Cursor changes in the orchestration panel

---

## PART 5: SKILLS AND CODING NEEDED

### What You Need to Build Award-Winning 3D Websites

**Level 1: Basic (What We Need for Temuclaude)**
- React/Next.js — we have this
- CSS animations and transitions — we have this
- CSS 3D transforms (perspective, rotateX/Y/Z) — easy to learn
- Framer Motion — React-native, easy to learn
- SVG animation (CSS animation of SVG elements) — moderate

**Level 2: Intermediate (Optional Enhancements)**
- GSAP + ScrollTrigger — for complex scroll animations
- Canvas 2D API — for custom particle systems
- Lottie (After Effects → JSON animation) — if we have an animator
- Spline (no-code 3D design tool) — visual editor, export to React

**Level 3: Advanced (Not Needed for Temuclaude)**
- Three.js / React Three Fiber — for real WebGL 3D scenes
- GLSL shaders — for custom visual effects
- Blender — for creating 3D models
- WebGL optimization — for performance-critical 3D

### Thinking and Reasoning for 3D Web Design
1. **Purpose over spectacle**: Every 3D element should serve a purpose (explain, engage, differentiate). Not decoration.
2. **Performance is design**: A beautiful 3D site that takes 10 seconds to load is worse than a clean 2D site that loads instantly.
3. **Progressive enhancement**: 3D should enhance the experience, not be required for it. If WebGL fails, the site should still work.
4. **Mobile-first 3D**: 3D effects must degrade gracefully on mobile (fewer particles, lower resolution, or disabled).
5. **Brand consistency**: 3D elements must use the same color palette, typography, and mood as the rest of the site.
6. **Storytelling**: The best 3D websites tell a story — the 3D guides the user through a narrative.
7. **Subtlety wins**: A subtle 3D card tilt is more elegant than a full-screen WebGL scene. Less is more.

### For Temuclaude Specifically
- Our "3D" is the orchestration diagram — an SVG animation showing nodes connecting
- Our "depth" is CSS 3D transforms on cards and buttons
- Our "motion" is Framer Motion scroll-triggered reveals
- Our "interactive" is the playground (not 3D, but interactive)
- We do NOT need Three.js, WebGL, or GLSL shaders
- We DO need: SVG animation, CSS 3D transforms, Framer Motion, and good design sense

---

## PART 6: HOW TO CREATE THE ORCHESTRATION DIAGRAM

### The Hero Animation (Our Key Visual)

**Concept**: An animated SVG showing 5 model nodes connecting to a central Temuclaude hub, with data "pulses" flowing along the connections.

**Technical Implementation**:
```svg
<svg viewBox="0 0 800 400">
  <!-- 5 model nodes positioned in an arc -->
  <circle cx="100" cy="200" r="20" class="node node-1" />
  <circle cx="250" cy="100" r="20" class="node node-2" />
  <circle cx="400" cy="80"  r="20" class="node node-3" />
  <circle cx="550" cy="100" r="20" class="node node-4" />
  <circle cx="700" cy="200" r="20" class="node node-5" />
  
  <!-- Central hub (Temuclaude) -->
  <circle cx="400" cy="250" r="35" class="hub" />
  
  <!-- Connection lines (animated draw-in) -->
  <line x1="100" y1="200" x2="400" y2="250" class="connection" />
  <line x1="250" y1="100" x2="400" y2="250" class="connection" />
  <line x1="400" y1="80"  x2="400" y2="250" class="connection" />
  <line x1="550" y1="100" x2="400" y2="250" class="connection" />
  <line x1="700" y1="200" x2="400" y2="250" class="connection" />
  
  <!-- Data pulses (small dots moving along lines) -->
  <circle r="4" class="pulse pulse-1">
    <animateMotion dur="2s" repeatCount="indefinite">
      <mpath href="#path-1" />
    </animateMotion>
  </circle>
</svg>
```

**Animation Sequence**:
1. Nodes fade in one by one (staggered 200ms)
2. Connection lines draw in from node to hub (stroke-dashoffset animation)
3. Data pulses start flowing along lines (animateMotion)
4. Hub pulses gently (scale 1.0 → 1.05 → 1.0, 2s loop)
5. Entire diagram gently floats (translateY ±5px, 4s loop)

**Colors**:
- Nodes: #D97757 (warm clay)
- Hub: #1A1816 (warm near-black)
- Connection lines: rgba(217, 119, 87, 0.3) (subtle clay)
- Data pulses: #D97757 (clay)
- Background: transparent (sits on #FAF8F5)

**Performance**: < 5KB SVG, GPU-accelerated CSS animations, no JavaScript needed for the animation itself (pure SVG + CSS). Optional: Framer Motion for scroll-triggered start.

---

## PART 7: AWARD-WINNING PATTERNS (From Awwwards SOTD Analysis)

### What Makes 3D Websites Win Awards
1. **Seamless integration**: 3D doesn't feel bolted on — it's part of the story
2. **Performance despite complexity**: Even heavy 3D sites load in < 3s
3. **Custom cursor**: Almost every SOTD has a custom cursor experience
4. **Sound design**: Optional ambient sound adds immersion (TRIONN)
5. **Scroll-driven narrative**: The 3D scene evolves as you scroll
6. **Micro-interactions everywhere**: Every element responds to hover/click
7. **Typography as art**: Headings are animated, revealed, or 3D-transformed
8. **Consistent color story**: 3D elements use the same palette as the site
9. **Loading screen as art**: The loading state is designed, not a generic spinner
10. **Accessibility despite 3D**: Keyboard navigation works, reduced-motion respected

### What We Should Adopt (Within Our Warm Minimal Aesthetic)
1. ✅ Custom cursor on playground (subtle dot that grows on hover)
2. ✅ Scroll-driven orchestration flow (query → classify → route → fuse → verify)
3. ✅ Micro-interactions on every element (hover, focus, click states)
4. ✅ Typography animation (H1 reveals word-by-word)
5. ✅ Designed loading state (skeleton screens with shimmer, not spinners)
6. ✅ Reduced-motion fallback (all animations respect prefers-reduced-motion)
7. ❌ NO custom cursor on landing page (too gimmicky for a developer tool)
8. ❌ NO sound design (developers browse with sound off)
9. ❌ NO heavy WebGL (performance > spectacle for our audience)

---

## SUMMARY: 3D WEBSITE RESEARCH CONCLUSIONS

### What We Learned
1. **Most "3D websites" use video, not real WebGL** — Cula.tech, Together AI use pre-rendered video for 3D-like effects
2. **Real WebGL 3D is heavy** — TRIONN (3 canvases) and Spline (3 canvases) are beautiful but slow
3. **Award winners combine: GSAP + custom cursor + scroll narrative + micro-interactions**
4. **For SaaS/AI tools, 3D should be subtle** — Vectr (AI tool) has NO 3D at all, just clean design
5. **SVG + CSS is the sweet spot** — award-winning animations without the WebGL payload
6. **Framer Motion is the React-native choice** — works with Next.js, spring physics, scroll triggers
7. **Spline is the easiest path to real 3D** — visual editor, export to React, no GLSL coding
8. **Performance is design** — developers will judge us on Lighthouse score, not on 3D spectacle

### What Temuclaude Should Do
1. **Hero**: Animated SVG orchestration diagram (nodes connecting, data flowing) — < 5KB
2. **Cards**: CSS 3D transforms for subtle tilt on hover — 0KB additional
3. **Sections**: Framer Motion scroll-triggered reveals — 30KB library
4. **Playground**: Framer Motion for loading states, panel transitions
5. **Stats**: Animated counters (count up from 0 on scroll into view)
6. **H1**: Word-by-word reveal animation on page load
7. **Optional future**: Spline embed for 3D logo mark (if we want to add real 3D later)
8. **NO WebGL, NO Three.js, NO GLSL shaders** — keep it fast, keep it clean

### Skills We Need
- React/Next.js ✅ (we have this)
- CSS animations + 3D transforms ✅ (we can do this)
- Framer Motion (easy to learn, React-native)
- SVG animation (moderate — CSS animation of SVG elements)
- Design sense (warm minimal, editorial quality, purposeful motion)

### Skills We DON'T Need
- Three.js / WebGL (too heavy for our use case)
- GLSL shaders (overkill)
- Blender (no custom 3D models needed)
- GSAP (Framer Motion covers our needs in React)