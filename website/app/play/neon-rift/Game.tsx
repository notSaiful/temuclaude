'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

type Enemy = { x: number; y: number; r: number; hp: number; speed: number; damage: number; hue: number; kind: 'drone' | 'brute' | 'skimmer' };
type Bullet = { x: number; y: number; vx: number; vy: number; life: number; friendly: boolean };
type Spark = { x: number; y: number; vx: number; vy: number; life: number; max: number; hue: number };
type Upgrade = { title: string; detail: string; apply: (s: State) => void };
type State = {
  w: number; h: number; player: { x: number; y: number; hp: number; maxHp: number; angle: number; speed: number; fireRate: number; damage: number; radius: number };
  keys: Set<string>; pointer: { x: number; y: number; down: boolean }; enemies: Enemy[]; bullets: Bullet[]; sparks: Spark[];
  wave: number; spawned: number; target: number; score: number; combo: number; comboUntil: number; xp: number; level: number; nextXp: number; lastShot: number; lastSpawn: number; paused: boolean; over: boolean; choosing: boolean;
};

const upgrades: Upgrade[] = [
  { title: 'Overclock', detail: '+30% fire rate', apply: s => { s.player.fireRate *= 1.3; } },
  { title: 'Plasma Core', detail: '+8 weapon damage', apply: s => { s.player.damage += 8; } },
  { title: 'Phase Boots', detail: '+18% movement speed', apply: s => { s.player.speed *= 1.18; } },
  { title: 'Nanoforge', detail: 'Restore 35 hull', apply: s => { s.player.hp = Math.min(s.player.maxHp, s.player.hp + 35); } },
  { title: 'Reinforced Hull', detail: '+25 max hull', apply: s => { s.player.maxHp += 25; s.player.hp += 25; } },
  { title: 'Wide Bore', detail: '+4 projectile size', apply: s => { s.player.radius = Math.min(22, s.player.radius + 4); } },
];

function pick<T>(items: T[], count: number) { return [...items].sort(() => Math.random() - 0.5).slice(0, count); }
function distance(ax: number, ay: number, bx: number, by: number) { return Math.hypot(ax - bx, ay - by); }

