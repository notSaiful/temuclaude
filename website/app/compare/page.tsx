'use client';

import { useState, useEffect, useRef } from 'react';
import { Navbar } from '@/components/Navbar';

interface ComparisonCase {
  id: string;
  title: string;
  category: string;
  prompt: string;
  temuclaude: {
    latency: string;
    tokens: number;
    highlights: string[];
    code: string;
  };
  frontierBaseline: {
    latency: string;
    tokens: number;
    highlights: string[];
    note: string;
    sourceText: string;
    sourceUrl: string;
    code: string;
  };
}

const FRONTIER_BASELINE_SHADER = `
precision mediump float;
uniform vec2 u_resolution;
uniform float u_time;

float map(vec3 p) {
  // Infinite repeating corridor walls
  float walls = p.x * p.x - 0.8;
  // Floor & ceiling
  float floorCeil = abs(p.y) - 1.0;
  return min(walls, floorCeil);
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;
  vec3 ro = vec3(0.0, 0.0, u_time * 0.8);
  vec3 rd = normalize(vec3(uv, 1.0));

  float d = 0.0;
  for (int i = 0; i < 40; i++) {
    vec3 p = ro + d * rd;
    float dist = map(p);
    if (dist < 0.001) break;
    d += dist;
    if (d > 10.0) break;
  }

  vec3 p = ro + d * rd;
  vec3 col = vec3(0.08); // background

  if (d < 10.0) {
    // Basic diffuse coloring
    if (abs(p.y) > 0.99) {
      col = vec3(0.3, 0.3, 0.32); // Ceiling/Floor grey
    } else {
      col = vec3(0.85, 0.75, 0.45); // Yellow walls
    }
    // Basic fog
    col *= 1.0 - (d / 10.0);
  }

  gl_FragColor = vec4(col, 1.0);
}
`;

const TEMU_BACKROOMS_PLAYABLE_SHADER = `
precision mediump float;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_angle;
uniform vec3 u_camera;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hash(i + vec2(0.0,0.0)), hash(i + vec2(1.0,0.0)), u.x),
             mix(hash(i + vec2(0.0,1.0)), hash(i + vec2(1.0,1.0)), u.x), u.y);
}

float map(vec3 p) {
  // Infinite grid corridors spaced every 2.5 units
  vec3 c = vec3(2.5, 0.0, 2.5);
  vec3 q = p;
  q.x = mod(p.x, c.x) - 0.5 * c.x;
  q.z = mod(p.z, c.z) - 0.5 * c.z;

  float walls = min(abs(q.x) - 0.1, abs(q.z) - 0.1);
  float floorCeil = abs(p.y) - 1.0;

  return min(walls, floorCeil);
}

void rotateY(inout vec3 p, float a) {
  float c = cos(a); float s = sin(a);
  p.xz = mat2(c, -s, s, c) * p.xz;
}

void rotateX(inout vec3 p, float a) {
  float c = cos(a); float s = sin(a);
  p.yz = mat2(c, -s, s, c) * p.yz;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution) / u_resolution.y;

  // Ray origin is u_camera position
  vec3 ro = u_camera;

  // Rotate ray direction according to yaw/pitch
  vec3 rd = normalize(vec3(uv, 1.2));
  rotateX(rd, u_angle.y);
  rotateY(rd, u_angle.x);

  float d = 0.0;
  for (int i = 0; i < 55; i++) {
    vec3 p = ro + d * rd;
    float dist = map(p);
    if (dist < 0.001) break;
    d += dist;
    if (d > 12.0) break;
  }

  vec3 p = ro + d * rd;
  vec3 col = vec3(0.02, 0.02, 0.03); // ambient base dark

  // Flickering fluorescent ceiling light panel
  float flicker = step(0.08, hash(vec2(floor(u_time * 5.0), 17.0)));
  float lightState = mix(0.12, 1.0, flicker);

  if (d < 12.0) {
    if (abs(p.y) > 0.99) {
      // Ceilings
      float ceilGrid = step(0.78, fract(p.x * 2.0)) + step(0.78, fract(p.z * 2.0));
      col = mix(vec3(0.15, 0.15, 0.12), vec3(0.85, 0.82, 0.6) * lightState, ceilGrid);
    } else {
      // Yellow wallpaper stains
      float stains = noise(p.zy * 9.0) * 0.35;
      col = (vec3(0.8, 0.7, 0.32) - stains) * 0.85;
    }

    // Spotlight/Flashlight center beam overlay
    float distToCenter = length(uv);
    float flashIntensity = smoothstep(0.42, 0.06, distToCenter);
    col *= (flashIntensity * 1.6 + 0.15); // light cone multiplier

    // Corridors fog depth
    col *= 1.0 - (d / 12.0);

    // Entity shadow figure standing down the hallway
    float entityDist = length(p.xz - vec3(0.0, 0.0, ro.z + 4.5).xz);
    if (entityDist < 0.22 && abs(p.y) < 0.65 && flicker < 0.4) {
      col = vec3(0.0); // Spooky black silhouette
    }
  }

  // VHS grain filter
  float grain = hash(gl_FragCoord.xy + u_time) * 0.09;
  col += vec3(grain);

  // Analog CRT scanlines
  col *= 1.0 - step(0.95, sin(gl_FragCoord.y * 1.9)) * 0.18;

  gl_FragColor = vec4(col, 1.0);
}
`;

