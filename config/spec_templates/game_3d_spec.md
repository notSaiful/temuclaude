# Interactive Demo: {{ PROJECT_NAME }}

## Core Mechanic
{{ RAW_PROMPT }}

## Technical Stack
- Single HTML file (no build step)
- Three.js + Cannon-ES physics engine
- Vite dev server (hot reload during development)
- Procedural texture generation (no external assets)

## Visual Design
- Theme: Dark cinematic with glowing accents
- Color palette: {{ COLORS }}
- Typography: {{ FONTS }}
- UI panels: Top-left controls, top-right stats, bottom-center instructions
- Crosshair in center for FPS mode

## Game Features (Required)
- First-person camera with WASD + mouse look
- Block placement and destruction (left/right click)
- Inventory hotbar (1-9 number keys)
- Chunk loading/unloading (performance)
- Day/night cycle
- Basic lighting (ambient + directional + block lighting)

## Physics Parameters (Exposed as Controls)
- Gravity: [range 0.1-2.0, default 1.0]
- Movement speed: [range 1-10, default 5]
- Jump force: [range 1-20, default 8]
- Render distance: [range 2-16 chunks, default 6]

## Interaction
- Mouse: Look around, left-click destroy, right-click place
- Keyboard: WASD movement, Space jump, Shift sprint, 1-9 hotbar
- Touch: Virtual joystick for mobile (left=move, right=look, tap=action)

## Performance Targets
- 60fps on 5-year-old laptop with render distance 6
- <100KB total (gzipped, excluding Three.js CDN)
- No memory leaks over 10min session
- Chunk load time < 100ms

## Quality Bar
{{ QUALITY_BAR }}

## Keywords Matched
{{ KEYWORDS_MATCHED }}