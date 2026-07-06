"""
Dynamic Priority Engine for Temuclaude Research Swarm.

Instead of fixed priority ranks, this engine calculates REAL-TIME priority
based on what temuclaude actually needs RIGHT NOW. It reads:
- Current source code (what's implemented vs missing)
- Research findings (what's been discovered vs what's still unknown)
- CHANGELOG (what was recently integrated vs rejected)
- Test results (what's working vs broken)
- Benchmark gaps (where we're weakest vs frontier models)

The engine outputs a dynamic priority score for each research topic,
adjusting in real time based on the project's current state.

This is called by the cron jobs to determine WHERE to spend tokens.
"""

import os
import json
import glob
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple


TEMUCLAUDE_DIR = os.path.expanduser("~/temuclaude")
RESEARCH_DIR = os.path.join(TEMUCLAUDE_DIR, "research")
SRC_DIR = os.path.join(TEMUCLAUDE_DIR, "src")
CHANGELOG = os.path.join(RESEARCH_DIR, "CHANGELOG.md")
TRACKER = os.path.join(RESEARCH_DIR, "TRACKER.md")
RAW_DIR = os.path.join(RESEARCH_DIR, "raw")
FINDINGS_DIR = os.path.join(RESEARCH_DIR, "findings")


# ============================================================
# TECHNIQUE DATABASE — what exists, what's missing, what's blocked
# ============================================================

# Techniques we've already implemented (checked against source code)
IMPLEMENTED_TECHNIQUES = {
    "prm_weighted_voting": {"file": "consistency.py", "function": "prm_weighted_vote", "status": "implemented"},
    "adaptive_sample_count": {"file": "consistency.py", "function": "get_adaptive_n_samples", "status": "implemented"},
    "usva_4_rubric": {"file": "self_qa.py", "function": "build_usva_prompt", "status": "implemented"},
    "reflexion_memory": {"file": "self_qa.py", "function": "build_reflexion_prompt", "status": "implemented"},
    "moa_3layer": {"file": "fusion.py", "function": "build_cross_review_prompt", "status": "implemented"},
    "self_moa": {"file": "orchestrator.py", "function": "should_use_self_moA", "status": "implemented"},
    "atts_adaptive_compute": {"file": "orchestrator.py", "function": "get_adaptive_token_budget", "status": "implemented"},
    "unified_routing_cascading": {"file": "orchestrator.py", "function": "complete", "status": "implemented"},
    "tree_of_thoughts": {"file": "tot.py", "function": "tree_of_thoughts", "status": "implemented"},
    "selective_debate": {"file": "debate.py", "function": "multi_agent_debate", "status": "implemented"},
    "skill_curator": {"file": "skill_curator.py", "function": "track_skill_usage", "status": "implemented"},
}