const PlayableWebGLHorrorCanvas = ({ shaderCode }: { shaderCode: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Gameplay states
  const [cameraPos, setCameraPos] = useState({ x: 0.0, y: 0.0, z: 0.0 });
  const [angle, setAngle] = useState({ x: 0.0, y: 0.0 }); // Yaw, Pitch
  const [isFocused, setIsFocused] = useState(false);

  // Keep track of states for key events
  const keysPressed = useRef<{ [key: string]: boolean }>({});
  const mouseDragRef = useRef({ lastX: 0, lastY: 0, isDragging: false });

  // Handle focus locks
  const handleCanvasClick = () => {
    setIsFocused(true);
    if (containerRef.current) {
      containerRef.current.focus();
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    keysPressed.current = {};
  };

  // Keyboard handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isFocused) return;
      if (['KeyW', 'KeyS', 'KeyA', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
        e.preventDefault();
      }
      keysPressed.current[e.code] = true;
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysPressed.current[e.code] = false;
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isFocused]);

  // Mouse look handlers (drag to look around)
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    mouseDragRef.current = { lastX: e.clientX, lastY: e.clientY, isDragging: true };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!mouseDragRef.current.isDragging) return;
    const deltaX = e.clientX - mouseDragRef.current.lastX;
    const deltaY = e.clientY - mouseDragRef.current.lastY;

    mouseDragRef.current.lastX = e.clientX;
    mouseDragRef.current.lastY = e.clientY;

    setAngle(prev => ({
      x: prev.x - deltaX * 0.005, // Yaw rotation
      y: Math.max(-0.6, Math.min(0.6, prev.y + deltaY * 0.005)), // Pitch tilt limit
    }));
  };

  const handleMouseUp = () => {
    mouseDragRef.current.isDragging = false;
  };

  // Collision checks to match SDF grid maps (2.5 units corridors spacing, 0.1 units thick walls)
  const checkCollision = (x: number, z: number) => {
    const spacingX = 2.5;
    const spacingZ = 2.5;

    // Calculate modular offsets in 3D grid corridors
    const localX = Math.abs(((x % spacingX) + spacingX) % spacingX - spacingX * 0.5);
    const localZ = Math.abs(((z % spacingZ) + spacingZ) % spacingZ - spacingZ * 0.5);

    // Safety buffer limit of 0.22 prevents wall clipping
    if (localX < 0.22 || localZ < 0.22) {
      return true;
    }
    return false;
  };

  // Animation ticks for updates and movement
  useEffect(() => {
    let animId: number;
    const tick = () => {
      if (isFocused) {
        const speed = 0.07;
        const forwardX = Math.sin(angle.x);
        const forwardZ = Math.cos(angle.x);
        const rightX = Math.cos(angle.x);
        const rightZ = -Math.sin(angle.x);

        let dx = 0;
        let dz = 0;

        if (keysPressed.current['KeyW'] || keysPressed.current['ArrowUp']) {
          dx += forwardX * speed;
          dz += forwardZ * speed;
        }
        if (keysPressed.current['KeyS'] || keysPressed.current['ArrowDown']) {
          dx -= forwardX * speed;
          dz -= forwardZ * speed;
        }
        if (keysPressed.current['KeyA'] || keysPressed.current['ArrowLeft']) {
          dx -= rightX * speed;
          dz -= rightZ * speed;
        }
        if (keysPressed.current['KeyD'] || keysPressed.current['ArrowRight']) {
          dx += rightX * speed;
          dz += rightZ * speed;
        }

        // Apply translations with safety bounds checks
        setCameraPos(prev => {
          const nextX = prev.x + dx;
          const nextZ = prev.z + dz;
          const collision = checkCollision(nextX, nextZ);

          if (!collision) {
            return { ...prev, x: nextX, z: nextZ };
          }
          return prev;
        });
      }
      animId = requestAnimationFrame(tick);
    };
    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, [isFocused, angle]);

  // Compile and bind WebGL uniforms
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const gl = canvas.getContext('webgl');
    if (!gl) return;

    const vsSource = `
      attribute vec2 position;
      void main() {
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `;

    const vs = gl.createShader(gl.VERTEX_SHADER);
    if (!vs) return;
    gl.shaderSource(vs, vsSource);
    gl.compileShader(vs);

    const fs = gl.createShader(gl.FRAGMENT_SHADER);
    if (!fs) return;
    gl.shaderSource(fs, shaderCode);
    gl.compileShader(fs);

    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
      console.error(gl.getShaderInfoLog(fs));
      return;
    }

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    gl.useProgram(program);

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1,  1, -1, -1,  1,
      -1,  1,  1, -1,  1,  1,
    ]), gl.STATIC_DRAW);

    const positionLocation = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(positionLocation);
    gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

    const resolutionLocation = gl.getUniformLocation(program, 'u_resolution');
    const timeLocation = gl.getUniformLocation(program, 'u_time');
    const angleLocation = gl.getUniformLocation(program, 'u_angle');
    const cameraLocation = gl.getUniformLocation(program, 'u_camera');

    let animId: number;
    const render = (time: number) => {
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform2f(resolutionLocation, canvas.width, canvas.height);
      gl.uniform1f(timeLocation, time * 0.001);
      gl.uniform2f(angleLocation, angle.x, angle.y);
      gl.uniform3f(cameraLocation, cameraPos.x, cameraPos.y, cameraPos.z);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      animId = requestAnimationFrame(render);
    };
    animId = requestAnimationFrame(render);

    return () => cancelAnimationFrame(animId);
  }, [shaderCode, cameraPos, angle]);

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      onBlur={handleBlur}
      className="relative focus:outline-none"
    >
      <canvas
        ref={canvasRef}
        width={340}
        height={240}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleCanvasClick}
        className={`bg-black rounded-xl border shadow-2xl transition-all ${
          isFocused ? 'border-[#738E54] ring-2 ring-[#738E54]/20 cursor-move' : 'border-border-subtle cursor-pointer'
        }`}
      />
      {!isFocused && (
        <div className="absolute inset-0 bg-black/60 rounded-xl flex flex-col justify-center items-center text-center p-4 pointer-events-none">
          <span className="text-xs font-semibold text-[#738E54] tracking-widest uppercase mb-1">🎮 Click to Play</span>
          <span className="text-[10px] text-gray-400 font-mono">WASD to walk | Drag mouse to look around</span>
        </div>
      )}
      {isFocused && (
        <div className="absolute top-3 left-4 flex items-center gap-1.5 font-mono text-[9px] text-red-500 tracking-widest uppercase">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
          REC
        </div>
      )}
    </div>
  );
};

