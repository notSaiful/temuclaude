# Phase 5 Plan — Production Deployment

## What We're Building

Phase 5 takes Timuclaude from a development project to a production-ready API service. This includes: Dockerfile for deployment, a start script that runs the LiteLLM proxy with our orchestrator, an in-memory cache, a landing page, and a Dockerfile for Fly.io.

## Components

### 1. start.sh — Production Start Script
- Starts LiteLLM proxy with our config
- Sets environment variables
- Health check endpoint
- Graceful shutdown

### 2. Dockerfile — Container for Fly.io
- Python 3.11 slim base
- Install requirements
- Copy source + config
- Start LiteLLM proxy
- Expose port 4000

### 3. .dockerignore — Docker build exclusions
- Exclude .git, __pycache__, logs, .env, research docs

### 4. cache.py — In-Memory Response Cache
- Cache identical requests (same prompt → same response)
- LRU eviction (max 1000 entries)
- TTL: 1 hour
- Saves API calls for repeated questions

### 5. landing_page.html — Simple Landing Page
- What Timuclaude is
- Benchmark results placeholder
- API documentation link
- Pricing tiers
- GitHub link
- Warm minimal design (matching Ggs's preferences)

### 6. fly.toml — Fly.io Deployment Config
- App name: timuclaude
- Region: closest to user
- Port: 4000
- Auto-scaling: 1-3 instances

### 7. tests/test_phase5.py — Phase 5 Tests
- Test cache (set, get, eviction, TTL)
- Test start script syntax
- Test Dockerfile syntax
- Test landing page exists and has content
- Test fly.toml exists and has correct config

## File Changes
1. NEW: start.sh
2. NEW: Dockerfile
3. NEW: .dockerignore
4. NEW: src/cache.py
5. NEW: landing_page.html
6. NEW: fly.toml
7. NEW: tests/test_phase5.py
8. MODIFY: README.md — add Phase 5 status + deployment instructions
9. MODIFY: requirements.txt — no new packages needed

## What's NOT in Phase 5
- Redis cache (Phase 6 — production scaling)
- Postgres database (Phase 6 — cost tracking at scale)
- Custom domain setup (Phase 6)
- CI/CD pipeline (Phase 6)
- Marketing site (Phase 6 — separate session)
- Official benchmark submission (Phase 6)