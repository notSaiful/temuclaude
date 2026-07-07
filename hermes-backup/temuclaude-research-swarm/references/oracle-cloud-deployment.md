# Cloud Deployment — Oracle Cloud Always Free Tier

## Why Not Fly.io

Fly.io was originally planned but is expensive for always-on daemon workloads. Oracle Cloud Always Free Tier provides better specs at $0/month forever.

## Oracle Cloud Always Free Specs

- Shape: VM.Standard.A1.Flex (ARM Ampere A1)
- CPUs: 4 OCPUs (ARM)
- RAM: 24GB
- Storage: 200GB block volume
- Region: Mumbai (ap-mumbai-1) — closest to Nagpur
- Cost: $0/month forever (not a trial)

## Setup Steps

1. Sign up at https://cloud.oracle.com (credit card for verification, won't be charged)
2. Create ARM VM: VM.Standard.A1.Flex, Ubuntu 22.04, 4 CPUs, 24GB RAM, SSH key
3. SSH in: `ssh ubuntu@<vm-public-ip>`
4. Run `oracle_setup.sh` — installs Python, git, clones repo, creates systemd service
5. Set API keys in `/opt/temuclaude/.env`
6. `sudo systemctl start temuclaude-swarm`

## systemd Service

The swarm runs as a systemd service (`temuclaude-swarm.service`) with:
- `Restart=always` — auto-restarts on crash
- `RestartSec=10` — 10 second delay between restarts
- `EnvironmentFile=/opt/temuclaude/.env` — loads API keys
- Auto-starts on boot (`WantedBy=multi-user.target`)

No Docker needed — just install Python and run daemons directly. Simpler, less overhead.

## Environment Variables for Cloud

```bash
TEMUCLAUDE_DIR=/opt/temuclaude
RESEARCH_DIR=/opt/temuclaude/research
DAEMON_STATE_DIR=/tmp/temuclaude_daemons
SHARED_STATE_DIR=/opt/temuclaude/research/shared_state
MEMORY_STORE_DIR=/opt/temuclaude/research/memory_store
OPENROUTER_API_KEY=sk-or-v1-xxx
OLLAMA_API_KEY=ollama-xxx
OLLAMA_BASE_URL=https://ollama.com  # Direct to cloud, no local proxy
ZERNIO_API_KEY=xxx
GITHUB_TOKEN=ghp_xxx
VERCEL_TOKEN=xxx
```

## Path Migration

All daemon scripts must use environment variables instead of hardcoded `/Users/saiful/temuclaude`:

```python
TEMUCLAUDE_DIR = os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude")
RESEARCH_DIR = os.environ.get("RESEARCH_DIR", f"{TEMUCLAUDE_DIR}/research")
DAEMON_STATE_DIR = os.environ.get("DAEMON_STATE_DIR", "/tmp/temuclaude_daemons")
```

This allows the same code to run on Mac (local dev) and Oracle Cloud (production) without changes.

## Verification Commands

```bash
sudo systemctl status temuclaude-swarm
sudo journalctl -u temuclaude-swarm -f
bash /opt/temuclaude/research/scripts/status_swarm.sh
```

## Old Fly.io Config (deprecated)

The `fly.toml` and `Dockerfile` still exist for the LiteLLM proxy app (the API server), but the daemon swarm uses Oracle Cloud + systemd instead.