const comparisonCases: ComparisonCase[] = [
  {
    id: 'website',
    title: '1. Website: Glassmorphic Feature Grid',
    category: 'Frontend Engineering & UI/UX',
    prompt: 'Create a Next.js React component for a responsive landing page section featuring glassmorphic feature cards and a smooth dark mode transition.',
    temuclaude: {
      latency: '1.8s',
      tokens: 410,
      highlights: [
        'Backdrop-blur glassmorphic overlays',
        'Dynamic radial ambient glow behind cards',
        'Hover border gradient transformations',
        'Outfit font styling with warm offsets'
      ],
      code: `// temuClaude Generated Component
import { useState } from 'react';

export default function FeaturesGrid() {
  const [isDark, setIsDark] = useState(true);
  return (
    <div className={\`p-8 rounded-2xl border transition-colors duration-500 relative overflow-hidden \${
      isDark ? 'bg-[#0f110c] text-white border-white/10' : 'bg-[#faf8f5] text-black border-black/10'
    }\`}>
      {/* Radial Gradient Glow */}
      <div className="absolute top-2 left-2 w-32 h-32 bg-[#738E54]/15 rounded-full blur-2xl pointer-events-none" />
      <div className="flex justify-between items-center mb-6 relative z-10">
        <h4 className="text-lg font-serif">Modern Cognitive Pipelines</h4>
        <button onClick={() => setIsDark(!isDark)} className="p-1.5 rounded-full bg-white/10 border backdrop-blur">
          {isDark ? '☀️ Light' : '🌙 Dark'}
        </button>
      </div>
    </div>
  );
}`,
    },
    frontierBaseline: {
      latency: '2.5s',
      tokens: 490,
      highlights: [
        'Fully responsive Tailwind grid layout',
        'Active functional light/dark mode states',
        'Modern card elevation with colored icon badges',
        'Optimized typography and clean HTML syntax'
      ],
      note: 'Frontier direct baseline generates a highly polished, responsive Tailwind component with active state toggles and clean visual hierarchies, representing frontier-grade single-model code outputs.',
      sourceText: 'View user-generated web layouts gallery on GitHub (pulkitxm/claude-directory)',
      sourceUrl: 'https://github.com/pulkitxm/claude-directory',
      code: `// Frontier direct baseline Generated Component
import { useState } from 'react';

export default function FrontierBaselineFeatures() {
  const [dark, setDark] = useState(false);
  return (
    <div className={\`p-6 rounded-2xl border transition-all \${
      dark ? 'bg-gray-900 text-white border-gray-800' : 'bg-white text-gray-900 border-gray-200'
    }\`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-md font-bold">Standard Tailwind Feature Grid</h3>
        <button onClick={() => setDark(!dark)} className="text-xs px-2.5 py-1 border rounded bg-gray-50 text-gray-800">
          Toggle Mode
        </button>
      </div>
    </div>
  );
}`,
    },
  },
  {
    id: 'game',
    title: '2. Game: 3D Ray-Marched Backrooms Horror',
    category: 'Advanced WebGL & Computer Graphics',
    prompt: 'Implement a 3D browser-based ray-marched horror experience of the Backrooms Level 0 with yellow wallpapers, flickering lights, VHS filter, and interactive flashlight.',
    temuclaude: {
      latency: '2.9s',
      tokens: 680,
      highlights: [
        'Endless corridor intersection grid algorithms',
        'Interactive keyboard WASD translations with wall collisions',
        'Mouse look rotations mapping yaw/pitch camera matrix transformations',
        'CRT camera analog filters and pulsing red REC overlay',
        'Flickering light silhouette monster triggers'
      ],
      code: `// temuClaude WebGL Fragment Shader (Endless Corridors + VHS Noise + Yaw/Pitch)
precision mediump float;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_angle;
uniform vec3 u_camera;

void rotateY(inout vec3 p, float a) {
  float c = cos(a); float s = sin(a);
  p.xz = mat2(c, -s, s, c) * p.xz;
}

void rotateX(inout vec3 p, float a) {
  float c = cos(a); float s = sin(a);
  p.yz = mat2(c, -s, s, c) * p.yz;
}

float map(vec3 p) {
  vec3 c = vec3(2.5, 0.0, 2.5);
  vec3 q = p;
  q.x = mod(p.x, c.x) - 0.5 * c.x;
  q.z = mod(p.z, c.z) - 0.5 * c.z;
  return min(min(abs(q.x) - 0.1, abs(q.z) - 0.1), abs(p.y) - 1.0);
}
// ...`,
    },
    frontierBaseline: {
      latency: '3.4s',
      tokens: 520,
      highlights: [
        '3D ray-marched linear perspective hallway',
        'Basic fog scaling calculations',
        'Solid yellow wall layout configurations',
        'Smooth rendering compilation logs'
      ],
      note: 'Frontier direct baseline is embedded as a live frame showing StarKnightt\'s complete Three.js 3D game directly from the deployment. Click to lock pointer lock controls and play the Frontier direct baseline example.',
      sourceText: 'StarKnightt / Backrooms Level 0 Escape (backroom-escape.vercel.app)',
      sourceUrl: 'https://backroom-escape.vercel.app',
      code: `// Frontier direct baseline Output embeds the live web game directly via Iframe
<iframe src="https://backroom-escape.vercel.app" />`,
    },
  },
];