# Techniques we know we need but haven't implemented
MISSING_TECHNIQUES = {
    "mcts_full": {
        "reason": "THE breakthrough (rStar-Math: 58.8%→90%). Need implementation details for our model pool.",
        "blocked_by": "need_code_analysis",  # Need to study existing MCTS repos
        "research_needed": "maximum",
        "impact": 10,
    },
    "prm_training": {
        "reason": "PRM-weighted voting implemented but no TRAINED PRM. Need auto-data-generation (OmegaPRM).",
        "blocked_by": "need_training_methodology",
        "research_needed": "maximum",
        "impact": 9,
    },
    "dspy_integration": {
        "reason": "DSPy/MIPROv2 gives 10-50% gains, enables self-improvement. Not integrated.",
        "blocked_by": "need_framework_understanding",
        "research_needed": "maximum",
        "impact": 9,
    },
    "step_level_code_verification": {
        "reason": "We verify final answers but not intermediate steps. rStar-Math pattern.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 8,
    },
    "preference_data_router": {
        "reason": "RouteLLM gives 2x cost reduction with preference-data-trained routing.",
        "blocked_by": "need_data_collection_method",
        "research_needed": "high",
        "impact": 7,
    },
    "pareto_efficiency_tracking": {
        "reason": "Track token_savings vs accuracy_loss. Auto-tune thresholds.",
        "blocked_by": None,  # Can implement now
        "research_needed": "low",
        "impact": 4,
    },
    "marketing_strategy": {
        "reason": "Zero marketing done. No users, no community, no attention.",
        "blocked_by": "need_research",  # Completely new area
        "research_needed": "maximum",
        "impact": 10,
    },
    # === CYBERSECURITY (added 2026-07-06) ===
    "cognitive_firewall": {
        "reason": "4-gate zero-trust defense. Reduces attack success to 2%. NOT implemented.",
        "blocked_by": "need_implementation_details",
        "research_needed": "maximum",
        "impact": 10,
    },
    "self_healing_guard": {
        "reason": "Self-healing injection defense (Silmaril pattern). Retrains on new attacks in <1h. NOT implemented.",
        "blocked_by": "need_architecture_design",
        "research_needed": "maximum",
        "impact": 10,
    },
    "haloguard_classifier": {
        "reason": "Open-weights constitutional classifier, 90.9 F1 at 1/10 model size. NOT implemented.",
        "blocked_by": "need_model_download",
        "research_needed": "high",
        "impact": 9,
    },
    "knnguard_guardrail": {
        "reason": "Training-free guardrail using kNN on activations. 2.7x faster. NOT implemented.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 9,
    },
    "owasp_llm_top10": {
        "reason": "OWASP LLM Top 10 (2025) compliance. 10 vulnerability classes, ZERO implemented.",
        "blocked_by": "need_research",
        "research_needed": "high",
        "impact": 9,
    },
    "owasp_agentic_top10": {
        "reason": "OWASP Agentic Top 10 (2026) compliance. Agent-specific threats, ZERO implemented.",
        "blocked_by": "need_research",
        "research_needed": "high",
        "impact": 9,
    },
    "ai_infra_guard": {
        "reason": "4-layer red teaming framework. 1400+ vuln rules. Need to integrate for self-testing.",
        "blocked_by": "need_framework_integration",
        "research_needed": "high",
        "impact": 8,
    },
    "red_blue_loop": {
        "reason": "Self-attacking self-improving defense loop. THE architecture for unbeatable security.",
        "blocked_by": "need_full_architecture",
        "research_needed": "maximum",
        "impact": 10,
    },
    "antaeus_scanner": {
        "reason": "Repository-level logic vulnerability detection. Finds bugs memory-safety scanners miss.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 7,
    },
    "function_call_defense": {
        "reason": "Function-calling jailbreak via SMT pattern. Must sanitize tool outputs + enforce schemas.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 8,
    },
    "lifecycle_defenses": {
        "reason": "8-stage lifecycle vulnerability defense. Only inference-time defense exists currently.",
        "blocked_by": "need_research",
        "research_needed": "high",
        "impact": 8,
    },
    "supply_chain_defense": {
        "reason": "Model poisoning, backdoor, dependency attacks. Zero supply chain security implemented.",
        "blocked_by": "need_research",
        "research_needed": "high",
        "impact": 8,
    },
    "backdoor_detection": {
        "reason": "Backdoor attacks (Pmeta-TLA, ReShift). No detection implemented.",
        "blocked_by": "need_research",
        "research_needed": "medium",
        "impact": 7,
    },
    "adversarial_verifier_security": {
        "reason": "Existing adversarial_verifier.py only checks code quality. EXTEND to security.",
        "blocked_by": None,  # Can implement now — extend existing file
        "research_needed": "low",
        "impact": 8,
    },
    # === EFFICIENCY (added 2026-07-06) — QUALITY GUARDRAIL ENFORCED ===
    "semantic_caching": {
        "reason": "Semantic cache: 20% hit rate, 100% savings on hit. QUALITY-PRESERVING (0.95+ threshold). NOT implemented.",
        "blocked_by": None,  # Can implement now — embedding model + vector store
        "research_needed": "high",
        "impact": 9,
        "quality_class": "quality_preserving",
    },
    "prefix_caching": {
        "reason": "KV cache reuse for shared prefixes. 90% input token savings. LOSSLESS. NOT implemented.",
        "blocked_by": None,  # Can implement now — restructure prompt templates
        "research_needed": "high",
        "impact": 9,
        "quality_class": "lossless",
    },
    "routellm_cascade": {
        "reason": "RouteLLM cascade routing: 85% savings, 95% GPT-4 quality. Extend existing preference_router.py (526 LOC).",
        "blocked_by": "need_preference_data_training",
        "research_needed": "high",
        "impact": 10,
        "quality_class": "quality_preserving",
    },
    "structured_output": {
        "reason": "Constrained generation: 100% valid output, eliminates retries. LOSSLESS. NOT implemented.",
        "blocked_by": None,  # Can implement now — provider-native JSON mode
        "research_needed": "medium",
        "impact": 7,
        "quality_class": "lossless",
    },
    "provider_prompt_caching": {
        "reason": "Provider-native prompt caching (Anthropic/OpenAI): 90% input savings. LOSSLESS. NOT optimized.",
        "blocked_by": None,  # Can implement now — restructure prompts for caching
        "research_needed": "medium",
        "impact": 8,
        "quality_class": "lossless",
    },
    "efficiency_pareto_monitoring": {
        "reason": "Pareto tracker exists (266 LOC) but may not be actively monitoring production. Verify + extend.",
        "blocked_by": None,  # Can implement now — verify existing tracker
        "research_needed": "low",
        "impact": 8,
        "quality_class": "pareto_optimal",
    },
    "speculative_decoding": {
        "reason": "2-3x speedup, LOSSLESS. Blocked by self-hosting OR provider-native support.",
        "blocked_by": "needs_self_hosted_vllm",
        "research_needed": "medium",
        "impact": 9,
        "quality_class": "lossless",
    },
    "continuous_batching": {
        "reason": "2-3x throughput via PagedAttention. LOSSLESS. Blocked by self-hosting.",
        "blocked_by": "needs_self_hosted_vllm",
        "research_needed": "low",
        "impact": 7,
        "quality_class": "lossless",
    },
    "awq_quantization": {
        "reason": "AWQ 4-bit: 4x memory, 10-20% speed, <1% loss. PRESERVING. Blocked by self-hosting.",
        "blocked_by": "needs_self_hosted_vllm",
        "research_needed": "low",
        "impact": 7,
        "quality_class": "quality_preserving",
    },
    "early_exit_adaptive": {
        "reason": "Apple Duo-LLM: 30-50% compute savings, <1% loss. PRESERVING. Blocked by self-hosting.",
        "blocked_by": "needs_self_hosted_vllm",
        "research_needed": "medium",
        "impact": 7,
        "quality_class": "quality_preserving",
    },
    "teacher_student_distillation": {
        "reason": "DSPy teacher-student: 50x cost reduction. PRESERVING with cascade fallback. Blocked by DSPy.",
        "blocked_by": "needs_dspy_framework",
        "research_needed": "medium",
        "impact": 8,
        "quality_class": "quality_preserving",
    },
    "dflash_speculator_training": {
        "reason": "Custom DFlash draft models: +5-20% over base spec decoding. LOSSLESS. Blocked by training.",
        "blocked_by": "needs_training_pipeline",
        "research_needed": "low",
        "impact": 7,
        "quality_class": "lossless",
    },
    "model_weight_merging_eff": {
        "reason": "TIES/Task Arithmetic: +1.62 mean gain, 80-100% success. LOSSLESS. Blocked by self-hosting.",
        "blocked_by": "needs_self_hosted_vllm",
        "research_needed": "low",
        "impact": 6,
        "quality_class": "lossless",
    },
    "efficiency_continuous_improvement": {
        "reason": "DSPy+GEPA continuous Pareto improvement loop. 10-50% from prompt optimization. PRESERVING.",
        "blocked_by": "needs_dspy_framework",
        "research_needed": "high",
        "impact": 9,
        "quality_class": "pareto_optimal",
    },
    # === MEDIA GENERATION (added 2026-07-06) — BEAT FRONTIERS ===
    "media_model_pool_update": {
        "reason": "Model pool must include latest frontiers: FLUX.2, Sora 2, Veo 3.1, Runway Gen-4.5, GPT Image 2. VERIFY+UPDATE.",
        "blocked_by": None,  # Can implement now — update model list
        "research_needed": "high",
        "impact": 10,
        "quality_class": "lossless",
    },
    "s3_verifier_guided_denoising": {
        "reason": "S³ Stratified Scaling Search (arXiv:2604.06260): verifier guides denoising at each step. Beyond best-of-N.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 9,
        "quality_class": "lossless",
    },
    "flux2_multi_reference": {
        "reason": "FLUX.2 multi-reference: 6 reference images, consistent style, pose control, 4MP photoreal. NOT in pool.",
        "blocked_by": None,  # Can implement — add FLUX.2 provider
        "research_needed": "high",
        "impact": 9,
        "quality_class": "lossless",
    },
    "sora2_audio_video": {
        "reason": "Sora 2: video + synchronized dialogue + sound effects. Frontier capability. NOT in pool.",
        "blocked_by": None,  # Can implement — add Sora 2 provider
        "research_needed": "high",
        "impact": 9,
        "quality_class": "lossless",
    },
    "veo31_cinematic": {
        "reason": "Veo 3.1: cinematic video with audio. Matches Sora 2. NOT in pool.",
        "blocked_by": None,  # Can implement — add Veo 3.1 provider
        "research_needed": "high",
        "impact": 8,
        "quality_class": "lossless",
    },
    "runway_gen45": {
        "reason": "Runway Gen-4.5: #1 motion quality (1247 ELO). NOT in pool.",
        "blocked_by": None,  # Can implement — add Runway provider
        "research_needed": "high",
        "impact": 8,
        "quality_class": "lossless",
    },
    "image_editing_mode": {
        "reason": "Image editing with instruction following (Grok Imagine, GPT Image 2 pattern). NOT implemented.",
        "blocked_by": None,  # Can implement — extend generator + intent
        "research_needed": "high",
        "impact": 8,
        "quality_class": "lossless",
    },
    "video_temporal_consistency": {
        "reason": "Temporal consistency enforcement for video. Frontier models do this internally. We need a checker.",
        "blocked_by": "need_implementation_details",
        "research_needed": "high",
        "impact": 8,
        "quality_class": "quality_preserving",
    },
    "multimodal_judge_vision": {
        "reason": "Use vision-language model as judge for image/video quality. Better judge = better best-of-N.",
        "blocked_by": None,  # Can implement — upgrade judge model
        "research_needed": "medium",
        "impact": 8,
        "quality_class": "quality_preserving",
    },
    "media_dynamic_routing": {
        "reason": "Track which media model wins for which intent. Auto-route to best model (RouteLLM for media).",
        "blocked_by": "need_preference_data",
        "research_needed": "medium",
        "impact": 8,
        "quality_class": "quality_preserving",
    },
    "diffusion_acceleration_media": {
        "reason": "Consistency models, guided distillation, ParallelVLM: faster generation, same quality. PRESERVING.",
        "blocked_by": "need_implementation_details",
        "research_needed": "medium",
        "impact": 7,
        "quality_class": "quality_preserving",
    },
    "controlnet_all_models": {
        "reason": "ControlNet-like guidance (pose, depth, edges) for all models, not just FLUX.2.",
        "blocked_by": "need_implementation_details",
        "research_needed": "medium",
        "impact": 7,
        "quality_class": "lossless",
    },
    "media_pipeline_verify": {
        "reason": "Verify existing 10-stage pipeline (5911 LOC) is using latest models and best prompts.",
        "blocked_by": None,  # Can implement now — verify
        "research_needed": "low",
        "impact": 7,
        "quality_class": "lossless",
    },
    "text_to_3d_generation": {
        "reason": "Text-to-3D generation (arXiv:2607.02516 X-to-4D). Emerging frontier capability.",
        "blocked_by": "need_3d_infrastructure",
        "research_needed": "medium",
        "impact": 6,
        "quality_class": "lossless",
    },
    "world_model_interactive_video": {
        "reason": "WorldDirector (arXiv:2607.02517): interactive, controllable video worlds. Next gen.",
        "blocked_by": "need_world_model_infra",
        "research_needed": "low",
        "impact": 6,
        "quality_class": "lossless",
    },
    "unified_multimodal_generation": {
        "reason": "Single model for image+video+audio (Gemini Omni pattern). Eliminates model selection.",
        "blocked_by": "need_unified_model",
        "research_needed": "low",
        "impact": 7,
        "quality_class": "lossless",
    },
    "long_video_generation": {
        "reason": "Generate minutes of video (not seconds). Requires temporal consistency + scene memory.",
        "blocked_by": "need_long_video_infra",
        "research_needed": "low",
        "impact": 7,
        "quality_class": "quality_preserving",
    },
}

