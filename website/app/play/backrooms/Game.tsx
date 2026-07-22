'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import * as THREE from 'three';

// ============================================================================
// CONSTANTS
// ============================================================================
const MAZE_SIZE = 25;
const WALL_SIZE = 4;
const WALL_HEIGHT = 4;
const PLAYER_HEIGHT = 1.6;
const MOVE_SPEED = 6;
const MOUSE_SENSITIVITY = 0.002;
const ENTITY_SPEED = 2.0;
const ENTITY_SPAWN_DELAY = 30000; // 30 seconds
const FOG_NEAR = 6;
const FOG_FAR = 30;

// ============================================================================
// MAZE GENERATION
// ============================================================================
function generateMaze(): boolean[][] {
  const grid: boolean[][] = [];
  for (let x = 0; x < MAZE_SIZE; x++) {
    grid[x] = [];
    for (let z = 0; z < MAZE_SIZE; z++) {
      if (x === 0 || x === MAZE_SIZE - 1 || z === 0 || z === MAZE_SIZE - 1) {
        grid[x][z] = true; // border
      } else if (Math.abs(x - 12) <= 2 && Math.abs(z - 12) <= 2) {
        grid[x][z] = false; // safe spawn
      } else {
        grid[x][z] = Math.random() < 0.28;
      }
    }
  }
  return grid;
}

// ============================================================================
// PAGE POSITIONS
// ============================================================================
function generatePages(maze: boolean[][]): { id: number; x: number; z: number; collected: boolean }[] {
  const offset = (MAZE_SIZE * WALL_SIZE) / 2;
  const pages: { id: number; x: number; z: number; collected: boolean }[] = [];
  let attempts = 0;
  while (pages.length < 8 && attempts < 500) {
    attempts++;
    const gx = Math.floor(Math.random() * (MAZE_SIZE - 4)) + 2;
    const gz = Math.floor(Math.random() * (MAZE_SIZE - 4)) + 2;
    if (!maze[gx][gz] && !(Math.abs(gx - 12) <= 2 && Math.abs(gz - 12) <= 2)) {
      pages.push({ id: pages.length, x: gx * WALL_SIZE - offset, z: gz * WALL_SIZE - offset, collected: false });
    }
  }
  return pages;
}

// ============================================================================
// AUDIO ENGINE
// ============================================================================
class AudioEngine {
  private ctx: AudioContext | null = null;
  private noiseBuffer: AudioBuffer | null = null;
  private lastFootstep = 0;
  private lastHeartbeat = 0;

  init() {
    if (this.ctx) return;
    this.ctx = new AudioContext();
    const bufSize = this.ctx.sampleRate * 2;
    this.noiseBuffer = this.ctx.createBuffer(1, bufSize, this.ctx.sampleRate);
    const data = this.noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;

    // Drone
    const droneGain = this.ctx.createGain(); droneGain.gain.value = 0.3; droneGain.connect(this.ctx.destination);
    const o1 = this.ctx.createOscillator(); o1.frequency.value = 40; o1.connect(droneGain); o1.start();
    const o2 = this.ctx.createOscillator(); o2.frequency.value = 42; o2.connect(droneGain); o2.start();
    const ring = this.ctx.createOscillator(); ring.frequency.value = 1100;
    const rg = this.ctx.createGain(); rg.gain.value = 0.006; ring.connect(rg); rg.connect(this.ctx.destination); ring.start();
  }

