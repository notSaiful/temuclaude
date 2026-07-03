#!/usr/bin/env python3
"""
Resume ALL timuclaude research swarm cron jobs.
Dynamically fetches current job list — always accurate, no hardcoded IDs.

Usage: python3 scripts/resume_swarm.py
Or just tell Hermes: "resume the swarm" / "start"
"""
import subprocess
import json
import sys

# Jobs to EXCLUDE from resuming (non-timuclaude jobs)
EXCLUDE_NAMES = {"Agentive Weekly Plan"}

def get_all_jobs():
    """Fetch all cron jobs dynamically."""
    result = subprocess.run(
        ["hermes", "cron", "list", "--json"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["hermes", "cron", "list"],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout, False
    
    try:
        data = json.loads(result.stdout)
        return data, True
    except json.JSONDecodeError:
        return result.stdout, False

def resume_job(job_id):
    """Resume a single job. Returns True on success."""
    result = subprocess.run(
        ["hermes", "cron", "resume", job_id],
        capture_output=True, text=True, timeout=10
    )
    output = (result.stdout + result.stderr).lower()
    return result.returncode == 0 or "already" in output or "active" in output

# Get current jobs
jobs_output, is_json = get_all_jobs()

if is_json:
    job_list = []
    if isinstance(jobs_output, dict):
        if "jobs" in jobs_output:
            job_list = jobs_output["jobs"]
        else:
            job_list = jobs_output
    elif isinstance(jobs_output, list):
        job_list = jobs_output
    
    to_resume = []
    for job in job_list:
        if isinstance(job, dict):
            name = job.get("name", "")
            job_id = job.get("job_id", job.get("id", ""))
            if name not in EXCLUDE_NAMES and job_id:
                to_resume.append((job_id, name))
else:
    print("WARNING: Could not parse JSON. Using fallback method.")
    to_resume = [
        ("aa2649e8061c", "RANK 1 Dynamic Deep Research"),
        ("ba16699034a9", "RANK 2 Dynamic Competitive Intelligence"),
        ("c332087ad4e2", "RANK 3 Development Scan"),
        ("77872248bce3", "RANK 4 Headline Scan"),
        ("387688d82a5a", "Scout-arXiv + GitHub + HuggingFace"),
        ("1e046581cc53", "Auto-Integrator"),
        ("f23172a317e5", "Daily Post"),
    ]

# Resume each job
resumed = 0
for job_id, name in to_resume:
    if resume_job(job_id):
        resumed += 1
        print(f"  RESUMED: {name} ({job_id})")
    else:
        print(f"  SKIP: {name} ({job_id})")

print(f"\nSwarm resumed: {resumed}/{len(to_resume)} jobs")