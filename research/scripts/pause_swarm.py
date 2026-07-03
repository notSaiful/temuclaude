#!/usr/bin/env python3
"""
Pause all timuclaude research swarm cron jobs.
Usage: python3 scripts/pause_swarm.py
"""
import subprocess
import sys

# All timuclaude research swarm job IDs
JOB_IDS = [
    "9e7df020354c",  # Scout-arXiv
    "ff1ccb6918ed",  # Scout-GitHub
    "61e64cefc851",  # Scout-HuggingFace
    "f630666365c5",  # Distiller
    "567d1c02b6a3",  # Weekly Digest
    "9cead4c12afe",  # Daily Web Scout
    "bca9279465b2",  # Weekly Meta-Skill
    "4df1b8b9c554",  # Daily Auto-Integrator
    "59dfc008b65c",  # Daily Frontier Model Docs
    "36dc1811f66f",  # Daily Hermes Self-Improvement
]

paused = 0
for job_id in JOB_IDS:
    result = subprocess.run(
        ["hermes", "cron", "pause", job_id],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        paused += 1
        print(f"  PAUSED: {job_id}")
    else:
        # Already paused or error — check if it's already paused
        if "already" in result.stderr.lower() or "paused" in result.stdout.lower():
            print(f"  ALREADY PAUSED: {job_id}")
            paused += 1
        else:
            print(f"  SKIP: {job_id} — {result.stderr.strip()[:60]}")

print(f"\nSwarm paused: {paused}/{len(JOB_IDS)} jobs")