# Techniques blocked by infrastructure (can't implement with cloud API)
BLOCKED_TECHNIQUES = {
    "hermes_self_evolution": {"blocked_by": "needs_dspy_framework", "impact": 8},
    "layer_4_compression": {"blocked_by": "needs_context_module", "impact": 6},
    "speculative_tool_execution": {"blocked_by": "needs_async_architecture", "impact": 5},
    "miprov2": {"blocked_by": "needs_dspy_framework", "impact": 7},
    "fork_agents_cache": {"blocked_by": "needs_parallel_refactor", "impact": 5},
    "teacher_student_distillation": {"blocked_by": "needs_dspy", "impact": 6},
    "vstar_dpo_verifier": {"blocked_by": "needs_training_pipeline", "impact": 6},
    "full_mcts_ppm": {"blocked_by": "needs_prm_training", "impact": 10},
    "collaborative_parallel_thinking": {"blocked_by": "needs_mcts_first", "impact": 7},
    "model_weight_merging": {"blocked_by": "needs_self_hosted_vllm", "impact": 5},
    "token_level_speculative_decoding": {"blocked_by": "needs_self_hosted_vllm", "impact": 5},
    "honcho_user_modeling": {"blocked_by": "needs_honcho_integration", "impact": 3},
    # === CYBERSECURITY — BLOCKED BY TRAINING INFRA ===
    "harc_alignment": {"blocked_by": "needs_fine_tuning_pipeline", "impact": 9},
    "autonomous_red_blue_ecosystem": {"blocked_by": "needs_red_blue_infra", "impact": 10},
    "offensive_swarm": {"blocked_by": "needs_offensive_agent_infra", "impact": 8},
    "neurosymbolic_scanner": {"blocked_by": "needs_cpg_tooling", "impact": 7},
    "mobile_agent_security": {"blocked_by": "needs_mobile_infra", "impact": 5},
    "context_lake": {"blocked_by": "needs_database_setup", "impact": 7},
}

