# Media Generation Domain Integration (added 2026-07-06)

Complete integration pattern for adding media generation research to the Temuclaude swarm.

## What Was Added

### New Files
1. `research/MASTER-MEDIA-GENERATION-BREAKTHROUGHS-2026-07-06.md` — 24 techniques, 3 tiers, frontier landscape table
2. `research/findings/deep_research_media_generation_2026-07-06.md` — 16KB deep research report with citations
3. `research/media_daemon.py` — dedicated media research daemon (NEW 10th daemon)

### Modified Files
1. `scripts/scout_arxiv.py` — +21 media queries (81 total)
2. `scripts/scout_github.py` — +23 media queries (85 total)
3. `scripts/scout_huggingface.py` — +30 media keywords, +6 media model searches
4. `scripts/dynamic_priorities.py` — +17 media techniques in MISSING_TECHNIQUES with quality_class
5. `coordinator_daemon.py` — media_daemon registered in DAEMON_SCRIPTS
6. `daemon_base.py` — media_daemon added to get_all_daemon_statuses (10 daemons)
7. `scripts/start_swarm.sh` — starts 10 daemons with media generation mission
8. `scripts/status_swarm.sh` — media_daemon added to dashboard daemon array
9. `TRACKER.md` — full media generation section

### Cron Job
- Name: "Temuclaude Media Generation Deep Research (Daily 4am IST)"
- Schedule: `0 4 * * *` (daily at 4am IST — staggered after cyber 2am and efficiency 3am)
- Skills loaded: `deep-research-mode`
- Job ID: `028cc2e55cc8`

## The 17 Media Techniques (in dynamic_priorities.py)

| Technique | Impact | Quality Class | Action |
|-----------|--------|---------------|--------|
| media_model_pool_update | 10 | lossless | implement_now |
| s3_verifier_guided_denoising | 9 | lossless | research_and_implement |
| flux2_multi_reference | 9 | lossless | implement_now |
| sora2_audio_video | 9 | lossless | implement_now |
| veo31_cinematic | 8 | lossless | implement_now |
| runway_gen45 | 8 | lossless | implement_now |
| image_editing_mode | 8 | lossless | implement_now |
| video_temporal_consistency | 8 | quality_preserving | research_and_implement |
| multimodal_judge_vision | 8 | quality_preserving | implement_now |
| media_dynamic_routing | 8 | quality_preserving | research_and_implement |
| diffusion_acceleration_media | 7 | quality_preserving | research_and_implement |
| controlnet_all_models | 7 | lossless | research_and_implement |
| media_pipeline_verify | 7 | lossless | implement_now |
| text_to_3d_generation | 6 | lossless | track_for_future |
| world_model_interactive_video | 6 | lossless | track_for_future |
| unified_multimodal_generation | 7 | lossless | track_for_future |
| long_video_generation | 7 | quality_preserving | track_for_future |

## Media Daemon Architecture

`media_daemon.py` follows the same pattern as `cyber_daemon.py` and `efficiency_daemon.py`:

```python
class MediaResearchDaemon(DaemonBase):
    def __init__(self):
        super().__init__("media_daemon")

    def run_once(self) -> bool:
        # 1. Check queue for media findings
        findings = pop_findings(3)
        media_findings = [f for f in findings if self._is_media_finding(f)]
        # 2. If findings, research them; else research top media priority
        # 3. Generate research prompt + placeholder report
        # 4. Push to implementation queue
```

Key sets:
- `MEDIA_TOPICS` — 17 technique names this daemon focuses on
- `MEDIA_KEYWORDS` — 38 keywords to identify media findings from the queue

## Frontier Models to Beat

### Image (Artificial Analysis ELO, July 2026)
- GPT Image 2 (high) — 1340 ELO, #1 overall quality + instruction following
- Reve 2.0 — 1281 ELO, photorealism
- FLUX.2 [max] — 1193 ELO, open weight, 4MP photoreal, multi-reference, pose control
- Midjourney V7 — ~1280 ELO, art direction

