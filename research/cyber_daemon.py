#!/usr/bin/env python3
"""
Cyber Research Daemon - Continuous cybersecurity research and defense testing.

This daemon is dedicated to cybersecurity research. It:
1. Pulls cybersecurity findings from the queue (populated by scouts + distiller)
2. Runs deep research on top cyber priorities (Cognitive Firewall, self-healing guard, etc.)
3. Generates implementation-ready security reports
4. Queues them for the auto-integrator
5. Runs a mini Red-Blue loop: tests existing defenses, logs vulnerabilities

This runs alongside the 3 existing research_daemon instances, but focuses
exclusively on cybersecurity topics identified by the dynamic priority engine.
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add research dir to path
sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase
from queue import pop_findings, push_implementation
from dynamic_priorities import calculate_dynamic_priorities

RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")
FINDINGS_DIR = RESEARCH_DIR / "findings"
RAW_DIR = RESEARCH_DIR / "raw"

# Cybersecurity topics that this daemon focuses on
CYBER_TOPICS = {
    "cognitive_firewall", "self_healing_guard", "haloguard_classifier",
    "knnguard_guardrail", "owasp_llm_top10", "owasp_agentic_top10",
    "ai_infra_guard", "red_blue_loop", "antaeus_scanner",
    "function_call_defense", "lifecycle_defenses", "supply_chain_defense",
    "backdoor_detection", "adversarial_verifier_security",
    "harc_alignment", "autonomous_red_blue_ecosystem", "offensive_swarm",
    "neurosymbolic_scanner", "context_lake",
}

# Keywords to identify cybersecurity findings from the queue
CYBER_KEYWORDS = [
    "jailbreak", "injection", "adversarial", "security", "attack", "defense",
    "red team", "vulnerab", "exploit", "malicious", "poisoning", "backdoor",
    "robustness", "safety", "guardrail", "firewall", "owasp", "mitre",
    "cyber", "pentest", "cve", "zero-day", "supply chain",
]


class CyberResearchDaemon(DaemonBase):
    """Continuous cybersecurity research daemon."""

    def __init__(self):
        super().__init__("cyber_daemon")
        self.cycle = 0
        self.researched_topics = set()

    def run_once(self) -> bool:
        """Run one cyber research cycle."""
        self.cycle += 1
        self.logger.info(f"=== Cyber research cycle {self.cycle} started ===")

        # 1. Check for cyber findings in the queue
        findings = pop_findings(3)
        cyber_findings = []
        for f in findings:
            if self._is_cyber_finding(f):
                cyber_findings.append(f)

        if cyber_findings:
            self.logger.info(f"Found {len(cyber_findings)} cyber findings in queue")
            for f in cyber_findings:
                self._research_finding(f)
        else:
            # 2. No cyber findings — research top cyber priority
            self._research_top_cyber_priority()

        # 3. Log cycle completion
        self.logger.info(f"=== Cyber research cycle {self.cycle} complete ===")
        return True

    def _is_cyber_finding(self, finding_file: str) -> bool:
        """Check if a finding file is cybersecurity-related."""
        try:
            with open(finding_file) as f:
                data = json.load(f)

            # Check title, abstract, description, keywords
            text = json.dumps(data).lower()
            return any(kw in text for kw in CYBER_KEYWORDS)
        except Exception:
            return False

    def _research_top_cyber_priority(self):
        """Research the highest-priority cybersecurity topic."""
        priorities = calculate_dynamic_priorities()

        # Find the top cyber topic
        top_cyber = None
        for name, info in priorities.items():
            if name in CYBER_TOPICS and info.get("action") != "stop_researching":
                top_cyber = (name, info)
                break

        if not top_cyber:
            self.logger.info("No cyber topics to research")
            return

        topic, info = top_cyber
        score = info.get("priority_score", 0)
        self.logger.info(f"Top cyber priority: {topic} (score: {score})")

        if topic in self.researched_topics:
            self.logger.info(f"Already researched {topic} this session, skipping")
            return

        self._research_topic(topic, info)
        self.researched_topics.add(topic)

    def _research_topic(self, topic: str, info: dict):
        """Create a deep research prompt for a cybersecurity topic."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        prompt_file = RAW_DIR / f"research_prompt_cyber_{topic}_{timestamp}.txt"

        prompt = f"""You are the CYBERSECURITY RESEARCH AGENT for Temuclaude.
Research this topic deeply: {topic}

Priority Score: {info.get('priority_score', 'N/A')}
Reason: {info.get('reason', 'N/A')}
Action Needed: {info.get('action', 'N/A')}

Focus on:
1. Latest papers (arXiv cs.CR), repos (GitHub), models (HuggingFace)
2. Concrete defense techniques we can implement in src/security/
3. Code examples, APIs, integration details
4. Benchmarks, results, tradeoffs (attack success rate, false positive rate)
5. How to integrate with Temuclaude's existing orchestrator + daemon swarm

Output a deep research report as markdown to:
{FINDINGS_DIR}/deep_research_cyber_{topic}_{timestamp}.md

Include:
- Executive summary
- Key techniques with implementation details
- Code snippets / pseudo-code
- Integration points for Temuclaude (which src/ files to modify)
- Risk assessment
- Priority: implement now / track for future / blocked
- OWASP/MITRE/CSA framework mapping
"""

        with open(prompt_file, "w") as f:
            f.write(prompt)

        self.logger.info(f"Created cyber research prompt: {prompt_file.name}")

        # Also create a placeholder findings report so the integrator can pick it up
        report_file = FINDINGS_DIR / f"deep_research_cyber_{topic}_{timestamp}.md"
        report = f"""# Deep Research: {topic} (Cybersecurity)

## Status: QUEUED_FOR_LLM_RESEARCH
## Topic: {topic}
## Priority Score: {info.get('priority_score', 'N/A')}
## Reason: {info.get('reason', 'N/A')}
## Timestamp: {datetime.now(timezone.utc).isoformat()}

## Research Prompt
See: {prompt_file.name}

## Next Steps
1. LLM agent reads the research prompt
2. Conducts deep search on arXiv (cs.CR), GitHub, HuggingFace, OWASP
3. Produces implementation-ready security report
4. Queues for auto-integrator to implement in src/security/
"""
        with open(report_file, "w") as f:
            f.write(report)

        push_implementation([str(report_file)])
        self.logger.info(f"Cyber research report queued: {report_file.name}")

    def _research_finding(self, finding_file: str):
        """Deep research on a specific cybersecurity finding."""
        try:
            with open(finding_file) as f:
                finding = json.load(f)

            title = finding.get("title", finding.get("name", "unknown"))
            self.logger.info(f"Deep cyber research on: {title}")

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            output_file = FINDINGS_DIR / f"deep_research_cyber_{title.replace(' ', '_')[:50]}_{timestamp}.md"

            report = f"""# Deep Research: {title} (Cybersecurity Finding)

## Source Finding
- File: {finding_file}
- Type: {finding.get('type', 'unknown')}
- Relevance Score: {finding.get('relevance_score', 'N/A')}
- Keywords: {finding.get('matched_keywords', [])}

## Research Status
- Status: QUEUED_FOR_LLM_RESEARCH
- Priority: HIGH (CYBERSECURITY)
- Timestamp: {datetime.now(timezone.utc).isoformat()}

## Next Steps
1. LLM agent reads this finding
2. Conducts deep research on the specific paper/repo/model
3. Assesses applicability to Temuclaude's security stack
4. Produces implementation-ready report
5. Queues for auto-integrator to implement in src/security/
"""
            with open(output_file, "w") as f:
                f.write(report)

            push_implementation([str(output_file)])
            self.logger.info(f"Cyber finding research report created: {output_file.name}")

        except Exception as e:
            self.logger.exception(f"Failed to process cyber finding {finding_file}: {e}")


def main():
    daemon = CyberResearchDaemon()
    # Run every 5 minutes (same as research daemons)
    daemon.run(interval=300)


if __name__ == "__main__":
    main()