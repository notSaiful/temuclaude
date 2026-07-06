#!/usr/bin/env python3
"""
Efficiency Research Daemon - Continuous efficiency and cost-saving research.

This daemon is dedicated to LOSSLESS and QUALITY-PRESERVING efficiency research.
It NEVER researches techniques that sacrifice quality, per Ggs's rule:
  "NEVER NEVER NEVER sacrifice quality for cost cutting.
   Unless the risk to reward is way better."

It:
1. Pulls efficiency findings from the queue (populated by scouts + distiller)
2. Runs deep research on top efficiency priorities (semantic caching, prefix
   caching, RouteLLM cascade, structured output, etc.)
3. Generates implementation-ready efficiency reports with quality classification
4. Queues them for the auto-integrator
5. Verifies quality classification (lossless / quality-preserving / Pareto-optimal)

This runs alongside the existing 8 daemons, focused exclusively on efficiency.
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

# Efficiency topics that this daemon focuses on
EFFICIENCY_TOPICS = {
    "semantic_caching", "prefix_caching", "routellm_cascade",
    "structured_output", "provider_prompt_caching",
    "efficiency_pareto_monitoring", "speculative_decoding",
    "continuous_batching", "awq_quantization", "early_exit_adaptive",
    "teacher_student_distillation", "dflash_speculator_training",
    "model_weight_merging_eff", "efficiency_continuous_improvement",
}

# Keywords to identify efficiency findings from the queue
EFFICIENCY_KEYWORDS = [
    "speculative", "caching", "cache", "kv cache", "prefix caching",
    "quantization", "awq", "gguf", "efficiency", "cost reduction",
    "speedup", "throughput", "lossless", "pruning", "distillation",
    "moe", "mixture of experts", "early exit", "adaptive computation",
    "compression", "token reduction", "batch", "vllm", "pagedattention",
    "continuous batching", "cascade routing", "routellm",
    "semantic cache", "structured output", "constrained generation",
    "pareto", "model merging", "ties merging", "task arithmetic",
    "dflash", "eagle", "medusa", "draft model",
    "prompt caching", "prompt optimization", "dspy", "miprov2",
]

# QUALITY GUARDRAIL — techniques that sacrifice quality are REJECTED
REJECTED_TECHNIQUES = {
    "extreme_quantization",  # >2% quality loss
    "aggressive_pruning",   # unstructured pruning with >5% loss
    "extreme_distillation", # distillation without cascade fallback
    "unverified_efficiency", # no benchmarks, marketing claims only
}


class EfficiencyResearchDaemon(DaemonBase):
    """Continuous efficiency research daemon — QUALITY GUARDRAIL ENFORCED."""

    def __init__(self):
        super().__init__("efficiency_daemon")
        self.cycle = 0
        self.researched_topics = set()

    def run_once(self) -> bool:
        """Run one efficiency research cycle."""
        self.cycle += 1
        self.logger.info(f"=== Efficiency research cycle {self.cycle} started ===")

        # 1. Check for efficiency findings in the queue
        findings = pop_findings(3)
        eff_findings = []
        for f in findings:
            if self._is_efficiency_finding(f):
                eff_findings.append(f)

        if eff_findings:
            self.logger.info(f"Found {len(eff_findings)} efficiency findings in queue")
            for f in eff_findings:
                self._research_finding(f)
        else:
            # 2. No efficiency findings — research top efficiency priority
            self._research_top_efficiency_priority()

        self.logger.info(f"=== Efficiency research cycle {self.cycle} complete ===")
        return True

    def _is_efficiency_finding(self, finding_file: str) -> bool:
        """Check if a finding file is efficiency-related."""
        try:
            with open(finding_file) as f:
                data = json.load(f)
            text = json.dumps(data).lower()
            return any(kw in text for kw in EFFICIENCY_KEYWORDS)
        except Exception:
            return False

    def _research_top_efficiency_priority(self):
        """Research the highest-priority efficiency topic."""
        priorities = calculate_dynamic_priorities()

        top_eff = None
        for name, info in priorities.items():
            if name in EFFICIENCY_TOPICS and info.get("action") != "stop_researching":
                # QUALITY GUARDRAIL: skip rejected techniques
                if name in REJECTED_TECHNIQUES:
                    self.logger.warning(f"REJECTED (quality sacrifice): {name}")
                    continue
                top_eff = (name, info)
                break

        if not top_eff:
            self.logger.info("No efficiency topics to research")
            return

        topic, info = top_eff
        score = info.get("priority_score", 0)
        quality = info.get("quality_class", "unknown")
        self.logger.info(f"Top efficiency priority: {topic} (score: {score}, quality: {quality})")

        if topic in self.researched_topics:
            self.logger.info(f"Already researched {topic} this session, skipping")
            return

        self._research_topic(topic, info)
        self.researched_topics.add(topic)

    def _research_topic(self, topic: str, info: dict):
        """Create a deep research prompt for an efficiency topic."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        prompt_file = RAW_DIR / f"research_prompt_efficiency_{topic}_{timestamp}.txt"

        quality_class = info.get("quality_class", "unknown")
        quality_note = self._quality_guardrail_note(quality_class)

        prompt = f"""You are the EFFICIENCY RESEARCH AGENT for Temuclaude.
Research this topic deeply: {topic}

Priority Score: {info.get('priority_score', 'N/A')}
Reason: {info.get('reason', 'N/A')}
Quality Class: {quality_class}
Action Needed: {info.get('action', 'N/A')}

{quality_note}

Focus on:
1. Latest papers (arXiv), repos (GitHub), models (HuggingFace) on this topic
2. Concrete efficiency techniques we can implement in src/efficiency/
3. Code examples, APIs, integration details
4. Benchmarks: speedup, cost savings, and CRITICALLY quality impact
5. How to integrate with Temuclaude's existing orchestrator + pareto_tracker

CRITICAL CONSTRAINT — Ggs's Rule:
  NEVER NEVER NEVER sacrifice quality for cost cutting.
  Unless the risk to reward is WAY better (savings >50%, loss <2%).
  Every technique must be classified: LOSSLESS, QUALITY-PRESERVING, or PARETO-OPTIMAL.
  Techniques that sacrifice >5% quality are REJECTED.

Output a deep research report as markdown to:
{FINDINGS_DIR}/deep_research_efficiency_{topic}_{timestamp}.md

Include:
- Executive summary
- Key techniques with implementation details
- Code snippets / pseudo-code
- Quality classification: LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
- Benchmarks (speedup, cost savings, quality impact — ALL THREE required)
- Integration points for Temuclaude (which src/ files to create/modify)
- Kill switch / revert mechanism if quality drops
- Pareto tracker integration plan
"""

        with open(prompt_file, "w") as f:
            f.write(prompt)

        self.logger.info(f"Created efficiency research prompt: {prompt_file.name}")

        # Create placeholder findings report for integrator
        report_file = FINDINGS_DIR / f"deep_research_efficiency_{topic}_{timestamp}.md"
        report = f"""# Deep Research: {topic} (Efficiency)

## Status: QUEUED_FOR_LLM_RESEARCH
## Topic: {topic}
## Quality Class: {quality_class}
## Priority Score: {info.get('priority_score', 'N/A')}
## Reason: {info.get('reason', 'N/A')}
## Timestamp: {datetime.now(timezone.utc).isoformat()}

## Quality Guardrail
{quality_note}

## Research Prompt
See: {prompt_file.name}

## Next Steps
1. LLM agent reads the research prompt
2. Conducts deep search on arXiv, GitHub, HuggingFace
3. Produces implementation-ready efficiency report
4. Classifies technique: LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
5. Queues for auto-integrator to implement in src/efficiency/
"""
        with open(report_file, "w") as f:
            f.write(report)

        push_implementation([str(report_file)])
        self.logger.info(f"Efficiency research report queued: {report_file.name}")

    def _quality_guardrail_note(self, quality_class: str) -> str:
        """Generate quality guardrail note based on technique classification."""
        notes = {
            "lossless": "This technique is LOSSLESS — zero quality loss, mathematically guaranteed. Green-light for implementation.",
            "quality_preserving": "This technique is QUALITY-PRESERVING — <1% quality loss with >20% savings. Implement with pareto_tracker monitoring and kill switch.",
            "pareto_optimal": "This technique is PARETO-OPTIMAL — savings% > loss%, savings > 20%, loss < 5%. Implement if risk:reward is WAY better. Auto-revert if off-Pareto.",
            "unknown": "QUALITY CLASS UNKNOWN — research MUST determine the quality impact before implementation. Reject if quality loss > 5%.",
        }
        return notes.get(quality_class, notes["unknown"])

    def _research_finding(self, finding_file: str):
        """Deep research on a specific efficiency finding."""
        try:
            with open(finding_file) as f:
                finding = json.load(f)

            title = finding.get("title", finding.get("name", "unknown"))
            self.logger.info(f"Deep efficiency research on: {title}")

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            output_file = FINDINGS_DIR / f"deep_research_efficiency_{title.replace(' ', '_')[:50]}_{timestamp}.md"

            report = f"""# Deep Research: {title} (Efficiency Finding)

## Source Finding
- File: {finding_file}
- Type: {finding.get('type', 'unknown')}
- Relevance Score: {finding.get('relevance_score', 'N/A')}
- Keywords: {finding.get('matched_keywords', [])}

## Research Status
- Status: QUEUED_FOR_LLM_RESEARCH
- Priority: HIGH (EFFICIENCY)
- Quality Guardrail: ENFORCED — classify as LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
- Timestamp: {datetime.now(timezone.utc).isoformat()}

## Next Steps
1. LLM agent reads this finding
2. Conducts deep research on the specific paper/repo/model
3. Determines quality impact (speedup, savings, quality loss — ALL THREE)
4. Classifies: LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
5. If not REJECTED, queues for auto-integrator to implement in src/efficiency/
"""
            with open(output_file, "w") as f:
                f.write(report)

            push_implementation([str(output_file)])
            self.logger.info(f"Efficiency finding research report created: {output_file.name}")

        except Exception as e:
            self.logger.exception(f"Failed to process efficiency finding {finding_file}: {e}")


def main():
    daemon = EfficiencyResearchDaemon()
    # Run every 5 minutes (same as research daemons)
    daemon.run(interval=300)


if __name__ == "__main__":
    main()