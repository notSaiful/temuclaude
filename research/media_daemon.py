#!/usr/bin/env python3
"""
Media Generation Research Daemon - Continuous image/video generation research.

This daemon is dedicated to researching how to ALWAYS beat frontier image and
video generation models (GPT Image 2, Sora 2, Veo 3.1, Runway Gen-4.5, FLUX.2,
Midjourney V7) via orchestration.

It:
1. Pulls media generation findings from the queue
2. Runs deep research on top media priorities (new frontier models, techniques)
3. Generates implementation-ready reports for src/media/ improvements
4. Queues them for the auto-integrator
5. Tracks frontier model releases and benchmark changes

This runs alongside the existing 9 daemons, focused on media generation.
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase
from queue import pop_findings, push_implementation
from dynamic_priorities import calculate_dynamic_priorities

RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")
FINDINGS_DIR = RESEARCH_DIR / "findings"
RAW_DIR = RESEARCH_DIR / "raw"

MEDIA_TOPICS = {
    "media_model_pool_update", "s3_verifier_guided_denoising",
    "flux2_multi_reference", "sora2_audio_video", "veo31_cinematic",
    "runway_gen45", "image_editing_mode", "video_temporal_consistency",
    "multimodal_judge_vision", "media_dynamic_routing",
    "diffusion_acceleration_media", "controlnet_all_models",
    "media_pipeline_verify", "text_to_3d_generation",
    "world_model_interactive_video", "unified_multimodal_generation",
    "long_video_generation",
}

MEDIA_KEYWORDS = [
    "text-to-image", "text-to-video", "image generation", "video generation",
    "diffusion", "FLUX", "Sora", "Veo", "Runway", "Midjourney", "DALL-E",
    "Imagen", "Stable Diffusion", "GPT Image", "Grok Imagine", "Seedance",
    "controlnet", "instructpix2pix", "text-to-3d", "world model",
    "VBench", "ELO arena", "consistency model", "flow matching",
    "rectified flow", "multi-reference", "temporal consistency",
    "denoising", "best-of-N", "verifier guided", "image editing",
    "video audio", "cinematic", "photoreal", "prompt following",
    "motion quality", "DiT", "diffusion transformer",
]


class MediaResearchDaemon(DaemonBase):
    """Continuous media generation research daemon — BEAT FRONTIERS."""

    def __init__(self):
        super().__init__("media_daemon")
        self.cycle = 0
        self.researched_topics = set()

    def run_once(self) -> bool:
        self.cycle += 1
        self.logger.info(f"=== Media research cycle {self.cycle} started ===")

        findings = pop_findings(3)
        media_findings = [f for f in findings if self._is_media_finding(f)]

        if media_findings:
            self.logger.info(f"Found {len(media_findings)} media findings in queue")
            for f in media_findings:
                self._research_finding(f)
        else:
            self._research_top_media_priority()

        self.logger.info(f"=== Media research cycle {self.cycle} complete ===")
        return True

    def _is_media_finding(self, finding_file: str) -> bool:
        try:
            with open(finding_file) as f:
                data = json.load(f)
            text = json.dumps(data).lower()
            return any(kw.lower() in text for kw in MEDIA_KEYWORDS)
        except Exception:
            return False

    def _research_top_media_priority(self):
        priorities = calculate_dynamic_priorities()

        top_media = None
        for name, info in priorities.items():
            if name in MEDIA_TOPICS and info.get("action") != "stop_researching":
                top_media = (name, info)
                break

        if not top_media:
            self.logger.info("No media topics to research")
            return

        topic, info = top_media
        score = info.get("priority_score", 0)
        self.logger.info(f"Top media priority: {topic} (score: {score})")

        if topic in self.researched_topics:
            self.logger.info(f"Already researched {topic} this session, skipping")
            return

        self._research_topic(topic, info)
        self.researched_topics.add(topic)

    def _research_topic(self, topic: str, info: dict):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        prompt_file = RAW_DIR / f"research_prompt_media_{topic}_{timestamp}.txt"

        prompt = f"""You are the MEDIA GENERATION RESEARCH AGENT for Temuclaude.
Research this topic deeply: {topic}

Priority Score: {info.get('priority_score', 'N/A')}
Reason: {info.get('reason', 'N/A')}
Action Needed: {info.get('action', 'N/A')}

MISSION: Always beat frontier image/video generation models via orchestration.