  playGunshot() {
    if (!this.ctx || !this.noiseBuffer) return;
    const t = this.ctx.currentTime;
    const crack = this.ctx.createBufferSource(); crack.buffer = this.noiseBuffer;
    const cf = this.ctx.createBiquadFilter(); cf.type = 'bandpass'; cf.frequency.value = 1200;
    const cg = this.ctx.createGain(); cg.gain.setValueAtTime(0.7, t); cg.gain.exponentialRampToValueAtTime(0.01, t + 0.15);
    crack.connect(cf); cf.connect(cg); cg.connect(this.ctx.destination); crack.start();
    const boom = this.ctx.createOscillator(); boom.type = 'sawtooth';
    boom.frequency.setValueAtTime(140, t); boom.frequency.exponentialRampToValueAtTime(30, t + 0.25);
    const bg = this.ctx.createGain(); bg.gain.setValueAtTime(1, t); bg.gain.exponentialRampToValueAtTime(0.01, t + 0.25);
    boom.connect(bg); bg.connect(this.ctx.destination); boom.start(); boom.stop(t + 0.25);
  }

  playScreech() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const c = this.ctx.createOscillator(); c.type = 'sawtooth';
    c.frequency.setValueAtTime(180, t); c.frequency.linearRampToValueAtTime(450, t + 0.4);
    const m = this.ctx.createOscillator(); m.frequency.value = 95;
    const mg = this.ctx.createGain(); mg.gain.value = 350; m.connect(mg); mg.connect(c.frequency);
    const g = this.ctx.createGain(); g.gain.setValueAtTime(0.35, t); g.gain.exponentialRampToValueAtTime(0.01, t + 0.45);
    c.connect(g); g.connect(this.ctx.destination); c.start(); m.start(); c.stop(t + 0.45); m.stop(t + 0.45);
  }

  playBuzz() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 60;
    const g = this.ctx.createGain(); g.gain.setValueAtTime(0.15, t); g.gain.exponentialRampToValueAtTime(0.01, t + 0.12);
    o.connect(g); g.connect(this.ctx.destination); o.start(); o.stop(t + 0.12);
  }

  update(isMoving: boolean, monsterDist: number) {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    if (isMoving && now - this.lastFootstep > 0.45) {
      this.lastFootstep = now;
      const o = this.ctx.createOscillator();
      o.frequency.setValueAtTime(75, now); o.frequency.exponentialRampToValueAtTime(25, now + 0.12);
      const g = this.ctx.createGain(); g.gain.setValueAtTime(0.15, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      o.connect(g); g.connect(this.ctx.destination); o.start(); o.stop(now + 0.12);
    }
    if (monsterDist < 25) {
      const interval = 0.35 + (monsterDist / 25) * 0.85;
      if (now - this.lastHeartbeat > interval) {
        this.lastHeartbeat = now;
        const vol = Math.max(0.08, 0.5 - (monsterDist / 25) * 0.45);
        const o = this.ctx.createOscillator();
        o.frequency.setValueAtTime(52, now); o.frequency.exponentialRampToValueAtTime(18, now + 0.14);
        const g = this.ctx.createGain(); g.gain.setValueAtTime(vol, now); g.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
        o.connect(g); g.connect(this.ctx.destination); o.start(); o.stop(now + 0.14);
      }
    }
  }
}

// ============================================================================
// TEXTURE GENERATORS
// ============================================================================
function makeWallTex(): THREE.CanvasTexture {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const x = c.getContext('2d')!;
  x.fillStyle = '#c8b88a'; x.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 5000; i++) {
    x.fillStyle = `rgba(${120 + Math.random() * 40}, ${110 + Math.random() * 30}, ${80 + Math.random() * 30}, 0.25)`;
    x.fillRect(Math.random() * 256, Math.random() * 256, 2, 2);
  }
  x.strokeStyle = '#a89970'; x.lineWidth = 1;
  for (let y = 0; y < 256; y += 64) { x.beginPath(); x.moveTo(0, y); x.lineTo(256, y); x.stroke(); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter;
  return t;
}