export default function Game() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<State | null>(null);
  const rafRef = useRef<number | null>(null);
  const audioRef = useRef<AudioContext | null>(null);
  const [hud, setHud] = useState({ wave: 1, score: 0, hp: 100, maxHp: 100, xp: 0, nextXp: 80, combo: 0, paused: false, over: false });
  const [choices, setChoices] = useState<Upgrade[]>([]);

  const sound = useCallback((frequency: number, duration: number, gain: number) => {
    const context = audioRef.current;
    if (!context) return;
    const oscillator = context.createOscillator(); const volume = context.createGain();
    oscillator.type = 'square'; oscillator.frequency.value = frequency; volume.gain.setValueAtTime(gain, context.currentTime); volume.gain.exponentialRampToValueAtTime(0.001, context.currentTime + duration);
    oscillator.connect(volume); volume.connect(context.destination); oscillator.start(); oscillator.stop(context.currentTime + duration);
  }, []);

  const startAudio = useCallback(() => { if (!audioRef.current) audioRef.current = new AudioContext(); if (audioRef.current.state === 'suspended') void audioRef.current.resume(); }, []);

  const reset = useCallback(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const next: State = { w: rect.width, h: rect.height, player: { x: rect.width / 2, y: rect.height / 2, hp: 100, maxHp: 100, angle: 0, speed: 285, fireRate: 5, damage: 22, radius: 13 }, keys: new Set(), pointer: { x: rect.width / 2, y: rect.height / 2, down: false }, enemies: [], bullets: [], sparks: [], wave: 1, spawned: 0, target: 8, score: 0, combo: 0, comboUntil: 0, xp: 0, level: 1, nextXp: 80, lastShot: 0, lastSpawn: 0, paused: false, over: false, choosing: false };
    stateRef.current = next; setChoices([]); setHud({ wave: 1, score: 0, hp: 100, maxHp: 100, xp: 0, nextXp: 80, combo: 0, paused: false, over: false });
  }, []);

  useEffect(() => {
    reset(); const canvas = canvasRef.current!;
    const resize = () => { const s = stateRef.current; const r = canvas.getBoundingClientRect(); canvas.width = Math.floor(r.width * devicePixelRatio); canvas.height = Math.floor(r.height * devicePixelRatio); if (s) { s.w = r.width; s.h = r.height; s.player.x = Math.min(s.w - 20, s.player.x); s.player.y = Math.min(s.h - 20, s.player.y); } };
    resize(); window.addEventListener('resize', resize);
    const point = (event: PointerEvent) => { const r = canvas.getBoundingClientRect(); const s = stateRef.current; if (s) { s.pointer.x = event.clientX - r.left; s.pointer.y = event.clientY - r.top; } };
    const key = (event: KeyboardEvent, down: boolean) => { const s = stateRef.current; if (!s) return; if (event.code === 'Space') { event.preventDefault(); s.pointer.down = down; } if (event.code === 'Escape' && down && !s.choosing && !s.over) s.paused = !s.paused; s.keys[down ? 'add' : 'delete'](event.code); };
    const pointerDown = (event: PointerEvent) => { startAudio(); point(event); const s = stateRef.current; if (s) s.pointer.down = true; };
    const pointerUp = () => { const s = stateRef.current; if (s) s.pointer.down = false; };
    const keyDown = (event: KeyboardEvent) => key(event, true); const keyUp = (event: KeyboardEvent) => key(event, false);
    canvas.addEventListener('pointermove', point); canvas.addEventListener('pointerdown', pointerDown); canvas.addEventListener('pointerup', pointerUp);
    window.addEventListener('keydown', keyDown); window.addEventListener('keyup', keyUp);
    const render = (now: number) => {
      const s = stateRef.current; const ctx = canvas.getContext('2d'); if (!s || !ctx) return;
      const dt = Math.min(0.035, ((render as any).last ? now - (render as any).last : 16) / 1000); (render as any).last = now;
      ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0); ctx.clearRect(0, 0, s.w, s.h);
      const bg = ctx.createRadialGradient(s.player.x, s.player.y, 0, s.player.x, s.player.y, Math.max(s.w, s.h) * .8); bg.addColorStop(0, '#111b40'); bg.addColorStop(1, '#04050e'); ctx.fillStyle = bg; ctx.fillRect(0, 0, s.w, s.h);
      ctx.strokeStyle = 'rgba(0,240,255,.08)'; ctx.lineWidth = 1; for (let x = -40; x < s.w + 40; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x - s.h * .22, s.h); ctx.stroke(); } for (let y = 0; y < s.h; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(s.w, y); ctx.stroke(); }
      if (!s.paused && !s.over && !s.choosing) update(s, dt, now, sound, setChoices);
      draw(ctx, s, now); if (now % 120 < 18) setHud({ wave: s.wave, score: s.score, hp: Math.ceil(s.player.hp), maxHp: s.player.maxHp, xp: s.xp, nextXp: s.nextXp, combo: s.combo, paused: s.paused, over: s.over });
      rafRef.current = requestAnimationFrame(render);
    };
    rafRef.current = requestAnimationFrame(render);
    return () => { if (rafRef.current !== null) cancelAnimationFrame(rafRef.current); window.removeEventListener('resize', resize); canvas.removeEventListener('pointermove', point); canvas.removeEventListener('pointerdown', pointerDown); canvas.removeEventListener('pointerup', pointerUp); window.removeEventListener('keydown', keyDown); window.removeEventListener('keyup', keyUp); };
  }, [reset, sound, startAudio]);

  const choose = (upgrade: Upgrade) => { const s = stateRef.current; if (!s) return; upgrade.apply(s); s.choosing = false; setChoices([]); sound(520, .08, .05); };
  const togglePause = () => { const s = stateRef.current; if (s && !s.choosing && !s.over) { s.paused = !s.paused; setHud(h => ({ ...h, paused: s.paused })); } };
  return <main className="relative min-h-screen select-none overflow-hidden bg-[#04050e] font-mono text-cyan-100"><canvas ref={canvasRef} className="absolute inset-0 h-full w-full touch-none" aria-label="Neon Rift action shooter. Use WASD or arrows to move, aim with pointer, and click or press Space to fire." />
    <section className="pointer-events-none relative mx-auto flex max-w-5xl justify-between p-4 text-xs sm:p-6"><div><p className="text-cyan-300">NEON RIFT // WAVE {hud.wave}</p><p className="mt-1 text-white/70">SCORE {hud.score.toString().padStart(6, '0')} {hud.combo > 1 && <span className="text-fuchsia-300">×{hud.combo} COMBO</span>}</p></div><div className="w-36 text-right"><p>HULL {hud.hp}/{hud.maxHp}</p><div className="mt-1 h-2 overflow-hidden border border-cyan-400/40 bg-black/50"><div className="h-full bg-cyan-300" style={{ width: `${Math.max(0, hud.hp / hud.maxHp * 100)}%` }} /></div><p className="mt-2">LEVEL {Math.floor(hud.nextXp ? (hud.nextXp / 80) : 1)} · XP {hud.xp}/{hud.nextXp}</p></div></section>
    <div className="pointer-events-none absolute inset-x-0 bottom-4 text-center text-[10px] text-cyan-100/60">WASD / ARROWS MOVE · POINTER AIM · CLICK / SPACE FIRE · ESC PAUSE</div>
    <div className="absolute bottom-12 left-4 flex gap-2 sm:hidden"><button onPointerDown={() => stateRef.current?.keys.add('ArrowLeft')} onPointerUp={() => stateRef.current?.keys.delete('ArrowLeft')} className="rounded border border-cyan-300/40 bg-black/50 px-3 py-2">◀</button><button onPointerDown={() => stateRef.current?.keys.add('ArrowRight')} onPointerUp={() => stateRef.current?.keys.delete('ArrowRight')} className="rounded border border-cyan-300/40 bg-black/50 px-3 py-2">▶</button></div>
    <button onClick={togglePause} className="absolute right-4 bottom-12 rounded border border-cyan-300/40 bg-black/50 px-3 py-2 text-xs text-cyan-100">{hud.paused ? 'RESUME' : 'PAUSE'}</button>
    {(hud.paused || hud.over || choices.length > 0) && <div className="absolute inset-0 grid place-items-center bg-[#03040c]/80 p-5"><div className="max-w-xl text-center">{hud.over ? <><h1 className="text-3xl font-bold text-fuchsia-300">RIFT BREACH</h1><p className="mt-3 text-cyan-100/70">Final score: {hud.score}</p><button onClick={() => { startAudio(); reset(); }} className="mt-6 border border-cyan-300 bg-cyan-300/15 px-6 py-3 text-cyan-100">DEPLOY AGAIN</button></> : choices.length ? <><h1 className="text-2xl font-bold text-cyan-200">LEVEL UP — CHOOSE A MODULE</h1><div className="mt-6 grid gap-3 sm:grid-cols-3">{choices.map(choice => <button key={choice.title} onClick={() => choose(choice)} className="border border-cyan-300/40 bg-[#0a1030] p-4 text-left transition hover:border-fuchsia-300 hover:bg-[#151046]"><b>{choice.title}</b><span className="mt-2 block text-xs text-cyan-100/65">{choice.detail}</span></button>)}</div></> : <><h1 className="text-3xl font-bold text-cyan-200">SYSTEM PAUSED</h1><button onClick={togglePause} className="mt-6 border border-cyan-300 bg-cyan-300/15 px-6 py-3">RESUME</button></>}</div></div>}
  </main>;
}

