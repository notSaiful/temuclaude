#!/usr/bin/env python3
"""
Industry Radar Daemon — continuous market intelligence.
Runs every 2 hours, monitors industry sources, converts to research tasks.
"""

import json, time, os, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from radar_sources import scan_all_sources
from radar_scorer import score_and_filter

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
RADAR_DIR = TEMUCLAUDE / "research" / "radar_reports"
RADAR_DIR.mkdir(exist_ok=True)
BOOST_FILE = TEMUCLAUDE / "research" / "industry_boosts.json"


class IndustryRadarDaemon(DaemonBase):
    def __init__(self):
        super().__init__("industry_radar_daemon")

    def run_once(self) -> bool:
        self.logger.info("=== Industry Radar scan started ===")
        signals = scan_all_sources()
        self.logger.info(f"Raw signals: {len(signals)}")
        scored = score_and_filter(signals)
        self.logger.info(f"Novel signals: {len(scored)}")
        tasks = self._signals_to_tasks(scored)
        self.logger.info(f"Created {tasks} research tasks")
        self._generate_boosts(scored)
        self._save_report(scored)
        return True

    def _signals_to_tasks(self, scored):
        tasks = 0
        try:
            sys.path.insert(0, str(TEMUCLAUDE / "research"))
            from queue import QueueManager
            qm = QueueManager()
            for s in scored:
                if s.get("score", 0) < 50:
                    break
                if s.get("action") != "research_task":
                    continue
                task_data = {
                    "id": f"radar_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{s.get('source', '')}",
                    "source": "industry_radar",
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "score": s.get("score", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                # Write to file so research_daemon can open it
                findings_dir = TEMUCLAUDE / "research" / "findings"
                findings_dir.mkdir(exist_ok=True)
                finding_file = findings_dir / f"radar_{task_data['id'].split('_')[1]}_{s.get('source', 'unknown')[:20]}.json"
                with open(finding_file, 'w') as f:
                    json.dump(task_data, f, indent=2)
                qm.push("new_findings", [str(finding_file)])
                tasks += 1
        except Exception as e:
            self.logger.exception(f"Task creation failed: {e}")
        return tasks

    def _generate_boosts(self, scored):
        boosts = []
        topic_map = {
            "speculative_decoding": "speculative_decoding",
            "vllm": "vllm_serving", "litellm": "litellm_config",
            "openrouter": "model_pool", "jailbreak": "jailbreak_defense",
            "guardrail": "output_guardrail", "reasoning": "reasoning_enhancement",
            "benchmark": "benchmark_improvement",
        }
        seen_topics = {}
        for s in scored:
            if s.get("score", 0) < 30:
                break
            for kw in s.get("matched_keywords", []):
                topic = topic_map.get(kw)
                if topic:
                    boost = min(s["score"] // 2, 40)
                    if topic not in seen_topics or boost > seen_topics[topic]["boost"]:
                        seen_topics[topic] = {"topic": topic, "boost": boost,
                            "reason": f"Industry signal: {s.get('title', '')[:100]}",
                            "source": s.get("source", "")}
        with open(BOOST_FILE, 'w') as f:
            json.dump(list(seen_topics.values()), f, indent=2)

    def _save_report(self, scored):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_signals": len(scored),
            "top_signals": [{"title": s.get("title", ""), "source": s.get("source", ""),
                             "score": s.get("score", 0), "url": s.get("url", "")}
                            for s in scored[:20]],
        }
        with open(RADAR_DIR / f"radar_{ts}.json", 'w') as f:
            json.dump(report, f, indent=2)
        with open(RADAR_DIR / "CURRENT_RADAR.md", 'w') as f:
            f.write(f"# Temuclaude Industry Radar\n> Updated: {report['timestamp']}\n> Signals: {report['total_signals']}\n\n")
            for i, s in enumerate(report["top_signals"], 1):
                f.write(f"{i}. [{s['score']}] ({s['source']}) {s['title'][:100]}\n")
        old = sorted(RADAR_DIR.glob("radar_*.json"), reverse=True)[84:]
        for o in old:
            o.unlink()

def main():
    daemon = IndustryRadarDaemon()
    daemon.run(interval=7200)  # 2 hours

if __name__ == "__main__":
    main()