# Research areas that are saturated (no more research needed)
SATURATED_AREAS = [
    "management_science", "planning_theory", "quality_control",
    "coding_agent_architecture", "military_planning", "self_managing_systems",
    "meta_cognition", "organizing_principles", "directing_principles",
    "controlling_principles",
]


# ============================================================
# REAL-TIME STATE ANALYSIS
# ============================================================

def get_implementation_status() -> Dict:
    """Check which techniques are actually implemented by reading source code."""
    status = {}
    for name, info in IMPLEMENTED_TECHNIQUES.items():
        filepath = os.path.join(SRC_DIR, info["file"])
        if os.path.isfile(filepath):
            try:
                with open(filepath) as f:
                    content = f.read()
                # Check if the function actually exists
                if info["function"] in content:
                    status[name] = "implemented"
                else:
                    status[name] = "missing_function"
            except IOError:
                status[name] = "file_error"
        else:
            status[name] = "file_missing"
    return status


def get_recent_changelog_entries() -> List[Dict]:
    """Read recent CHANGELOG entries to understand what was recently done."""
    if not os.path.isfile(CHANGELOG):
        return []
    try:
        with open(CHANGELOG) as f:
            content = f.read()
        # Parse entries — look for timestamps and actions
        entries = []
        current_entry = {}
        for line in content.split("\n"):
            if line.startswith("## "):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {"timestamp": line.replace("## ", "").strip(), "text": ""}
            elif current_entry:
                current_entry["text"] += line + "\n"
        if current_entry:
            entries.append(current_entry)
        return entries[-10:]  # Last 10 entries
    except IOError:
        return []