function update(s: State, dt: number, now: number, sound: (f: number, d: number, g: number) => void, showChoices: (u: Upgrade[]) => void) {
  const p = s.player; let dx = 0, dy = 0; if (s.keys.has('KeyW') || s.keys.has('ArrowUp')) dy--; if (s.keys.has('KeyS') || s.keys.has('ArrowDown')) dy++; if (s.keys.has('KeyA') || s.keys.has('ArrowLeft')) dx--; if (s.keys.has('KeyD') || s.keys.has('ArrowRight')) dx++;
  const len = Math.hypot(dx, dy) || 1; p.x = Math.max(18, Math.min(s.w - 18, p.x + dx / len * p.speed * dt)); p.y = Math.max(18, Math.min(s.h - 18, p.y + dy / len * p.speed * dt)); p.angle = Math.atan2(s.pointer.y - p.y, s.pointer.x - p.x);
  if (s.pointer.down && now - s.lastShot > 1000 / p.fireRate) { s.lastShot = now; s.bullets.push({ x: p.x + Math.cos(p.angle) * 22, y: p.y + Math.sin(p.angle) * 22, vx: Math.cos(p.angle) * 720, vy: Math.sin(p.angle) * 720, life: .9, friendly: true }); sound(170, .04, .035); }
  if (s.spawned < s.target && now - s.lastSpawn > Math.max(260, 800 - s.wave * 35)) { s.lastSpawn = now; s.spawned++; const a = Math.random() * Math.PI * 2; const kind = Math.random() < .18 + s.wave * .01 ? 'brute' : Math.random() < .25 ? 'skimmer' : 'drone'; const r = kind === 'brute' ? 22 : kind === 'skimmer' ? 9 : 14; const hp = kind === 'brute' ? 90 + s.wave * 18 : kind === 'skimmer' ? 24 + s.wave * 5 : 40 + s.wave * 8; s.enemies.push({ x: p.x + Math.cos(a) * Math.max(s.w, s.h) * .65, y: p.y + Math.sin(a) * Math.max(s.w, s.h) * .65, r, hp, speed: kind === 'brute' ? 55 + s.wave * 3 : kind === 'skimmer' ? 145 + s.wave * 5 : 90 + s.wave * 4, damage: kind === 'brute' ? 25 : 12, hue: kind === 'brute' ? 310 : kind === 'skimmer' ? 50 : 345, kind }); }
  for (const bullet of s.bullets) { bullet.x += bullet.vx * dt; bullet.y += bullet.vy * dt; bullet.life -= dt; } s.bullets = s.bullets.filter(b => b.life > 0 && b.x > -30 && b.x < s.w + 30 && b.y > -30 && b.y < s.h + 30);
  for (const enemy of s.enemies) { const a = Math.atan2(p.y - enemy.y, p.x - enemy.x); const wobble = enemy.kind === 'skimmer' ? Math.sin(now / 190 + enemy.x) * .55 : 0; enemy.x += Math.cos(a + wobble) * enemy.speed * dt; enemy.y += Math.sin(a + wobble) * enemy.speed * dt; if (distance(enemy.x, enemy.y, p.x, p.y) < enemy.r + 12) { p.hp -= enemy.damage * dt; if (p.hp <= 0) s.over = true; } }
  for (const bullet of s.bullets) if (bullet.friendly) for (const enemy of s.enemies) if (enemy.hp > 0 && distance(bullet.x, bullet.y, enemy.x, enemy.y) < enemy.r + 5) { enemy.hp -= p.damage; bullet.life = 0; for (let i = 0; i < 6; i++) s.sparks.push({ x: enemy.x, y: enemy.y, vx: (Math.random() - .5) * 180, vy: (Math.random() - .5) * 180, life: .35, max: .35, hue: enemy.hue }); }
  const alive: Enemy[] = []; for (const enemy of s.enemies) if (enemy.hp > 0) alive.push(enemy); else { s.combo = now < s.comboUntil ? s.combo + 1 : 1; s.comboUntil = now + 1500; const gain = 12 + s.wave * 2; s.score += gain * s.combo; s.xp += gain; sound(380, .07, .045); } s.enemies = alive; if (now > s.comboUntil) s.combo = 0;
  for (const spark of s.sparks) { spark.x += spark.vx * dt; spark.y += spark.vy * dt; spark.life -= dt; } s.sparks = s.sparks.filter(spark => spark.life > 0);
  if (s.xp >= s.nextXp) { s.xp -= s.nextXp; s.level++; s.nextXp = Math.round(s.nextXp * 1.28); s.choosing = true; showChoices(pick(upgrades, 3)); } if (s.spawned === s.target && s.enemies.length === 0) { s.wave++; s.spawned = 0; s.target = 7 + s.wave * 3; p.hp = Math.min(p.maxHp, p.hp + 12); }
}