function makeFloorTex(): THREE.CanvasTexture {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const x = c.getContext('2d')!;
  x.fillStyle = '#5a5040'; x.fillRect(0, 0, 256, 256);
  x.strokeStyle = '#4a4230'; x.lineWidth = 2;
  for (let i = 0; i <= 256; i += 64) {
    x.beginPath(); x.moveTo(i, 0); x.lineTo(i, 256); x.stroke();
    x.beginPath(); x.moveTo(0, i); x.lineTo(256, i); x.stroke();
  }
  for (let i = 0; i < 3000; i++) {
    x.fillStyle = `rgba(${55 + Math.random() * 30}, ${45 + Math.random() * 25}, ${25 + Math.random() * 20}, 0.2)`;
    x.fillRect(Math.random() * 256, Math.random() * 256, 2, 2);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(12, 12);
  t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter;
  return t;
}

function makeCeilTex(): THREE.CanvasTexture {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const x = c.getContext('2d')!;
  x.fillStyle = '#d4cfc5'; x.fillRect(0, 0, 256, 256);
  x.strokeStyle = '#b5b0a0'; x.lineWidth = 2;
  for (let i = 0; i <= 256; i += 128) {
    x.beginPath(); x.moveTo(i, 0); x.lineTo(i, 256); x.stroke();
    x.beginPath(); x.moveTo(0, i); x.lineTo(256, i); x.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(12, 12);
  t.minFilter = THREE.NearestFilter; t.magFilter = THREE.NearestFilter;
  return t;
}

// ============================================================================
// PURE THREE.JS GAME (No R3F — direct WebGL rendering)
// ============================================================================
export default function Game() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [started, setStarted] = useState(false);
  const [gameOver, setGameOver] = useState<string | null>(null);
  const [collectedCount, setCollectedCount] = useState(0);

  const gameRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    clock: THREE.Clock;
    maze: boolean[][];
    pages: { id: number; x: number; z: number; collected: boolean; mesh: THREE.Mesh }[];
    entity: { mesh: THREE.Mesh; spawned: boolean; stunned: boolean; stunnedUntil: number } | null;
    keys: Record<string, boolean>;
    euler: THREE.Euler;
    isLocked: boolean;
    audio: AudioEngine;
    animationId: number;
    flashlight: THREE.SpotLight;
    flashTarget: THREE.Object3D;
    ambientLight: THREE.AmbientLight;
    dirLight: THREE.DirectionalLight;
    nextFlicker: number;
    flickering: boolean;
    lightBulbs: THREE.MeshBasicMaterial[];
    gunGroup: THREE.Group;
    isShooting: boolean;
    muzzleFlash: THREE.PointLight;
  } | null>(null);

  // Build the entire scene imperatively
  const initGame = useCallback(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.BasicShadowMap;
    renderer.setClearColor(0x0a0a08);
    container.appendChild(renderer.domElement);

    // Scene
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0a0a08, FOG_NEAR, FOG_FAR);

    // Camera
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, PLAYER_HEIGHT, 0);

    // Maze
    const maze = generateMaze();
    const offset = (MAZE_SIZE * WALL_SIZE) / 2;

    // Textures
    const wallTex = makeWallTex();
    const floorTex = makeFloorTex();
    const ceilTex = makeCeilTex();

    // Floor
    const floorGeo = new THREE.PlaneGeometry(MAZE_SIZE * WALL_SIZE, MAZE_SIZE * WALL_SIZE);
    const floorMat = new THREE.MeshStandardMaterial({ map: floorTex, roughness: 1, metalness: 0 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    // Ceiling
    const ceilGeo = new THREE.PlaneGeometry(MAZE_SIZE * WALL_SIZE, MAZE_SIZE * WALL_SIZE);
    const ceilMat = new THREE.MeshStandardMaterial({ map: ceilTex, roughness: 1, metalness: 0 });
    const ceil = new THREE.Mesh(ceilGeo, ceilMat);
    ceil.position.y = WALL_HEIGHT;
    ceil.rotation.x = Math.PI / 2;
    ceil.receiveShadow = true;
    scene.add(ceil);

    // Walls (InstancedMesh)
    let wallCount = 0;
    for (let x = 0; x < MAZE_SIZE; x++)
      for (let z = 0; z < MAZE_SIZE; z++)
        if (maze[x][z]) wallCount++;

    const wallGeo = new THREE.BoxGeometry(WALL_SIZE, WALL_HEIGHT, WALL_SIZE);
    const wallMat = new THREE.MeshStandardMaterial({ map: wallTex, roughness: 1, metalness: 0 });
    const walls = new THREE.InstancedMesh(wallGeo, wallMat, wallCount);
    walls.castShadow = true;
    walls.receiveShadow = true;

    const dummy = new THREE.Object3D();
    let idx = 0;
    for (let x = 0; x < MAZE_SIZE; x++) {
      for (let z = 0; z < MAZE_SIZE; z++) {
        if (maze[x][z]) {
          dummy.position.set(x * WALL_SIZE - offset, WALL_HEIGHT / 2, z * WALL_SIZE - offset);
          dummy.updateMatrix();
          walls.setMatrixAt(idx++, dummy.matrix);
        }
      }
    }
    walls.instanceMatrix.needsUpdate = true;
    scene.add(walls);

    // Ceiling light fixtures + point lights
    const lightBulbs: THREE.MeshBasicMaterial[] = [];
    for (let x = 2; x < MAZE_SIZE - 2; x += 3) {
      for (let z = 2; z < MAZE_SIZE - 2; z += 3) {
        if (!maze[x][z]) {
          const fx = x * WALL_SIZE - offset;
          const fz = z * WALL_SIZE - offset;

          // Fixture housing
          const housing = new THREE.Mesh(
            new THREE.BoxGeometry(1.6, 0.08, 0.6),
            new THREE.MeshStandardMaterial({ color: 0x404040, roughness: 1, metalness: 0 })
          );
          housing.position.set(fx, WALL_HEIGHT - 0.05, fz);
          scene.add(housing);

          // Glowing bulb panel
          const bulbMat = new THREE.MeshBasicMaterial({ color: 0xfffae6 });
          lightBulbs.push(bulbMat);
          const bulb = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.01, 0.5), bulbMat);
          bulb.position.set(fx, WALL_HEIGHT - 0.09, fz);
          scene.add(bulb);

          // Point light per fixture
          const pl = new THREE.PointLight(0xfffae6, 1.5, 16, 2);
          pl.position.set(fx, WALL_HEIGHT - 0.2, fz);
          scene.add(pl);
        }
      }
    }

    // Ambient & Directional light
    const ambientLight = new THREE.AmbientLight(0xfffcf0, 0.45);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xfffae6, 0.5);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.set(1024, 1024);
    dirLight.shadow.camera.far = 30;
    dirLight.shadow.camera.left = -15;
    dirLight.shadow.camera.right = 15;
    dirLight.shadow.camera.top = 15;
    dirLight.shadow.camera.bottom = -15;
    dirLight.shadow.bias = -0.0005;
    dirLight.position.set(10, 12, 10);
    scene.add(dirLight);
    scene.add(dirLight.target);

    // Flashlight
    const flashTarget = new THREE.Object3D();
    scene.add(flashTarget);
    const flashlight = new THREE.SpotLight(0xfff5dd, 22, 40, Math.PI / 7, 0.15, 1.4);
    flashlight.castShadow = true;
    flashlight.shadow.mapSize.set(512, 512);
    flashlight.shadow.bias = -0.0001;
    flashlight.target = flashTarget;
    scene.add(flashlight);

    // Gun model
    const gunGroup = new THREE.Group();
    const gunMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 1, metalness: 0 });
    const slideMat = new THREE.MeshStandardMaterial({ color: 0x2d2d30, roughness: 1, metalness: 0 });

    const slide = new THREE.Mesh(new THREE.BoxGeometry(0.038, 0.04, 0.28), slideMat);
    slide.position.set(0, 0.01, -0.04); gunGroup.add(slide);
    const frame = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.05, 0.22), gunMat);
    frame.position.set(0, -0.04, 0); gunGroup.add(frame);
    const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.06, 8), gunMat);
    barrel.position.set(0, 0.012, -0.19); barrel.rotation.x = Math.PI / 2; gunGroup.add(barrel);
    const grip = new THREE.Mesh(new THREE.BoxGeometry(0.033, 0.14, 0.065), gunMat);
    grip.position.set(0, -0.14, 0.04); grip.rotation.x = 0.22; gunGroup.add(grip);
    scene.add(gunGroup);

    // Muzzle flash light (hidden initially)
    const muzzleFlash = new THREE.PointLight(0xffbb44, 0, 8, 2);
    gunGroup.add(muzzleFlash);

    // Pages
    const pageObjs = generatePages(maze);
    const pageMeshes = pageObjs.map((p) => {
      const m = new THREE.Mesh(
        new THREE.BoxGeometry(0.3, 0.4, 0.02),
        new THREE.MeshBasicMaterial({ color: 0xee2222 })
      );
      m.position.set(p.x, 1.5, p.z);
      scene.add(m);

      const pl = new THREE.PointLight(0xff0000, 0.8, 6);
      pl.position.set(p.x, 1.5, p.z);
      scene.add(pl);

      return { ...p, mesh: m };
    });

    // Entity (not spawned yet)
    const entityMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.4, 0.4, 4, 16),
      new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 1, metalness: 0 })
    );
    entityMesh.position.set(0, 2, -40);
    entityMesh.visible = false;
    scene.add(entityMesh);

    // Audio
    const audio = new AudioEngine();
    audio.init();

    // Input
    const keys: Record<string, boolean> = {};
    const euler = new THREE.Euler(0, 0, 0, 'YXZ');
    let isLocked = false;

    const onKeyDown = (e: KeyboardEvent) => { keys[e.code] = true; };
    const onKeyUp = (e: KeyboardEvent) => { keys[e.code] = false; };
    const onMouseMove = (e: MouseEvent) => {
      if (!isLocked) return;
      euler.y -= e.movementX * MOUSE_SENSITIVITY;
      euler.x -= e.movementY * MOUSE_SENSITIVITY;
      euler.x = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, euler.x));
      camera.quaternion.setFromEuler(euler);
    };
    const onClick = () => {
      if (!isLocked) {
        renderer.domElement.requestPointerLock();
        return;
      }
      if (game.isShooting) return;
      game.isShooting = true;
      audio.playGunshot();
      muzzleFlash.intensity = 12;

      // Check entity hit
      if (game.entity && game.entity.spawned && !game.entity.stunned) {
        const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
        const toE = new THREE.Vector3().subVectors(entityMesh.position, camera.position);
        const dist = toE.length();
        toE.normalize();
        if (dir.dot(toE) > 0.85 && dist < 25) {
          game.entity.stunned = true;
          game.entity.stunnedUntil = clock.getElapsedTime() + 1.2;
          audio.playScreech();
          const push = new THREE.Vector3().subVectors(entityMesh.position, camera.position);
          push.y = 0; push.normalize();
          entityMesh.position.add(push.multiplyScalar(15));
          (entityMesh.material as THREE.MeshStandardMaterial).color.set(0xaa0000);
          (entityMesh.material as THREE.MeshStandardMaterial).emissive.set(0x330000);
        }
      }

      setTimeout(() => {
        game.isShooting = false;
        muzzleFlash.intensity = 0;
      }, 100);
    };
    const onLockChange = () => {
      isLocked = document.pointerLockElement === renderer.domElement;
      game.isLocked = isLocked;
    };
    const onResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    document.addEventListener('mousemove', onMouseMove);
    renderer.domElement.addEventListener('click', onClick);
    document.addEventListener('pointerlockchange', onLockChange);
    window.addEventListener('resize', onResize);

    // Spawn entity after delay
    const spawnTimer = setTimeout(() => {
      if (game.entity) {
        game.entity.spawned = true;
        entityMesh.visible = true;
      }
    }, ENTITY_SPAWN_DELAY);

    const clock = new THREE.Clock();

    const game = {
      renderer, scene, camera, clock, maze, pages: pageMeshes,
      entity: { mesh: entityMesh, spawned: false, stunned: false, stunnedUntil: 0 },
      keys, euler, isLocked, audio, animationId: 0,
      flashlight, flashTarget, ambientLight, dirLight,
      nextFlicker: 5, flickering: false, lightBulbs,
      gunGroup, isShooting: false, muzzleFlash,
    };

    // ====== GAME LOOP ======
    let collected = 0;

    function animate() {
      game.animationId = requestAnimationFrame(animate);
      const delta = Math.min(clock.getDelta(), 0.05);
      const elapsed = clock.getElapsedTime();

      // ---- Player Movement ----
      const fwd = Number(keys['KeyW'] || keys['ArrowUp']) - Number(keys['KeyS'] || keys['ArrowDown']);
      const strafe = Number(keys['KeyD'] || keys['ArrowRight']) - Number(keys['KeyA'] || keys['ArrowLeft']);

      if (fwd !== 0 || strafe !== 0) {
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
        right.y = 0; right.normalize();
        const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
        forward.y = 0; forward.normalize();

        const move = new THREE.Vector3();
        move.add(forward.multiplyScalar(-fwd * MOVE_SPEED * delta));
        move.add(right.multiplyScalar(strafe * MOVE_SPEED * delta));

        const newPos = camera.position.clone().add(move);
        const gx = Math.floor((newPos.x + offset + WALL_SIZE / 2) / WALL_SIZE);
        const gz = Math.floor((newPos.z + offset + WALL_SIZE / 2) / WALL_SIZE);
        if (gx >= 0 && gx < MAZE_SIZE && gz >= 0 && gz < MAZE_SIZE && !maze[gx][gz]) {
          camera.position.add(move);
        }
      }

      // Head bob
      const isMoving = fwd !== 0 || strafe !== 0;
      camera.position.y = isMoving
        ? PLAYER_HEIGHT + Math.sin(elapsed * 8) * 0.05
        : PLAYER_HEIGHT + Math.cos(elapsed) * 0.002;

      // ---- Flashlight ----
      flashlight.position.copy(camera.position);
      flashlight.position.y -= 0.15;
      const lookDir = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
      flashTarget.position.copy(camera.position).add(lookDir.multiplyScalar(10));

      // ---- Gun follow ----
      gunGroup.position.copy(camera.position);
      gunGroup.quaternion.copy(camera.quaternion);
      gunGroup.translateX(0.22);
      gunGroup.translateY(-0.22);
      gunGroup.translateZ(-0.5);
      if (isMoving) {
        gunGroup.translateY(Math.sin(elapsed * 8) * 0.012);
        gunGroup.translateX(Math.cos(elapsed * 4) * 0.008);
      }

      // ---- Dynamic shadow tracking ----
      dirLight.position.set(camera.position.x + 5, 12, camera.position.z + 5);
      dirLight.target.position.set(camera.position.x, 0, camera.position.z);
      dirLight.target.updateMatrixWorld();

      // ---- Light flicker ----
      if (elapsed > game.nextFlicker) {
        game.flickering = true;
        game.nextFlicker = elapsed + Math.random() * 6 + 4;
      }
      if (game.flickering) {
        const dim = Math.random() < 0.45;
        ambientLight.intensity = dim ? 0.08 : 0.45;
        dirLight.intensity = dim ? 0.05 : 0.5;
        lightBulbs.forEach((m) => m.color.set(dim ? 0x332a18 : 0xfffae6));
        if (dim && Math.random() < 0.25) audio.playBuzz();
        if (Math.random() < 0.12) game.flickering = false;
      } else {
        ambientLight.intensity = 0.45;
        dirLight.intensity = 0.5;
        lightBulbs.forEach((m) => m.color.set(0xfffae6));
      }

      // ---- Page collection ----
      pageMeshes.forEach((p) => {
        if (!p.collected) {
          p.mesh.rotation.y = elapsed * 1.5 + p.id;
          if (camera.position.distanceTo(p.mesh.position) < 2.5) {
            p.collected = true;
            p.mesh.visible = false;
            collected++;
            setCollectedCount(collected);
            if (collected >= 8) {
              setGameOver('You escaped Level 0!');
            }
          }
        }
      });

      // ---- Entity AI ----
      if (game.entity && game.entity.spawned) {
        const ent = game.entity;
        if (ent.stunned && elapsed > ent.stunnedUntil) {
          ent.stunned = false;
          (entityMesh.material as THREE.MeshStandardMaterial).color.set(0x050505);
          (entityMesh.material as THREE.MeshStandardMaterial).emissive.set(0x000000);
        }
        if (!ent.stunned) {
          const toPlayer = new THREE.Vector3().subVectors(camera.position, entityMesh.position);
          toPlayer.y = 0;
          const dist = toPlayer.length();
          if (dist < 1.5) {
            setGameOver('The entity caught you.');
          } else if (dist < 45) {
            toPlayer.normalize();
            entityMesh.position.add(toPlayer.multiplyScalar(ENTITY_SPEED * delta));
            entityMesh.lookAt(camera.position.x, entityMesh.position.y, camera.position.z);
          }
        }
      }

      // ---- Audio ----
      const monsterDist = game.entity?.spawned ? camera.position.distanceTo(entityMesh.position) : 999;
      audio.update(isMoving, monsterDist);

      // ---- Render ----
      renderer.render(scene, camera);
    }

    animate();
    gameRef.current = game;

    // Cleanup
    return () => {
      cancelAnimationFrame(game.animationId);
      clearTimeout(spawnTimer);
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      document.removeEventListener('mousemove', onMouseMove);
      renderer.domElement.removeEventListener('click', onClick);
      document.removeEventListener('pointerlockchange', onLockChange);
      window.removeEventListener('resize', onResize);
      if (document.pointerLockElement === renderer.domElement) document.exitPointerLock();
      renderer.dispose();
      if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement);
    };
  }, []);

  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!started || gameOver) return;
    const cleanup = initGame();
    cleanupRef.current = cleanup || null;
    return () => { cleanup?.(); cleanupRef.current = null; };
  }, [started, gameOver, initGame]);

  return (
    <div style={{
      width: '100vw', height: '100vh', background: '#000',
      overflow: 'hidden', position: 'relative',
      fontFamily: '"Courier New", Courier, monospace',
      color: '#fff', userSelect: 'none',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        aspectRatio: '4/3', height: '100%', maxWidth: '100%',
        position: 'relative',
        border: '10px solid #181715',
        boxShadow: '0 0 60px rgba(0,0,0,0.8)',
        overflow: 'hidden', background: '#0a0a08',
      }}>
        {/* 3D Canvas renders here */}
        {started && !gameOver && (
          <>
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
            {/* HUD Overlay */}
            <HUD collectedCount={collectedCount} />
          </>
        )}

        {/* Start / Game Over */}
        {(!started || gameOver) && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 20,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.92)',
          }}>
            {!started ? (
              <div style={{ textAlign: 'center', maxWidth: '600px', padding: '0 24px' }}>
                <h1 style={{
                  fontSize: 'clamp(3rem, 8vw, 6rem)', fontWeight: 'bold',
                  letterSpacing: '0.2em', color: '#e8b547',
                  marginBottom: '32px',
                  textShadow: '0 0 30px rgba(255,200,100,0.4)',
                }}>
                  LEVEL 0
                </h1>
                <p style={{
                  fontSize: '1.1rem', color: '#e8dfc8',
                  marginBottom: '48px', lineHeight: 1.8,
                  letterSpacing: '0.05em',
                }}>
                  You noclipped out of reality.<br /><br />
                  Find 8 pages before the entity finds you.<br />
                  Click to lock mouse. WASD to move. Click to shoot.
                </p>
                <button
                  onClick={() => setStarted(true)}
                  style={{
                    padding: '16px 48px', background: '#e8b547',
                    color: '#000', fontWeight: 'bold', fontSize: '1.1rem',
                    letterSpacing: '0.3em', border: 'none', cursor: 'pointer',
                    fontFamily: '"Courier New", monospace',
                  }}
                  onMouseEnter={(e) => { (e.target as HTMLButtonElement).style.background = '#fff'; }}
                  onMouseLeave={(e) => { (e.target as HTMLButtonElement).style.background = '#e8b547'; }}
                >
                  ENTER THE BACKROOMS
                </button>
              </div>
            ) : (
              <div style={{ textAlign: 'center', maxWidth: '600px', padding: '0 24px' }}>
                <h2 style={{
                  fontSize: '2.5rem', fontWeight: 'bold',
                  letterSpacing: '0.15em',
                  color: gameOver?.includes('escaped') ? '#44dd66' : '#ee3333',
                  marginBottom: '24px',
                  textShadow: gameOver?.includes('escaped') ? '0 0 15px rgba(68,221,102,0.5)' : '0 0 15px rgba(255,50,50,0.5)',
                }}>
                  {gameOver}
                </h2>
                <button
                  onClick={() => window.location.reload()}
                  style={{
                    padding: '12px 36px',
                    border: `1px solid ${gameOver?.includes('escaped') ? '#44dd66' : '#ee3333'}`,
                    background: 'transparent',
                    color: gameOver?.includes('escaped') ? '#44dd66' : '#ee3333',
                    fontWeight: 'bold', letterSpacing: '0.2em', cursor: 'pointer',
                    fontFamily: '"Courier New", monospace', fontSize: '1rem',
                  }}
                >
                  RESTART TAPE
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// HUD
// ============================================================================
function HUD({ collectedCount }: { collectedCount: number }) {
  const [blink, setBlink] = useState(true);
  useEffect(() => {
    const iv = setInterval(() => setBlink((b) => !b), 450);
    return () => clearInterval(iv);
  }, []);

  return (
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 10,
      fontFamily: '"Courier New", Courier, monospace', color: '#fff',
    }}>
      <div style={{ position: 'absolute', top: 24, left: 28, display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 18, height: 18, borderRadius: '50%',
          background: blink ? '#ff2222' : 'transparent',
          boxShadow: blink ? '0 0 8px #ff0000' : 'none',
        }} />
        <span style={{ color: '#ff2222', fontSize: 22, fontWeight: 'bold', letterSpacing: 4 }}>REC</span>
      </div>
      <div style={{ position: 'absolute', top: 24, right: 28, color: '#ccc', fontSize: 20 }}>SP 0:00:00</div>
      <div style={{
        position: 'absolute', bottom: 28, left: 28,
        color: '#ffdd44', fontSize: 26, fontWeight: 'bold',
        textShadow: '0 0 10px rgba(255,220,70,0.3)',
      }}>
        PAGES: {collectedCount}/8
      </div>
      <div style={{ position: 'absolute', bottom: 28, right: 28, color: 'rgba(220,215,200,0.4)', fontSize: 14, textAlign: 'right', lineHeight: '1.8' }}>
        WASD — MOVE<br />MOUSE — LOOK<br />CLICK — FIRE
      </div>
      <div style={{
        position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        width: 4, height: 4, borderRadius: '50%',
        background: 'rgba(255,255,255,0.35)',
        boxShadow: '0 0 4px rgba(255,255,255,0.15)',
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px)',
      }} />
    </div>
  );
}
