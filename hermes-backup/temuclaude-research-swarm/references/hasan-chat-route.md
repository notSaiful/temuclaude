# Hasan Chat Route — Architecture & Debugging Guide

## File Location
`website/app/api/hasan/chat/route.ts`

## Overview
The chat route is the core of Hasan's conversational interface. It:
1. Gathers live system context (daemon heartbeats, queue, SWOT, events)
2. Reads git history at runtime (last 15 commits, uncommitted changes, 7-day file changes)
3. Scans project structure (src, website, tests, research, staging directories)
4. Loads static project context from `research/project_context.json`
5. Builds a comprehensive system prompt with Hasan's identity, mission, rules
6. Tries Ollama cloud models (glm-5.2 primary → fallbacks)
7. Falls back to OpenRouter free models
8. Returns offline response if all LLMs fail

## Model Configuration

### Ollama Cloud (Primary — works without local daemon)
```
URL: https://ollama.com:443/api/chat
Auth: Bearer <OLLAMA_CLOUD_KEY>
Model names: NO :cloud suffix (e.g., "glm-5.2" not "glm-5.2:cloud")
```

### Ollama Local (Secondary — needs daemon running)
```
URL: http://localhost:11434/api/chat
Auth: None (local daemon)
Model names: REQUIRES :cloud suffix (e.g., "glm-5.2:cloud")
```

### OpenRouter (Final fallback — rate-limited)
```
URL: https://openrouter.ai/api/v1/chat/completions
Auth: Bearer <OPENROUTER_API_KEY>
Model names: Full OpenRouter IDs (e.g., "nvidia/nemotron-3-ultra-550b-a55b:free")
Rate limit: 50 requests/day for free models
```

## Model Priority & Load Balancing
1. **glm-5.2** (PRIMARY) — always tried first. 756B params, 1M context, fast.
2. **deepseek-v4-pro** — fallback 1. 1M context, strong reasoning.
3. **kimi-k2.6** — fallback 2. 1T params, vision capable.
4. **gpt-oss:120b** — fallback 3. 116.8B params, 131k context.

Each failed model gets a 60-second cooldown (`FAILURE_COOLDOWN_MS = 60000`). Only rotates to fallbacks if primary is in cooldown. Primary is always retried first once cooldown expires.

## Key Fixes Applied

### 1. Empty Content from Ollama Cloud Models
**Problem**: `glm-5.2:cloud` returns `{"message": {"content": "", "thinking": "..."}}` — the actual response is in `thinking`, not `content`.
**Cause**: With low `num_predict` (e.g., 5-50), the thinking process consumes all tokens before generating content.
**Fix**: 
- Always use `num_predict: 800` for chat
- Check `data.message.thinking` as fallback when `data.message.content` is empty

### 2. Ollama Cloud Direct API Auth
**Problem**: Direct calls to `https://ollama.com:443/api/chat` with the old API key returned `{"error":"Unauthorized"}`.
**Cause**: The local Ollama daemon uses SSH keys (id_ed25519) to authenticate with ollama.com. The direct cloud API uses a separate API key (Bearer token format: 32-char hex + dot + base64 suffix).
**Fix**: Use the new Ollama cloud key directly as Bearer token. Model names have NO `:cloud` suffix for direct API.

### 3. Timeout Chain Exceeding maxDuration
**Problem**: When Ollama cloud is unreachable, 3 model attempts × 30s timeout = 90s, but Next.js `maxDuration` is 60s. Request times out before reaching OpenRouter fallback.
**Fix**: 
- Quick health check (`/api/version` with 3s timeout) before trying models
- Per-model timeout reduced to 8s (cloud) and 8s (local)
- If Ollama unreachable, skip straight to OpenRouter

### 4. Stale PID Files Blocking Daemon Restart
**Problem**: Daemons refuse to start if PID file exists, even when process is dead.
**Fix**: Force-remove ALL PID and heartbeat files before starting:
```bash
rm -f /tmp/temuclaude_daemons/*.pid /tmp/temuclaude_daemons/*_heartbeat.json
```

## Environment Variables (website/.env)
```
OLLAMA_CLOUD_URL=https://ollama.com:443
OLLAMA_CLOUD_KEY=<32-char hex>.<base64 suffix>
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=<32-char hex>  (for local daemon)
OPENROUTER_API_KEY=sk-or-v1-<...>
```