def get_recent_research_topics() -> Dict[str, int]:
    """Analyze recent raw findings to see what topics have been researched recently."""
    topic_counts = defaultdict(int)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)  # Last 48 hours
    
    for fpath in sorted(glob.glob(os.path.join(RAW_DIR, "*.json")), reverse=True)[:20]:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc)
            if mtime < cutoff:
                break
            with open(fpath) as f:
                data = json.load(f)
            scout = data.get("scout", "unknown")
            topic_counts[scout] += 1
            # Count findings per topic
            findings = data.get("findings", data.get("papers", data.get("repos", [])))
            topic_counts[f"{scout}_items"] += len(findings) if isinstance(findings, list) else 0
        except (json.JSONDecodeError, IOError):
            continue
    
    return dict(topic_counts)


def get_source_file_count() -> int:
    """Count source files to understand project complexity."""
    return len(glob.glob(os.path.join(SRC_DIR, "*.py")))


def get_test_status() -> Dict:
    """Check if test files exist and are recent."""
    test_dir = os.path.join(TEMUCLAUDE_DIR, "tests")
    tests = {}
    for fpath in glob.glob(os.path.join(test_dir, "test_*.py")):
        name = os.path.basename(fpath).replace("test_", "").replace(".py", "")
        mtime = os.path.getmtime(fpath)
        tests[name] = {"exists": True, "last_modified": mtime}
    return tests