### Video (Artificial Analysis ELO, July 2026)
- Runway Gen-4.5 — 1247 ELO, #1 motion quality
- Sora 2 — ~1230 ELO, physical accuracy, world simulation, synced audio
- Veo 3.1 — ~1220 ELO, cinematic quality + audio
- Seedance 2.0 — 1225 ELO, cost efficiency

## Academic Foundation (3 Google DeepMind Papers)

1. **arXiv:2501.09732** — "Inference-Time Scaling for Diffusion Models" — proves best-of-N works for diffusion. Verifiers + algorithms. Validates Temuclaude's multi-model + LLM judge approach.

2. **arXiv:2507.05604** — "Kernel Density Steering (KDS)" — N-particle ensemble, "collective wisdom" steers away from artifacts. Temuclaude's N DIFFERENT models is even stronger (adds model diversity, not just noise diversity).

3. **arXiv:2604.06260** — "S³ Stratified Scaling Search" — verifier-guided denoising at each step. Beyond best-of-N. Corrects course during generation, not just at final selection.

## Existing Media Pipeline (Baseline)

`src/media/` — 13 files, 5911 LOC, 12 phases pass:
- cascading_generator.py (554 LOC) — multi-model best-of-N
- generator.py (424 LOC) — core generation pipeline
- intent.py (278 LOC) — route to best model per intent
- judge.py (608 LOC) — LLM judge evaluates quality
- media_cache.py (214 LOC) — deduplication
- memory.py (275 LOC) — pattern learning
- models.py (660 LOC) — model pool management
- orchestrator.py (444 LOC) — full pipeline orchestration
- post_processor.py (236 LOC) — upscaling, enhancement
- prompt_enhancer.py (361 LOC) — LLM prompt improvement
- quality_gate.py (323 LOC) — quality threshold enforcement
- tts_intent.py, tts_models.py, tts_orchestrator.py, tts_provider.py — TTS pipeline

Gap: Model pool needs latest frontiers (FLUX.2, Sora 2, Veo 3.1, Runway Gen-4.5). Need editing mode, temporal consistency, verifier-guided denoising.

## First Daemon Cycle

Media daemon started 2026-07-06 19:48 IST (PID 69804). First cycle identified `s3_verifier_guided_denoising` (score 115) as top media priority and generated research prompt `research_prompt_media_s3_verifier_guided_denoising_20260706T141843.txt`.

## Research Pattern (Adding Any New Domain)

Follow this exact pattern to add any new research domain to the swarm:

1. Research the domain (arXiv API, Startpage search, scrape key sources)
2. Create `research/MASTER-<DOMAIN>-BREAKTHROUGHS-<date>.md` — techniques, tiers, frontier landscape
3. Create `research/findings/deep_research_<domain>_<date>.md` — deep research report with citations
4. Add +N queries to `scout_arxiv.py`, `scout_github.py`, `scout_huggingface.py`
5. Add +N techniques to `MISSING_TECHNIQUES` in `dynamic_priorities.py` (with impact, quality_class)
6. Add blocked techniques to `BLOCKED_TECHNIQUES` if needed
7. Create `research/<domain>_daemon.py` — dedicated daemon
8. Register in `coordinator_daemon.py` DAEMON_SCRIPTS
9. Add to `daemon_base.py` get_all_daemon_statuses daemons list
10. Add to `scripts/status_swarm.sh` daemons array
11. Add to `scripts/start_swarm.sh` (increment daemon count N/10 → N/11)
12. Update `TRACKER.md` with domain section
13. Create daily cron job with staggered schedule (2am, 3am, 4am, 5am...)
14. Start the daemon, verify it's live in status dashboard
15. Verify priority engine picks up new techniques (run `python3 scripts/dynamic_priorities.py`)
16. Update this skill's SKILL.md with new daemon count and domain section
17. Create `references/<domain>-integration.md` reference file (this file)