**Gotcha**: Next.js .env file overrides shell env vars. To test fallback paths, edit .env directly or rename it temporarily. Setting `OLLAMA_CLOUD_URL=http://localhost:9999` in shell does NOT work — .env wins.

## Power Toggle API
`website/app/api/hasan/power/route.ts`

- `GET /api/hasan/power` — returns `{status: "active"|"deactivated", alive: N, total: 23}`
- `POST /api/hasan/power` with `{action: "activate"}` — clears PID files, runs `start_swarm.sh`, counts alive daemons
- `POST /api/hasan/power` with `{action: "deactivate"}` — SIGTERM all daemons, wait 2s, SIGKILL survivors, clean PID files

UI polls power state every 5 seconds. Header shows green ACTIVATE or red DEACTIVATE button.

## Deploy API
`website/app/api/hasan/deploy/route.ts`

- `GET` — returns pending_findings, staging_count, approved_count, rejected_count, agent_scaling state
- `POST` actions:
  - `approve` — mark finding as approved, move to approved_deployments
  - `reject` — mark finding as rejected, move to rejected_deployments
  - `approve_all` — approve all pending findings
  - `request_permission` — mark in_staging findings as pending_approval, set next_permission_eligible to +7 days
  - `scale_agents` — set current_research_agents (1-8), log to history

## Verification Tests (12 checks)
```bash
# Start server
cd /Users/saiful/temuclaude/website && npx next start -p 3952 &
sleep 4

# 1. Page loads (HTTP 200)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3952/hasan

# 2. Status API
curl -s http://localhost:3952/api/hasan | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'], d['identity']['verified'])"

# 3-6. Chat tests (who are you, math, system status, SWOT)
curl -s -X POST http://localhost:3952/api/hasan/chat -H 'Content-Type: application/json' -d '{"message":"Who are you?"}'

# 7. Model priority (all should be glm-5.2)
for i in 1 2 3; do curl -s -X POST http://localhost:3952/api/hasan/chat -H 'Content-Type: application/json' -d '{"message":"Say hi in 3 words"}'; done

# 8. Identity API
curl -s http://localhost:3952/api/hasan/identity

# 9. Deploy API
curl -s http://localhost:3952/api/hasan/deploy

# 10. Power API
curl -s http://localhost:3952/api/hasan/power

# 11. Instruction following
curl -s -X POST http://localhost:3952/api/hasan/chat -H 'Content-Type: application/json' -d '{"message":"Focus on researching speculative decoding for 2 hours"}'

# 12. Hasan identity integrity
cd /Users/saiful/temuclaude && python3 research/hasan_identity.py
```

## System Prompt Structure
The system prompt contains these sections in order:
1. Hasan identity (named after Hasan ibn Ali RA)
2. Creator (Ggs, Nagpur, story)
3. 7 mission priorities
4. 7 moral principles
5. Staging & deployment rules (codebase only — everything else autonomous)
6. Agent scaling protocol
7. Instruction following rules
8. Shared intelligence system + self-healing watchdog + always-run systems list
9. About Ggs (personality, mission statement)
10. Live system context (daemon heartbeats, queue, SWOT, events)
11. Project overview (architecture, pricing, tech stack)
12. Live git context (last 15 commits, uncommitted changes, recent files)
13. Project structure (directory listing, staging contents, deployment queue)
14. Shared intelligence (events, swarm state, knowledge facts, watchdog status)
15. Response style instruction (concise, 3-5 sentences)

## Shared Intelligence Injection
`gatherSharedIntelligence()` reads from 3 files at request time:
- `shared_state/events.json` — last 15 events from all daemons
- `shared_state/swarm_state.json` — alive daemon count
- `shared_state/knowledge.json` — last 10 shared facts
- `watchdog_heartbeat.json` — watchdog status

This is injected into the system prompt so Hasan sees what every daemon is doing and what the swarm has learned. See `references/shared-intelligence.md` for the hub API.

## Self-Healing Watchdog
`research/watchdog.py` — monitors all 23 daemons every 15 seconds.