# ============================================================
# DYNAMIC PRIORITY CALCULATION
# ============================================================

def calculate_dynamic_priorities() -> Dict[str, Dict]:
    """
    Calculate real-time priority scores for each research area.
    
    Factors:
    1. Impact score (how much would this improve temuclaude?)
    2. Implementation gap (is it implemented? missing? blocked?)
    3. Research saturation (have we already researched this enough?)
    4. Recency (have we researched this recently? if so, lower priority)
    5. Dependency (is this blocking other techniques?)
    
    Returns:
        Dict mapping topic → {priority_score, reason, action}
    """
    impl_status = get_implementation_status()
    recent_topics = get_recent_research_topics()
    changelog = get_recent_changelog_entries()
    
    priorities = {}
    
    # --- MISSING TECHNIQUES (highest priority — we need them) ---
    for name, info in MISSING_TECHNIQUES.items():
        if name in SATURATED_AREAS:
            continue
        
        score = info["impact"] * 10  # Base score from impact
        
        # Boost if not researched recently
        topic_key = f"rank1-deep_items" if name in ["mcts_full", "prm_training", "dspy_integration"] else None
        if topic_key and recent_topics.get(topic_key, 0) > 50:
            score -= 10  # Already heavily researched recently
        else:
            score += 10  # Needs more research
        
        # Boost if blocked by lack of research
        if info["blocked_by"] and "need" in info["blocked_by"]:
            score += 15  # Research is what's blocking implementation
        
        # Marketing is always high if not done
        if name == "marketing_strategy":
            score += 20
        
        priorities[name] = {
            "priority_score": score,
            "research_needed": info["research_needed"],
            "reason": info["reason"],
            "blocked_by": info["blocked_by"],
            "action": "research_and_implement" if info["blocked_by"] else "implement_now",
            "quality_class": info.get("quality_class", "unknown"),
        }
    
    # --- BLOCKED TECHNIQUES (lower priority — need infrastructure first) ---
    for name, info in BLOCKED_TECHNIQUES.items():
        score = info["impact"] * 3  # Lower base score (blocked)
        
        # Can still research for future, but lower priority
        score -= 10  # Blocked = lower priority
        
        priorities[name] = {
            "priority_score": score,
            "research_needed": "low",  # Track for future, don't deep research
            "reason": f"Blocked by: {info['blocked_by']}",
            "blocked_by": info["blocked_by"],
            "action": "track_for_future",
        }
    
    # --- IMPLEMENTED TECHNIQUES (lowest research priority — done) ---
    for name, info in IMPLEMENTED_TECHNIQUES.items():
        if impl_status.get(name) == "implemented":
            score = 1  # Minimal — just monitor for improvements
        else:
            score = 20  # High — supposed to be implemented but isn't!
        
        priorities[name] = {
            "priority_score": score,
            "research_needed": "minimal" if impl_status.get(name) == "implemented" else "high",
            "reason": f"Status: {impl_status.get(name, 'unknown')}",
            "action": "monitor" if impl_status.get(name) == "implemented" else "fix_implementation",
        }
    
    # --- SATURATED AREAS (zero priority) ---
    for area in SATURATED_AREAS:
        priorities[area] = {
            "priority_score": 0,
            "research_needed": "none",
            "reason": "Saturated — 2500+ lines of research already done",
            "action": "stop_researching",
        }
    
    # Sort by priority score (descending)
    sorted_priorities = dict(
        sorted(priorities.items(), key=lambda x: x[1]["priority_score"], reverse=True)
    )
    
    return sorted_priorities


