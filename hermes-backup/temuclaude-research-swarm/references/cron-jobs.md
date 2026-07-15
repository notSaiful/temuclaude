# Temuclaude Research Swarm — Cron Job Reference

## Overview
The Temuclaude project (`/Users/saiful/temuclaude`) includes a 24/7 autonomous deep research swarm implemented as Hermes cron jobs. This reference documents the cron job configuration, common issues, and how to activate/debug the swarm.

## Cron Jobs (7 jobs total)

| Job ID | Name | Schedule | Type | Workdir |
|--------|------|----------|------|---------|
| `387688d82a5a` | Scout-arXiv + GitHub + HuggingFace | `0 4,16 * * *` (2× daily) | Script (`no_agent=true`) | `/Users/saiful/temuclaude/research` |
| `aa2649e8061c` | RANK 1 — Dynamic Deep Research | `0 2,10,18 * * *` (3× daily) | Agent | `/Users/saiful/temuclaude/research` |
| `ba16699034a9` | RANK 2 — Competitive Intelligence | `0 6,14 * * *` (2× daily) | Agent | `/Users/saiful/temuclaude/research` |
| `c332087ad4e2` | RANK 3 — Development Scan | `0 12 * * *` (daily) | Agent | `/Users/saiful/temuclaude/research` |
| `77872248bce3` | RANK 4 — Headline Scan | `0 0 * * 0` (weekly Sun) | Agent | `/Users/saiful/temuclaude/research` |
| `1e046581cc581cc53` | Auto-Integrator | `0 1 * * *` (daily 1am) | Agent | `/Users/saiful/temuclaude` |
| `4bfd63cf51d6` | Agentive Weekly Plan | `0 20 * * 0` (Sun 8pm) | Script | (root) |

## Pipeline Architecture

```
Scouts (arXiv/GitHub/HF) → raw/*.json
       ↓
Distiller (runs after scouts) → findings/*.md (evaluated, scored)
       ↓
RANK 1-4 Agents → Deep research on prioritized topics
       ↓
Auto-Integrator (1am daily) → Implements findings into codebase
       ↓
Weekly Digest → Delivered to user
```

## Scout Scripts

Located in `/Users/saiful/temuclaude/research/scripts/`:
- `scout_arxiv.py` — Searches arXiv with 25 diverse queries
- `scout_github.py` — Searches GitHub for repos
- `scout_huggingface.py` — Searches HF for models/datasets
- `run_all_scouts.sh` — Orchestrates all 3 scouts + distiller
- `distiller.py` — Evaluates, deduplicates, scores findings
- `auto_integrator.py` — Implements high-priority findings

## Common Issues & Fixes

### Wrong Workdir (Most Common)
Cron jobs were created with `/Users/saiful/timuclaude` (typo: `timuclaude` vs `temuclaude`). The directory doesn't exist.

**Fix:**
```bash
# Update all affected jobs to correct workdir
hermes cron edit <job_id> --workdir /Users/saiful/temuclaude/research
# or for root-level jobs:
hermes cron edit <job_id> --workdir /Users/saiful/temuclaude
```

### Jobs Stuck in Paused State
All 6 research swarm jobs were paused. Resume with:
```bash
hermes cron resume <job_id>
# Or via cronjob tool:
cronjob(action='resume', job_id='<job_id>')
```

### Scout Timeout
The `scout_arxiv.py` script sleeps 15s between 25 queries → ~6+ minutes. Default cron timeout (3 min) kills it.

**Fix:** The cron job uses `no_agent=true` with a shell script, which has no timeout limit. The script runs to completion.

### First Run Verification
```bash
cd /Users/saiful/temuclaude/research
python3 scripts/run_all_scouts.sh
# Check output in research/raw/ for new JSON files
```

## Activation Checklist

- [ ] All 6 research swarm jobs have correct workdir (`/Users/saiful/temuclaude/research` or `/Users/saiful/temuclaude`)
- [ ] All 6 jobs are `enabled: true` and `state: scheduled`
- [ ] Scout script runs manually without errors
- [ ] `research/raw/` receives new timestamped JSON files after scout run
- [ ] `research/findings/` gets distilled markdown after distiller run
- [ ] Auto-integrator creates PRs/commits in temuclaude repo

## Commands

```bash
# List all cron jobs
hermes cron list --all

# Resume a paused job
hermes cron resume <job_id>

# Trigger a job immediately
hermes cron run <job_id>

# Check job status
hermes cron status

# View job details
hermes cron edit <job_id>  # shows current config
```

## Research Targets (What the Swarm Hunts)

- **Orchestration**: Fusion patterns, aggregator selection, dynamic routing, cost-quality tradeoffs
- **Reasoning**: MCTS/tree search, PRMs, CoT variants, self-consistency, test-time compute
- **Model Combination**: MoE at inference, model merging, speculative decoding, ensembles
- **Prompt Engineering**: OPRO, GEPA, automated prompting, meta-prompting
- **Competitive Intel**: Frontier model capabilities, benchmark landscapes, new model releases
- **Cost Optimization**: Routing, caching, speculative execution, early exit, quantization

## Files to Monitor

- `research/raw/arxiv_*.json` — New paper discoveries
- `research/raw/github_*.json` — New repo discoveries
- `research/raw/huggingface_*.json` — New model/dataset discoveries
- `research/findings/*.md` — Distilled, evaluated findings
- `research/weekly/*.md` — Weekly digests
- `ROADMAP.md` — Current product priorities and release gate
- `research/TRACKER.md` — Integration tracking
