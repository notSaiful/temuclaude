# Current Cron Job Configuration (as of 2026-07-03)

All 8 jobs active and running 24/7.

| Job ID | Name | Schedule | Type | Workdir | Status |
|--------|------|----------|------|---------|--------|
| `387688d82a5a` | Scout-arXiv + GitHub + HuggingFace | `0 4,16 * * *` (2× daily) | Script (`no_agent=true`) | `/Users/saiful/temuclaude/research` | ✅ ACTIVE |
| `aa2649e8061c` | RANK 1 — Dynamic Deep Research | `0 2,10,18 * * *` (3× daily) | Agent | `/Users/saiful/temuclaude/research` | ✅ ACTIVE |
| `ba16699034a9` | RANK 2 — Competitive Intelligence | `0 6,14 * * *` (2× daily) | Agent | `/Users/saiful/temuclaude/research` | ✅ ACTIVE (last error 2026-07-05) |
| `c332087ad4e2` | RANK 3 — Development Scan | `0 12 * * *` (daily) | Agent | `/Users/saiful/temuclaude/research` | ✅ ACTIVE |
| `77872248bce3` | RANK 4 — Headline Scan | `0 0 * * 0` (weekly Sun) | Agent | `/Users/saiful/temuclaude/research` | ✅ ACTIVE |
| `1e046581cc53` | Auto-Integrator | `0 1 * * *` (daily 1am) | Agent | `/Users/saiful/temuclaude` | ✅ ACTIVE (ran 2026-07-03 15:27 IST) |
| `4bfd63cf51d6` | Agentive Weekly Plan | `0 20 * * 0` (Sun 8pm) | Script | (root) | ✅ ACTIVE |
| `f23172a317e5` | Timuclaude Daily Post | `30 16 * * *` (4:30pm) | Agent | `/Users/saiful/temuclaude` | ⏸️ PAUSED |

## Key Configuration Notes

### Auto-Integrator Model Pinning
The Auto-Integrator job (`1e046581cc53`) required explicit model pinning due to global inference config drift:

```bash
cronjob action=update job_id=1e046581cc53 provider=openrouter model=nvidia/nemotron-3-ultra-550b-a55b:free
```

**Error when unpinned:** `RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created (provider 'custom' -> 'openrouter'; model 'glm-5.2:cloud' -> 'nvidia/nemotron-3-ultra-550b-a55b:free')`

### Workdir Corrections
All research jobs correctly use `/Users/saiful/temuclaude/research` (NOT `timuclaude` — typo was fixed).

### Job Runtimes
- Scout script (`run_all_scouts.sh`): ~6+ minutes (15s sleep × 25 queries)
- Deep research agents: 2-5 minutes each
- Auto-integrator: 1-3 minutes (depends on findings)

### Monitoring Commands

```bash
# Check all job statuses
hermes cron list --all

# Trigger auto-integrator manually
hermes cron run 1e046581cc53

# Check latest run output
hermes cron log <job_id>

# Resume paused jobs
hermes cron resume f23172a317e5
```