- Detects: dead process, stale PID file, missing PID file, stale heartbeat (>120s)
- Auto-restarts crashed daemons with 30s cooldown between restarts
- Max 3 restarts per check cycle (prevents restart storms)
- Logs all actions to `/tmp/temuclaude_daemons/watchdog.log`
- Health summary every 60s (4 cycles)
- Started/stopped automatically with ACTIVATE/DEACTIVATE button (power API)
- Writes own heartbeat to `watchdog_heartbeat.json` + PID to `watchdog.pid`

**Pitfall**: Daemon scripts check for their own PID file at startup and refuse to start if it exists. The watchdog must delete the stale PID file AND heartbeat file BEFORE spawning the daemon process. The daemon writes its own new PID file on startup — the watchdog should NOT write the PID file. Wait 2s after spawn for daemon to write its own PID, then verify.

**Test**: Kill a daemon with `kill -9 <pid>`, wait 15-20s, verify watchdog restarted it with a new PID.

### Power API + Watchdog Integration
- `POST /api/hasan/power {action: "activate"}` — starts swarm AND watchdog (spawned as detached process)
- `POST /api/hasan/power {action: "deactivate"}` — kills watchdog FIRST (so it doesn't restart daemons being stopped), then kills all daemons
- Watchdog PID file: `/tmp/temuclaude_daemons/watchdog.pid`

## Permission Model (Ggs's Rule — CRITICAL)

**Permission is ONLY for codebase deployment. Everything else runs autonomously 24/7.**

- Hasan works in `/staging/` for all code experiments — NO permission needed for staging
- Once per week, Hasan marks findings as `pending_approval` and notifies Ggs
- Ggs approves/rejects via the Deploy tab in the UI
- Only approved findings merge into the main codebase
- **EVERYTHING ELSE runs without asking**: marketing, research, agent scaling, monitoring, daemons, SWOT, competitive intelligence, social media, growth, revenue tracking, Ummah fund

This was corrected by Ggs mid-session. The initial implementation was too restrictive (asking permission for everything). Ggs clarified: "The only permission for Hasan is before implementing the changes in the real codebase. Other than that, it can do everything and doesn't require any permission." And: "marketing automations and things other than the codebase shall run successfully all the time."

## Instruction Following

Hasan treats Ggs's chat messages as **commands**, not just questions:
- Code instructions → done in `/staging/`, report back what was done
- Non-code instructions (marketing, research, agents, monitoring) → execute immediately and autonomously
- If unsure what Ggs means → ask a brief clarifying question
- Handles any instruction type: system changes, research directions, agent adjustments, content creation, analysis tasks

## Live Codebase Awareness

Hasan reads git history at runtime (every chat request) so it always knows the latest changes:
- `gatherGitContext()`: last 15 commits, uncommitted changes, files changed in 7 days, current branch, total commit count
- `gatherProjectStructure()`: scans src/website/tests/research/staging directories, deployment queue state
- Any commit (past or future) is automatically visible to Hasan on next chat request — no manual updates needed
- Static `project_context.json` provides architecture/pricing overview; live git provides current state

## Ollama Cloud Key Formats

Two different key formats exist:
1. **Local daemon key** (`OLLAMA_API_KEY`): 32-char hex string (e.g., `451b60551d11471d8d7db094c4ad874d`). Used by local Ollama daemon to authenticate with ollama.com via SSH keys.
2. **Direct cloud API key** (`OLLAMA_CLOUD_KEY`): 32-char hex + dot + base64 suffix (e.g., `eb9bdf87921344e6a5b471694fd86fc5.A56ktEEgXsvcwqg2yL10hP69`). Used for direct calls to `https://ollama.com:443/api/chat` with Bearer auth. Works without local daemon.

## Hasan Identity File
`research/hasan_identity.py` — IMMUTABLE constitution. 16 never-do rules, 7 principles, 7 missions. Every daemon verifies integrity at startup via `verify_integrity()`.

### Never-Do Rules (16 total, updated 2026-07-07)
The key additions for staging/deployment:
- Never touch the main codebase (/src, /website/app, /website/lib, /tests). All code goes to /staging/ only.
- Everything else (marketing, research, agent scaling, monitoring, daemons, SWOT, competitive intelligence, social media, growth, revenue, Ummah fund) runs autonomously 24/7 without permission.
- Never deploy code changes to main without Ggs's permission. The ONLY permission required is for codebase deployment.
- Never remove or disable the staging area or deployment queue system.