def get_top_research_priorities(n: int = 10) -> List[Tuple[str, Dict]]:
    """Get the top N research priorities for the swarm to focus on."""
    priorities = calculate_dynamic_priorities()
    return list(priorities.items())[:n]


def get_research_allocation() -> Dict[str, float]:
    """
    Get token allocation percentages based on dynamic priorities.
    
    Returns percentages that sum to 100%.
    Groups by research_needed level.
    """
    priorities = calculate_dynamic_priorities()
    
    # Group topics by research needed level
    groups = defaultdict(int)
    for name, info in priorities.items():
        level = info["research_needed"]
        groups[level] += max(1, info["priority_score"])
    
    # Calculate percentages
    total = sum(groups.values())
    if total == 0:
        return {"maximum": 40, "high": 25, "medium": 20, "low": 10, "minimal": 5, "none": 0}
    
    return {
        level: round((score / total) * 100, 1)
        for level, score in sorted(groups.items(), key=lambda x: -x[1])
    }


def generate_priority_report() -> str:
    """Generate a human-readable priority report for the swarm."""
    priorities = calculate_dynamic_priorities()
    allocation = get_research_allocation()
    
    report = []
    report.append("=" * 60)
    report.append("TEMUCLAUDE RESEARCH SWARM — DYNAMIC PRIORITY REPORT")
    report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    report.append("=" * 60)
    
    report.append("\nTOKEN ALLOCATION (% of research tokens):")
    for level, pct in allocation.items():
        if pct > 0:
            report.append(f"  {level}: {pct}%")
    
    report.append("\nTOP 10 RESEARCH PRIORITIES (real-time):")
    for i, (name, info) in enumerate(list(priorities.items())[:10], 1):
        report.append(f"  {i}. [{info['priority_score']:3d}] {name}")
        report.append(f"     Action: {info['action']}")
        report.append(f"     Reason: {info['reason'][:80]}")
    
    report.append("\nBOTTOM 5 (lowest priority — don't research):")
    for i, (name, info) in enumerate(list(priorities.items())[-5:], 1):
        report.append(f"  {i}. [{info['priority_score']:3d}] {name} — {info['action']}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


if __name__ == "__main__":
    print(generate_priority_report())