Context — Temuclaude's existing media pipeline:
- src/media/ (13 files, 5911 LOC, 10-stage pipeline)
- Cascading generator (554 LOC) — multi-model best-of-N
- Judge (608 LOC) — LLM judge evaluates quality
- Quality gate (323 LOC) — quality threshold enforcement
- Intent detector (278 LOC) — route to best model per intent
- Prompt enhancer (361 LOC) — LLM prompt improvement
- Media cache (214 LOC) — deduplication
- Post-processor (236 LOC) — upscaling, enhancement
- Models (660 LOC) — model pool management

Academic foundation (3 papers prove our approach works):
- arXiv:2501.09732 — Inference-Time Scaling for Diffusion (Google DeepMind)
- arXiv:2507.05604 — Kernel Density Steering (N-particle ensemble)
- arXiv:2604.06260 — S³ Stratified Scaling Search (verifier-guided denoising)

Focus on:
1. Latest papers on arXiv, repos on GitHub, models on HuggingFace for this topic
2. Concrete techniques to implement in src/media/
3. Code examples, APIs, integration details
4. Benchmarks: ELO scores, quality metrics, comparison vs frontiers
5. How to integrate with existing 10-stage pipeline
6. Which frontier models to add to the pool

Output a deep research report as markdown to:
{FINDINGS_DIR}/deep_research_media_{topic}_{timestamp}.md

Include:
- Executive summary
- Key techniques with implementation details
- Code snippets / pseudo-code
- Benchmark comparison: Temuclaude vs frontier (GPT Image 2, Sora 2, etc.)
- Integration points for Temuclaude (which src/media/ files to modify)
- Model pool update recommendations (which new models to add)
- Quality assessment (does this beat frontiers? how?)
"""

        with open(prompt_file, "w") as f:
            f.write(prompt)

        self.logger.info(f"Created media research prompt: {prompt_file.name}")

        report_file = FINDINGS_DIR / f"deep_research_media_{topic}_{timestamp}.md"
        report = f"""# Deep Research: {topic} (Media Generation)

## Status: QUEUED_FOR_LLM_RESEARCH
## Topic: {topic}
## Priority Score: {info.get('priority_score', 'N/A')}
## Mission: BEAT FRONTIERS (GPT Image 2, Sora 2, Veo 3.1, Runway Gen-4.5)
## Timestamp: {datetime.now(timezone.utc).isoformat()}

## Research Prompt
See: {prompt_file.name}

## Next Steps
1. LLM agent reads the research prompt
2. Conducts deep search on arXiv, GitHub, HuggingFace, Artificial Analysis
3. Produces implementation-ready media generation report
4. Identifies which frontier models to add to pool
5. Queues for auto-integrator to implement in src/media/
"""
        with open(report_file, "w") as f:
            f.write(report)

        push_implementation([str(report_file)])
        self.logger.info(f"Media research report queued: {report_file.name}")

    def _research_finding(self, finding_file: str):
        try:
            with open(finding_file) as f:
                finding = json.load(f)

            title = finding.get("title", finding.get("name", "unknown"))
            self.logger.info(f"Deep media research on: {title}")

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            output_file = FINDINGS_DIR / f"deep_research_media_{title.replace(' ', '_')[:50]}_{timestamp}.md"

            report = f"""# Deep Research: {title} (Media Generation Finding)

## Source Finding
- File: {finding_file}
- Type: {finding.get('type', 'unknown')}
- Relevance Score: {finding.get('relevance_score', 'N/A')}
- Keywords: {finding.get('matched_keywords', [])}

## Research Status
- Status: QUEUED_FOR_LLM_RESEARCH
- Priority: HIGH (MEDIA GENERATION — BEAT FRONTIERS)
- Timestamp: {datetime.now(timezone.utc).isoformat()}

## Next Steps
1. LLM agent reads this finding
2. Conducts deep research on the specific paper/repo/model
3. Assesses how it helps beat frontier image/video models
4. Produces implementation-ready report
5. Queues for auto-integrator to implement in src/media/
"""
            with open(output_file, "w") as f:
                f.write(report)

            push_implementation([str(output_file)])
            self.logger.info(f"Media finding research report created: {output_file.name}")

        except Exception as e:
            self.logger.exception(f"Failed to process media finding {finding_file}: {e}")


def main():
    daemon = MediaResearchDaemon()
    daemon.run(interval=300)


if __name__ == "__main__":
    main()