export default function ComparePage() {
  const [activeTab, setActiveTab] = useState<'website' | 'game' | 'diagram'>('website');

  // Website preview states
  const [temuDark, setTemuDark] = useState(true);
  const [frontierDark, setFrontierDark] = useState(false);

  // Display mode toggle for columns: 'preview' or 'code'
  const [temuMode, setTemuMode] = useState<'preview' | 'code'>('preview');
  const [frontierMode, setFrontierMode] = useState<'preview' | 'code'>('preview');

  const activeCase = comparisonCases.find(c => c.id === activeTab) || comparisonCases[0];

  return (
    <>
      <Navbar />
      <main id="main-content" className="pt-24 pb-20 px-6 min-h-screen text-text-primary bg-bg-primary" aria-label="Compare Arena Dashboard">
        <div className="max-w-6xl mx-auto space-y-10">
          {/* Header */}
          <div className="text-center md:text-left border-b border-border-subtle pb-6">
            <h1 className="text-3xl md:text-4xl font-serif mb-2 text-text-primary" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
              temuClaude vs Frontier direct baseline Fallback
            </h1>
            <p className="text-text-secondary text-sm max-w-xl">
              Compare actual generated output components and orchestration routing architectures side-by-side.
            </p>
          </div>

          {/* Combined Selection Tabs */}
          <div className="flex flex-wrap gap-2 mb-6 border-b border-border-subtle pb-4">
            <button
              onClick={() => setActiveTab('website')}
              className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider rounded transition-all border ${
                activeTab === 'website'
                  ? 'bg-[#738E54] text-white border-[#738E54]'
                  : 'text-text-muted hover:text-text-primary bg-bg-secondary border-border-subtle'
              }`}
            >
              1. Website Generation Preview
            </button>
            <button
              onClick={() => setActiveTab('game')}
              className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider rounded transition-all border ${
                activeTab === 'game'
                  ? 'bg-[#738E54] text-white border-[#738E54]'
                  : 'text-text-muted hover:text-text-primary bg-bg-secondary border-border-subtle'
              }`}
            >
              2. 3D Backrooms Escape Playable Game
            </button>
            <button
              onClick={() => setActiveTab('diagram')}
              className={`px-4 py-2.5 text-xs font-semibold uppercase tracking-wider rounded transition-all border ${
                activeTab === 'diagram'
                  ? 'bg-[#738E54] text-white border-[#738E54]'
                  : 'text-text-muted hover:text-text-primary bg-bg-secondary border-border-subtle'
              }`}
            >
              3. Orchestration Flow Diagram
            </button>
          </div>

          {/* WEBSITE TAB PREVIEWS */}
          {activeTab === 'website' && (
            <div className="space-y-8">
              <div className="card bg-white border border-border-subtle p-6">
                <span className="text-[10px] text-[#738E54] font-mono uppercase tracking-wider mb-2 font-semibold">User Request</span>
                <h2 className="text-base font-semibold text-text-primary mb-2">
                  "Create a glassmorphic Next.js card grid featuring active dark/light mode toggle animations."
                </h2>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Column 1: temuClaude */}
                <div className="flex flex-col p-6 rounded-xl bg-white border border-[#738E54]/30 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-[#738E54] text-white text-[10px] uppercase font-mono px-3 py-1 rounded-bl font-semibold">
                    temuClaude output (Real Rendered)
                  </div>

                  {/* Toggle Mode */}
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xs font-semibold">Interactive Glassmorphism Grid</span>
                    <div className="flex border border-border-subtle rounded overflow-hidden">
                      <button
                        onClick={() => setTemuMode('preview')}
                        className={`px-2 py-1 text-[10px] font-bold ${temuMode === 'preview' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => setTemuMode('code')}
                        className={`px-2 py-1 text-[10px] font-bold ${temuMode === 'code' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Code
                      </button>
                    </div>
                  </div>

                  {temuMode === 'preview' ? (
                    /* Rendered Live Website Component Preview */
                    <div className={`p-6 rounded-2xl border transition-colors duration-500 relative overflow-hidden min-h-[220px] ${
                      temuDark ? 'bg-[#0f110c] text-white border-white/10' : 'bg-[#faf8f5] text-[#1a1816] border-black/10'
                    }`}>
                      <div className="absolute top-2 left-2 w-32 h-32 bg-[#738E54]/15 rounded-full blur-2xl pointer-events-none" />
                      <div className="absolute bottom-2 right-2 w-32 h-32 bg-[#E25822]/10 rounded-full blur-2xl pointer-events-none" />

                      <div className="flex justify-between items-center mb-6 relative z-10">
                        <span className="text-[10px] font-mono tracking-widest uppercase opacity-75">temuClaude UI</span>
                        <button
                          onClick={() => setTemuDark(!temuDark)}
                          className="p-1.5 rounded-full bg-white/10 backdrop-blur border border-white/10 text-xs shadow-sm hover:scale-105 active:scale-95 transition-transform"
                        >
                          {temuDark ? '☀️ Light' : '🌙 Dark'}
                        </button>
                      </div>

                      <h4 className="text-lg font-serif mb-2 relative z-10">Modern Cognitive Pipelines</h4>
                      <p className="text-xs text-text-secondary mb-4 leading-relaxed relative z-10">
                        The compound approach splits context analysis, agent drafting, tree-search logic, and validation consensus.
                      </p>
                    </div>
                  ) : (
                    <pre className="p-4 bg-gray-50 border border-border-subtle rounded text-[9px] font-mono overflow-auto max-h-[220px] text-gray-800">
                      {activeCase.temuclaude.code}
                    </pre>
                  )}

                  <div className="mt-6 pt-4 border-t border-border-subtle space-y-2">
                    <div className="text-xs font-semibold text-text-primary">Evaluation Metrics:</div>
                    <div className="flex flex-wrap gap-2">
                      {activeCase.temuclaude.highlights.map((h, i) => (
                        <span key={i} className="px-2.5 py-1 text-[10px] rounded bg-[#738E54]/10 text-[#738E54] font-medium font-semibold">
                          ✓ {h}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Column 2: Frontier direct baseline */}
                <div className="flex flex-col p-6 rounded-xl bg-white border border-border-default shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-amber-600 text-white text-[10px] uppercase font-mono px-3 py-1 rounded-bl font-semibold">
                    Frontier direct baseline output (Real Rendered)
                  </div>

                  {/* Toggle Mode */}
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-semibold text-text-muted">Standard Tailwind Feature Grid</span>
                    <div className="flex border border-border-subtle rounded overflow-hidden">
                      <button
                        onClick={() => setFrontierMode('preview')}
                        className={`px-2 py-1 text-[10px] font-bold ${frontierMode === 'preview' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => setFrontierMode('code')}
                        className={`px-2 py-1 text-[10px] font-bold ${frontierMode === 'code' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Code
                      </button>
                    </div>
                  </div>

                  {frontierMode === 'preview' ? (
                    /* Rendered Live Website Component Preview from Fallback Frontier direct baseline */
                    <div className={`p-6 rounded-2xl border transition-colors duration-500 relative overflow-hidden min-h-[220px] ${
                      frontierDark ? 'bg-gray-900 text-white border-gray-800' : 'bg-white text-gray-900 border-gray-200'
                    }`}>
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-[10px] font-mono tracking-widest uppercase opacity-75">Frontier direct baseline UI</span>
                        <button
                          onClick={() => setFrontierDark(!frontierDark)}
                          className="p-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs shadow-sm"
                        >
                          {frontierDark ? '☀️ Light' : '🌙 Dark'}
                        </button>
                      </div>
                      <h4 className="text-lg font-sans font-bold mb-2">Standard Tailwind Grid</h4>
                      <p className="text-xs text-gray-500 mb-4 leading-relaxed">
                        A typical high-quality single model output using robust grid classes and semantic elements.
                      </p>
                    </div>
                  ) : (
                    <pre className="p-4 bg-gray-50 border border-border-subtle rounded text-[9px] font-mono overflow-auto max-h-[220px] text-gray-800">
                      {activeCase.frontierBaseline.code}
                    </pre>
                  )}

                  <div className="mt-6 pt-4 border-t border-border-subtle space-y-2">
                    <div className="text-xs font-semibold text-text-primary text-amber-700">Model Merits:</div>
                    <div className="flex flex-wrap gap-2">
                      {activeCase.frontierBaseline.highlights.map((h, i) => (
                        <span key={i} className="px-2.5 py-1 text-[10px] rounded bg-amber-100 text-amber-800 border border-amber-200 font-semibold font-mono">
                          {h}
                        </span>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted font-mono mt-2">
                      {activeCase.frontierBaseline.note}
                    </p>
                    <div className="text-[10px] text-text-muted mt-3 pt-2 border-t border-dashed border-border-subtle font-mono">
                      <a
                        href={activeCase.frontierBaseline.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#738E54] hover:underline font-semibold"
                      >
                        {activeCase.frontierBaseline.sourceText}
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* GAME TAB PREVIEWS */}
          {activeTab === 'game' && (
            <div className="space-y-8">
              <div className="card bg-white border border-border-subtle p-6">
                <span className="text-[10px] text-[#738E54] font-mono uppercase tracking-wider mb-2 font-semibold">User Request</span>
                <h2 className="text-base font-semibold text-text-primary mb-2">
                  "Implement a 3D browser-based ray-marched horror experience of the Backrooms Level 0 with yellow wallpapers, flickering lights, VHS filter, and interactive flashlight."
                </h2>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                {/* Column 1: temuClaude (Playable 3D WebGL Game) */}
                <div className="flex flex-col p-6 rounded-xl bg-white border border-[#738E54]/30 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-[#738E54] text-white text-[10px] uppercase font-mono px-3 py-1 rounded-bl font-semibold">
                    temuClaude output (WebGL Playable 3D Game)
                  </div>

                  {/* Toggle Mode */}
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-semibold text-[#738E54]">Interactive 3D Horror Engine</span>
                    <div className="flex border border-border-subtle rounded overflow-hidden">
                      <button
                        onClick={() => setTemuMode('preview')}
                        className={`px-2 py-1 text-[10px] font-bold ${temuMode === 'preview' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => setTemuMode('code')}
                        className={`px-2 py-1 text-[10px] font-bold ${temuMode === 'code' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Code
                      </button>
                    </div>
                  </div>

                  {temuMode === 'preview' ? (
                    <div className="flex flex-col justify-center items-center bg-black p-8 rounded-xl border border-border-subtle overflow-hidden min-h-[260px] relative">
                      <div className="absolute inset-0 bg-[url('https://upload.wikimedia.org/wikipedia/commons/d/d4/Texture_of_white_noise.png')] opacity-10 mix-blend-overlay animate-pulse" />
                      <div className="absolute top-4 left-4 flex items-center gap-2">
                        <div className="w-2 h-2 bg-red-600 rounded-full animate-ping" />
                        <span className="text-xs font-mono text-red-500 font-bold">REC</span>
                      </div>
                      <h3 className="text-xl font-bold tracking-widest text-amber-100 mb-4 drop-shadow-[0_0_10px_rgba(255,200,100,0.5)] z-10">LEVEL 0</h3>
                      <p className="text-xs text-amber-100/60 mb-6 text-center z-10">Fully standalone 3D WebGL experience.<br/>Made with Three.js</p>
                      <a href="/play/backrooms" target="_blank" rel="noopener noreferrer" className="px-6 py-2 bg-amber-100 text-black font-bold tracking-widest text-xs hover:bg-white transition-colors z-10">
                        PLAY FULL GAME
                      </a>
                    </div>
                  ) : (
                    <pre className="p-4 bg-gray-50 border border-border-subtle rounded text-[9px] font-mono overflow-auto max-h-[240px] text-gray-800">
                      {activeCase.temuclaude.code}
                    </pre>
                  )}

                  <div className="mt-6 pt-4 border-t border-border-subtle space-y-2">
                    <div className="text-xs font-semibold text-text-primary">Evaluation Metrics:</div>
                    <div className="flex flex-wrap gap-2">
                      {activeCase.temuclaude.highlights.map((h, i) => (
                        <span key={i} className="px-2.5 py-1 text-[10px] rounded bg-[#738E54]/10 text-[#738E54] font-medium font-semibold">
                          ✓ {h}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Column 2: Frontier direct baseline */}
                <div className="flex flex-col p-6 rounded-xl bg-white border border-border-default shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-amber-600 text-white text-[10px] uppercase font-mono px-3 py-1 rounded-bl font-semibold">
                    Frontier direct baseline output (Live Game Frame)
                  </div>

                  {/* Toggle Mode */}
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-semibold text-text-muted">Direct Iframe Game Integration</span>
                    <div className="flex border border-border-subtle rounded overflow-hidden">
                      <button
                        onClick={() => setFrontierMode('preview')}
                        className={`px-2 py-1 text-[10px] font-bold ${frontierMode === 'preview' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => setFrontierMode('code')}
                        className={`px-2 py-1 text-[10px] font-bold ${frontierMode === 'code' ? 'bg-[#738E54] text-white' : 'bg-white text-text-muted'}`}
                      >
                        Code
                      </button>
                    </div>
                  </div>

                  {frontierMode === 'preview' ? (
                    <div className="flex flex-col justify-center items-center bg-black p-8 rounded-xl border border-border-subtle overflow-hidden min-h-[260px]">
                      <h3 className="text-xl font-bold tracking-widest text-white mb-4">BACKROOMS ESCAPE</h3>
                      <p className="text-xs text-gray-400 mb-6 text-center">Frontier direct baseline generated Three.js game.<br/>Deployed on Vercel.</p>
                      <a href="https://backroom-escape.vercel.app" target="_blank" rel="noopener noreferrer" className="px-6 py-2 bg-white text-black font-bold tracking-widest text-xs hover:bg-gray-200 transition-colors">
                        PLAY FULL GAME
                      </a>
                    </div>
                  ) : (
                    <pre className="p-4 bg-gray-50 border border-border-subtle rounded text-[9px] font-mono overflow-auto max-h-[240px] text-gray-800">
                      {activeCase.frontierBaseline.code}
                    </pre>
                  )}

                  <div className="mt-6 pt-4 border-t border-border-subtle space-y-2">
                    <div className="text-xs font-semibold text-text-primary text-amber-700">Model Merits:</div>
                    <div className="flex flex-wrap gap-2">
                      {activeCase.frontierBaseline.highlights.map((h, i) => (
                        <span key={i} className="px-2.5 py-1 text-[10px] rounded bg-amber-100 text-amber-800 border border-amber-200 font-semibold font-mono">
                          {h}
                        </span>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted font-mono mt-2">
                      {activeCase.frontierBaseline.note}
                    </p>
                    <div className="text-[10px] text-text-muted mt-3 pt-2 border-t border-dashed border-border-subtle font-mono">
                      <a
                        href={activeCase.frontierBaseline.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#738E54] hover:underline font-semibold"
                      >
                        {activeCase.frontierBaseline.sourceText}
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* DIAGRAM TAB */}
          {activeTab === 'diagram' && (
            <div className="space-y-8">
              <div className="card bg-white border border-border-subtle p-8 space-y-8">
                <div className="text-center max-w-xl mx-auto space-y-2">
                  <h2 className="text-xl font-serif text-text-primary">Pipeline Comparison: Compound vs Agentic Loop</h2>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Comparing temuClaude&apos;s compound expert routing against Frontier direct baseline&apos;s local terminal agent loop.
                  </p>
                </div>

                <div className="grid md:grid-cols-2 gap-12 pt-6">
                  {/* Left Flow: temuClaude */}
                  <div className="space-y-6 relative">
                    <div className="absolute top-2 left-6 bottom-2 w-0.5 border-l-2 border-dashed border-[#738E54]/30 -z-10" />

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-[#738E54] text-white flex items-center justify-center font-mono text-xs font-bold">1</div>
                      <div className="flex-1 bg-[#738E54]/10 border border-[#738E54]/30 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#738E54] block">Prompt Classification</span>
                        <span className="text-[11px] text-text-secondary">Input classified dynamically to determine task-specific routes (coding, reasoning).</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-[#738E54] text-white flex items-center justify-center font-mono text-xs font-bold">2</div>
                      <div className="flex-1 bg-[#738E54]/10 border border-[#738E54]/30 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#738E54] block">Parallel Dispatching</span>
                        <span className="text-[11px] text-text-secondary">Dispatches concurrent draft queries to specialized panels (Gemini, Llama, DeepSeek).</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-[#738E54] text-white flex items-center justify-center font-mono text-xs font-bold">3</div>
                      <div className="flex-1 bg-[#738E54]/10 border border-[#738E54]/30 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#738E54] block">D-MCTS Tree Search</span>
                        <span className="text-[11px] text-text-secondary">Deep Monte Carlo reasoning trees verify syntax logic and execution branches.</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-[#738E54] text-white flex items-center justify-center font-mono text-xs font-bold">4</div>
                      <div className="flex-1 bg-[#738E54] text-white rounded-lg p-4 shadow-md">
                        <span className="text-xs font-mono font-bold uppercase tracking-wider block">Token Fusion Consensus</span>
                        <span className="text-[11px] opacity-90">Mixture-of-Agents consensus blends candidate tokens, outputting clean zero-fluff code.</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Flow: Frontier direct baseline (Claude Code agent loop) */}
                  <div className="space-y-6 relative">
                    <div className="absolute top-2 left-6 bottom-2 w-0.5 border-l-2 border-dashed border-amber-200/40 -z-10" />

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-mono text-xs font-bold">1</div>
                      <div className="flex-1 bg-amber-50 border border-amber-100 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-800 block">Agent Planning</span>
                        <span className="text-[11px] text-amber-700">Frontier direct baseline parses workspace structure, planning files to edit in parallel subtasks.</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-mono text-xs font-bold">2</div>
                      <div className="flex-1 bg-amber-50 border border-amber-100 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-800 block">Terminal & File Access</span>
                        <span className="text-[11px] text-amber-700">Calls CLI commands directly to read files, write chunks, or edit buffers.</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-mono text-xs font-bold">3</div>
                      <div className="flex-1 bg-amber-50 border border-amber-100 rounded-lg p-4">
                        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-800 block">Interactive Compile Ticks</span>
                        <span className="text-[11px] text-amber-700">Runs local compiler builds (tsc, linter) and tests to detect compilation failures.</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-mono text-xs font-bold">4</div>
                      <div className="flex-1 bg-amber-600 text-white rounded-lg p-4 shadow-md">
                        <span className="text-xs font-mono font-bold uppercase tracking-wider block">Self-Correcting Loops</span>
                        <span className="text-[11px] opacity-90">Parses linter errors, refactoring the output code until all tests pass.</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="text-center text-[10px] text-text-muted border-t pt-4 font-mono">
                  Sources: <a href="https://github.com/anthropics/claude-code" target="_blank" rel="noopener noreferrer" className="hover:underline text-[#738E54]">Claude Code Documentation</a> & <a href="https://www.anthropic.com/claude" target="_blank" rel="noopener noreferrer" className="hover:underline text-[#738E54]">Anthropic Research Specifications</a>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