function draw(ctx: CanvasRenderingContext2D, s: State, now: number) { for (const spark of s.sparks) { ctx.globalAlpha = spark.life / spark.max; ctx.fillStyle = `hsl(${spark.hue} 100% 65%)`; ctx.fillRect(spark.x, spark.y, 3, 3); } ctx.globalAlpha = 1; for (const bullet of s.bullets) { ctx.strokeStyle = bullet.friendly ? '#b8ffff' : '#ff71da'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(bullet.x, bullet.y); ctx.lineTo(bullet.x - bullet.vx * .022, bullet.y - bullet.vy * .022); ctx.stroke(); } for (const e of s.enemies) { ctx.save(); ctx.translate(e.x, e.y); ctx.rotate(now / 600); ctx.shadowBlur = 18; ctx.shadowColor = `hsl(${e.hue} 100% 60%)`; ctx.fillStyle = `hsl(${e.hue} 85% 55%)`; ctx.beginPath(); for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; const r = i % 2 ? e.r * .58 : e.r; i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r); } ctx.closePath(); ctx.fill(); ctx.restore(); } const p = s.player; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.angle); ctx.shadowBlur = 20; ctx.shadowColor = '#3bffff'; ctx.fillStyle = '#a6ffff'; ctx.fillRect(-8, -8, 18 + p.radius, 16); ctx.fillStyle = '#182454'; ctx.beginPath(); ctx.arc(0, 0, p.radius, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
