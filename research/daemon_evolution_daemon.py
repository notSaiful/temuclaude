#!/usr/bin/env python3
"""
Daemon Evolution Engine — Hasan improves its own workforce.

This daemon evaluates every daemon's ROI (value produced vs tokens spent),
improves underperformers by rewriting their logic, adds new daemons when
gaps are identified, and removes redundant ones.

It runs every 6 hours and logs all decisions to evolution_log.json.
Ggs approves structural changes (add/remove) via the Deploy tab.
Improvements to existing daemon logic are auto-applied in staging.
"""

import json
import time
import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from shared_memory import read_all_states, get_recent_events, log_event
from unlimited_memory import remember

try:
    from ollama_client import call_model, is_available as ollama_available
except ImportError:
    call_model = None
    ollama_available = lambda: False

RESEARCH_DIR = Path(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
EVOLUTION_LOG = RESEARCH_DIR / "evolution_log.json"
DAEMON_REGISTRY = RESEARCH_DIR / "daemon_registry.json"
STAGING_DIR = RESEARCH_DIR / "staging"

# Daemons that should never be removed — core infrastructure
PROTECTED_DAEMONS = {
    "coordinator_daemon",  # Brain — can't remove the brain
    "scout_daemon",        # Research pipeline entry point
    "distiller_daemon",    # Research pipeline filter
    "integrator_daemon",   # Code integration
    "watchdog",            # Health monitoring
    "sync_daemon",         # Vercel sync
}

# Minimum ROI thresholds
MIN_EVENTS_PER_DAY = 2       # Daemon must produce at least 2 events/day
MIN_UPTIME_PERCENT = 60      # Daemon must be alive >= 60% of the time
MAX_STALE_DAYS = 3           # If no events for 3 days, candidate for removal
MIN_IMPROVEMENT_GAP = 3      # Re-evaluate only after 3 cycles since last improvement


def _load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.rename(path)


class DaemonEvolutionDaemon(DaemonBase):
    """Hasan's self-improvement engine for its own workforce."""

    def __init__(self):
        super().__init__("daemon_evolution_daemon")
        self.registry = _load_json(DAEMON_REGISTRY, {"daemons": {}, "evaluations": [], "changes": []})

    def run_once(self) -> bool:
        """Main evolution cycle: evaluate → improve → add → remove."""
        self.logger.info("Starting evolution cycle...")

        # 1. Evaluate all daemons
        scores = self._evaluate_all_daemons()

        # 2. Improve underperformers
        improvements = self._improve_daemons(scores)

        # 3. Identify gaps → propose new daemons
        additions = self._identify_gaps(scores)

        # 4. Identify redundant/dead daemons → propose removal
        removals = self._identify_redundant(scores)

        # 5. Log everything
        cycle_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle": len(self.registry.get("evaluations", [])) + 1,
            "evaluations": scores,
            "improvements": improvements,
            "proposed_additions": additions,
            "proposed_removals": removals,
        }

        self.registry.setdefault("evaluations", []).append(cycle_result)
        self.registry.setdefault("changes", []).extend(improvements)
        _save_json(DAEMON_REGISTRY, self.registry)

        # Log to evolution_log.json (simpler history)
        log = _load_json(EVOLUTION_LOG, [])
        log.append({
            "timestamp": cycle_result["timestamp"],
            "cycle": cycle_result["cycle"],
            "daemons_evaluated": len(scores),
            "improvements_made": len(improvements),
            "additions_proposed": len(additions),
            "removals_proposed": len(removals),
            "summary": self._generate_summary(scores, improvements, additions, removals),
        })
        # Keep last 100 entries
        if len(log) > 100:
            log = log[-100:]
        _save_json(EVOLUTION_LOG, log)

        # Log events for the UI
        for imp in improvements:
            log_event("daemon_improved", "daemon_evolution_daemon",
                      f"Improved {imp['daemon']}: {imp['change']}", imp)
        for add in additions:
            log_event("daemon_proposed", "daemon_evolution_daemon",
                      f"Proposed new daemon: {add['name']} — {add['purpose']}", add)
        for rem in removals:
            log_event("daemon_removal_proposed", "daemon_evolution_daemon",
                      f"Proposed removal: {rem['daemon']} — {rem['reason']}", rem)

        remember("evolution", "daemon_evolution_daemon",
                 f"Evolution cycle {cycle_result['cycle']}: {len(scores)} evaluated, "
                 f"{len(improvements)} improved, {len(additions)} additions, {len(removals)} removals",
                 {"cycle": cycle_result["cycle"]})

        self.logger.info(f"Evolution cycle complete: {len(scores)} evaluated, "
                         f"{len(improvements)} improved, {len(additions)} additions, "
                         f"{len(removals)} removals proposed")
        return True

    def _evaluate_all_daemons(self) -> list:
        """Score every daemon on ROI: events produced, uptime, uniqueness."""
        all_states = read_all_states()
        states = all_states.get("daemons", all_states)  # Extract daemon sub-dict
        all_events = get_recent_events(limit=500)
        now = datetime.now(timezone.utc)

        # Count events per daemon in last 24h and 7d
        events_24h = defaultdict(int)
        events_7d = defaultdict(int)
        for ev in all_events:
            daemon = ev.get("daemon", "")
            try:
                ev_time = datetime.fromisoformat(ev.get("timestamp", "").replace("Z", "+00:00"))
                age = now - ev_time
                if age < timedelta(hours=24):
                    events_24h[daemon] += 1
                if age < timedelta(days=7):
                    events_7d[daemon] += 1
            except Exception:
                continue

        scores = []
        for name, state in states.items():
            if name == "daemon_evolution_daemon":
                continue

            ev_24 = events_24h.get(name, 0)
            ev_7d = events_7d.get(name, 0)

            # Uptime: check heartbeat freshness
            uptime_pct = 0
            try:
                hb_time = datetime.fromisoformat(state.get("timestamp", "").replace("Z", "+00:00"))
                age_sec = (now - hb_time).total_seconds()
                # If heartbeat is fresh, daemon is alive
                if age_sec < 120:
                    uptime_pct = 100
                elif age_sec < 3600:
                    uptime_pct = 80
                elif age_sec < 7200:
                    uptime_pct = 50
                elif age_sec < 21600:
                    uptime_pct = 20
                else:
                    uptime_pct = 0
            except Exception:
                pass

            # ROI score: events per cycle, weighted by uptime
            roi = ev_7d * (uptime_pct / 100)

            # Check if protected
            is_protected = name in PROTECTED_DAEMONS

            # Check last improvement cycle
            last_improved = None
            for change in self.registry.get("changes", []):
                if change.get("daemon") == name and change.get("type") == "improve":
                    last_improved = change.get("cycle", 0)

            current_cycle = len(self.registry.get("evaluations", [])) + 1
            cycles_since_improvement = current_cycle - (last_improved or 0)

            # Verdict
            if is_protected:
                verdict = "protected"
            elif ev_7d == 0 and uptime_pct == 0:
                verdict = "remove_candidate"
            elif ev_24 < MIN_EVENTS_PER_DAY and uptime_pct < MIN_UPTIME_PERCENT:
                verdict = "improve_candidate"
            elif ev_24 >= 10 and uptime_pct >= 80:
                verdict = "healthy"
            else:
                verdict = "marginal"

            scores.append({
                "daemon": name,
                "events_24h": ev_24,
                "events_7d": ev_7d,
                "uptime_pct": uptime_pct,
                "roi_score": round(roi, 1),
                "verdict": verdict,
                "protected": is_protected,
                "cycles_since_improvement": cycles_since_improvement,
            })

        return scores

    def _improve_daemons(self, scores: list) -> list:
        """Rewrite logic for underperforming daemons using LLM."""
        improvements = []
        current_cycle = len(self.registry.get("evaluations", [])) + 1

        for score in scores:
            if score["verdict"] != "improve_candidate":
                continue
            if score["cycles_since_improvement"] < MIN_IMPROVEMENT_GAP:
                continue

            daemon_name = score["daemon"]
            daemon_file = RESEARCH_DIR / f"{daemon_name}.py"

            if not daemon_file.exists():
                # Check scripts subdir
                daemon_file = RESEARCH_DIR / "scripts" / f"{daemon_name}.py"
                if not daemon_file.exists():
                    continue

            # Read current code
            try:
                current_code = daemon_file.read_text()
            except Exception:
                continue

            # Generate improvement using LLM
            improvement = self._llm_improve(daemon_name, current_code, score)
            if improvement and improvement.get("improved_code"):
                # Write to staging, not main — safety first
                staging_file = STAGING_DIR / daemon_file.name
                staging_file.parent.mkdir(parents=True, exist_ok=True)
                staging_file.write_text(improvement["improved_code"])

                improvements.append({
                    "type": "improve",
                    "daemon": daemon_name,
                    "file": str(staging_file),
                    "original_file": str(daemon_file),
                    "change": improvement.get("description", "LLM-generated improvement"),
                    "cycle": current_cycle,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "staged",  # Ggs approves via Deploy tab
                })

                self.logger.info(f"Staged improvement for {daemon_name}: {improvement.get('description', '')}")
            else:
                # If no LLM available, log a diagnostic improvement
                improvements.append({
                    "type": "improve",
                    "daemon": daemon_name,
                    "change": f"Identified low ROI (events_24h={score['events_24h']}, uptime={score['uptime_pct']}%). "
                              f"Manual review needed — LLM unavailable.",
                    "cycle": current_cycle,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "needs_manual_review",
                })

        # Update registry
        self.registry.setdefault("changes", []).extend(improvements)
        return improvements

    def _llm_improve(self, daemon_name: str, current_code: str, score: dict) -> dict:
        """Use LLM to generate improved daemon code."""
        if not call_model or not ollama_available():
            return {"improved_code": None, "description": "LLM unavailable"}

        prompt = f"""You are improving a Python daemon in an autonomous research swarm.
The daemon "{daemon_name}" is underperforming:
- Events in last 24h: {score['events_24h']}
- Events in last 7d: {score['events_7d']}
- Uptime: {score['uptime_pct']}%

Current code:
```python
{current_code[:3000]}
```

Problems to fix:
1. If it's not producing events, the run_once() logic may be broken or too conservative
2. If uptime is low, it may be crashing — add better error handling
3. If it's slow, reduce the work in each cycle

Rewrite the daemon to be more effective. Keep the same class name and interface.
Only output the improved Python code, no explanation."""

        try:
            result = call_model("glm-5.2", prompt, max_tokens=2000)
            improved = result.get("response", "").strip()
            if improved and len(improved) > 100 and "class " in improved:
                # Extract code from markdown if present
                if "```python" in improved:
                    improved = improved.split("```python")[1].split("```")[0]
                elif "```" in improved:
                    improved = improved.split("```")[1].split("```")[0]
                return {
                    "improved_code": improved.strip(),
                    "description": f"LLM rewrite: improved error handling and event production for low ROI (uptime {score['uptime_pct']}%)",
                }
        except Exception as e:
            self.logger.warning(f"LLM improvement failed for {daemon_name}: {e}")

        return {"improved_code": None, "description": "LLM call failed"}

    def _identify_gaps(self, scores: list) -> list:
        """Find capability gaps from SWOT weaknesses and propose new daemons."""
        additions = []

        # Get SWOT weaknesses from events
        swot_events = get_recent_events(limit=50, event_type="swot")
        existing_names = {s["daemon"] for s in scores}

        for ev in swot_events:
            weaknesses = ev.get("extra", {}).get("weaknesses", [])
            for w in weaknesses:
                area = w.get("area", "").lower().replace(" ", "_")
                if not area:
                    continue
                daemon_name = f"{area}_daemon"

                # Check if we already have something similar
                if daemon_name in existing_names or any(area in d for d in existing_names):
                    continue

                # Check if already proposed recently
                already_proposed = any(
                    a.get("name") == daemon_name
                    for a in self.registry.get("changes", [])
                    if a.get("type") == "add" and
                    (datetime.now(timezone.utc) - datetime.fromisoformat(a.get("timestamp", "2000-01-01T00:00:00+00:00"))).days < 7
                )
                if already_proposed:
                    continue

                additions.append({
                    "type": "add",
                    "name": daemon_name,
                    "purpose": w.get("action", f"Address weakness in {area}"),
                    "area": area,
                    "reason": f"SWOT identified weakness: {w.get('area', area)}",
                    "status": "proposed",  # Ggs approves via Deploy tab
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        # Also check for research breakthroughs that need implementation daemons
        impl_events = get_recent_events(limit=50, event_type="implementation_complete")
        tech_areas = set()
        for ev in impl_events:
            extra = ev.get("extra", {})
            tech = extra.get("technology", extra.get("category", ""))
            if tech:
                tech_areas.add(tech.lower().replace(" ", "_"))

        # If we have >3 completed implementations in a tech area without a dedicated daemon, propose one
        tech_counts = defaultdict(int)
        for ev in impl_events:
            extra = ev.get("extra", {})
            tech = extra.get("technology", extra.get("category", "general"))
            tech_counts[tech] += 1

        for tech, count in tech_counts.items():
            if count > 3:
                area = tech.lower().replace(" ", "_")
                daemon_name = f"{area}_specialist_daemon"
                if daemon_name not in existing_names:
                    additions.append({
                        "type": "add",
                        "name": daemon_name,
                        "purpose": f"Specialized daemon for {tech} — {count} implementations completed, needs dedicated focus",
                        "area": area,
                        "reason": f"High activity area: {count} implementations in {tech}",
                        "status": "proposed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

        self.registry.setdefault("changes", []).extend(additions)
        return additions

    def _identify_redundant(self, scores: list) -> list:
        """Find daemons that are dead, redundant, or zero-ROI → propose removal."""
        removals = []
        current_cycle = len(self.registry.get("evaluations", [])) + 1

        # Group daemons by function area (from registry metadata)
        for score in scores:
            if score["protected"]:
                continue

            daemon_name = score["daemon"]

            # Dead daemon: no events in 7 days, no uptime
            if score["events_7d"] == 0 and score["uptime_pct"] == 0:
                # Check if it's been dead for multiple cycles
                dead_cycles = 0
                for ev in reversed(self.registry.get("evaluations", [])):
                    for s in ev.get("evaluations", []):
                        if s.get("daemon") == daemon_name:
                            if s.get("events_7d", 0) == 0 and s.get("uptime_pct", 0) == 0:
                                dead_cycles += 1
                            else:
                                break
                            break

                if dead_cycles >= 2:  # Dead for 2+ consecutive cycles
                    removals.append({
                        "type": "remove",
                        "daemon": daemon_name,
                        "reason": f"Dead for {dead_cycles} cycles: 0 events, 0% uptime. No value produced.",
                        "status": "proposed",  # Ggs approves via Deploy tab
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    continue

            # Redundant daemon: same function area as another, lower ROI
            # Check if two daemons share the same area prefix
            name_area = daemon_name.replace("_daemon", "").rsplit("_", 1)[0]
            for other in scores:
                if other["daemon"] == daemon_name or other["protected"]:
                    continue
                other_area = other["daemon"].replace("_daemon", "").rsplit("_", 1)[0]
                if name_area == other_area and score["roi_score"] < other["roi_score"] * 0.3:
                    # This daemon produces <30% of the other's ROI in same area
                    removals.append({
                        "type": "remove",
                        "daemon": daemon_name,
                        "reason": f"Redundant with {other['daemon']}: ROI {score['roi_score']} vs {other['roi_score']} "
                                  f"(same area: {name_area}). Merge or remove.",
                        "status": "proposed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    break

        self.registry.setdefault("changes", []).extend(removals)
        return removals

    def _generate_summary(self, scores, improvements, additions, removals) -> str:
        """Human-readable summary for the log."""
        healthy = sum(1 for s in scores if s["verdict"] == "healthy")
        marginal = sum(1 for s in scores if s["verdict"] == "marginal")
        improve = sum(1 for s in scores if s["verdict"] == "improve_candidate")
        remove = sum(1 for s in scores if s["verdict"] == "remove_candidate")

        parts = [
            f"{healthy} healthy, {marginal} marginal, {improve} need improvement, {remove} removal candidates",
            f"{len(improvements)} improvements staged",
            f"{len(additions)} new daemons proposed",
            f"{len(removals)} removals proposed",
        ]
        return " · ".join(parts)


def main():
    daemon = DaemonEvolutionDaemon()
    daemon.run(interval=21600)  # 6 hours


if __name__ == "__main__":
    main()