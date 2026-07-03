#!/usr/bin/env python3
"""
Check the status of all timuclaude research swarm cron jobs.
Usage: python3 scripts/swarm_status.py
Or just tell Hermes: "swarm status"
"""
import subprocess
import sys

# All current timuclaude research swarm job IDs
JOB_IDS = [
    ("aa2649e8061c", "RANK 1 Dynamic Deep Research"),
    ("ba16699034a9", "RANK 2 Dynamic Competitive Intelligence"),
    ("c332087ad4e2", "RANK 3 Development Scan"),
    ("77872248bce3", "RANK 4 Headline Scan"),
    ("387688d82a5a", "Scout-arXiv + GitHub + HuggingFace"),
    ("1e046581cc53", "Auto-Integrator"),
    ("f23172a317e5", "Daily Post"),
]

print("=" * 60)
print("TIMUCLAUDE RESEARCH SWARM — STATUS")
print("=" * 60)

active = 0
paused = 0

for job_id, name in JOB_IDS:
    result = subprocess.run(
        ["hermes", "cron", "list"],
        capture_output=True, text=True, timeout=15
    )
    # Check if this job appears as paused or active in the output
    output = result.stdout
    if job_id in output:
        # Look for paused indicator near this job
        # The list output format varies, so we check common patterns
        lines = output.split("\n")
        for line in lines:
            if job_id in line:
                if "paused" in line.lower():
                    print(f"  [PAUSED] {name}")
                    paused += 1
                    break
                elif "scheduled" in line.lower() or "active" in line.lower() or "enabled" in line.lower():
                    print(f"  [ACTIVE] {name}")
                    active += 1
                    break
        else:
            print(f"  [UNKNOWN] {name}")
    else:
        print(f"  [MISSING] {name}")

print(f"\nActive: {active} | Paused: {paused} | Total: {len(JOB_IDS)}")
if active > 0 and paused == 0:
    print("STATUS: SWARM IS RUNNING")
elif paused > 0 and active == 0:
    print("STATUS: SWARM IS STOPPED")
elif active > 0 and paused > 0:
    print("STATUS: SWARM IS PARTIALLY RUNNING (some jobs active, some paused)")
else:
    print("STATUS: UNKNOWN")
print("=" * 60)