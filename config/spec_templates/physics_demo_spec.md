# Interactive Demo: {{ PROJECT_NAME }}

## Core Mechanic
{{ RAW_PROMPT }}

## Technical Stack
- Single HTML file (no build step)
- Raw WebGL2 (no Three.js, no libraries, no imports)
- Custom physics: Verlet integration + mass-spring system
- Texture generation: Offscreen canvas → procedural
- No external dependencies

## Visual Design
- Theme: Dark cinematic / Glassmorphism
- Color palette: {{ COLORS }}
- Typography: {{ FONTS }}
- UI panels: Left side controls panel, right side live stats
- Full-screen simulation canvas

## Physics Parameters (Exposed as Controls)
- Stiffness: [range 0.1-1.0, default 0.5]
- Damping: [range 0.0-0.1, default 0.02]
- Wind strength: [range 0-5, default 1.5]
- Turbulence: [range 0-3, default 0.8]
- Gravity: [range 0-2, default 0.98]
- Constraint type: Structural, Bend, Diagonal (checkboxes)

## Interaction
- Mouse: Grab/drag particles, release to let physics take over
- Keyboard: R to reset, Space to pause, 1-5 presets
- Touch: Pinch to zoom, drag to interact

## WebGL2 Requirements
- Custom vertex/fragment shaders
- Offscreen canvas for texture generation
- RequestAnimationFrame loop with delta time
- Proper context loss handling
- Viewport resize handling

## Performance Targets
- 60fps on 5-year-old laptop
- <100KB total (gzipped)
- No memory leaks over 10min
- Particle count: 5000+ without frame drops

## Quality Bar
{{ QUALITY_BAR }}

## Keywords Matched
{{ KEYWORDS_MATCHED }}