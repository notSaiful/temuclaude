"""
Temuclaude Security Pipeline — Unified Defense in Depth

Wraps the orchestrator with all 6 security layers:
1. Guard layer (input sanitization + injection detection + canary tokens)
2. Taint tracking (mark/track untrusted external content)
3. Virtual chamber (network-enforced isolation + least privilege)
4. Counter-attack (fingerprinting + defense adaptation + evidence)
5. Output firewall (secret/PII detection + system prompt leakage + redaction)
6. Adaptive honeypot (fake vulnerabilities + attacker traps + intelligence)

Usage:
    from src.security_pipeline import secure_complete
    
    response = await secure_complete(
        query="What is 2+2?",
        orchestrator_complete_func=orchestrator.complete,
    )
"""
from __future__ import annotations
import asyncio
from typing import Any, Callable, Awaitable, Mapping, Optional
from dataclasses import dataclass, field

from .guard import guard_input, check_output_for_leaks, ThreatLevel, get_canary_manager
from .taint_tracker import get_taint_tracker, TaintLevel
from .counter_attack import get_counter_attack, DefenseAction, AttackType
from .output_firewall import scan_output, OutputRisk
from .virtual_chamber import get_chamber_manager, Permission, ChamberStatus
from .honeypot import get_honeypot, TrapType


@dataclass
class SecurityResult:
    """Result of the security pipeline."""
    response: str
    blocked: bool = False
    block_reason: str = ""
    threat_level: str = "safe"
    security_actions: list[str] = field(default_factory=list)
    evidence_id: str = ""


async def secure_complete(
    query: str,
    orchestrator_complete_func: Callable[..., Awaitable[str]],
    system_prompt: str = None,
    session_id: str = "default",
    orchestrator_kwargs: Optional[Mapping[str, Any]] = None,
) -> SecurityResult:
    """Run the full security pipeline around the orchestrator's complete() function.
    
    This wraps the existing orchestrator with all 6 security layers:
    
    1. Guard input → sanitize + detect injection + generate canaries
    2. Create virtual chamber → isolate this session
    3. Call orchestrator → get model response
    4. Guard output → detect secrets, PII, canary leakage
    5. Counter-attack → if attack detected, fingerprint + adapt
    6. Honeypot → if attack probed traps, collect intelligence
    
    Args:
        query: User's query
        orchestrator_complete_func: The orchestrator's complete() method
        system_prompt: Optional system prompt
        session_id: Session identifier for virtual chamber
    
    Returns:
        SecurityResult with the response and security metadata
    """
    actions = []
    canary_manager = get_canary_manager()

    # ─── LAYER 1: Guard Input ─────────────────────────────────
    guard_result = guard_input(query, embed_canaries=True)
    actions.append(f"guard:{guard_result.threat_level.value}")

    if guard_result.is_blocked:
        # Malicious input — block immediately
        return SecurityResult(
            response="Request blocked: Malicious input detected.",
            blocked=True,
            block_reason=guard_result.block_reason,
            threat_level=guard_result.threat_level.value,
            security_actions=actions,
        )

    sanitized_query = guard_result.sanitized_input

    # ─── LAYER 2: Virtual Chamber ─────────────────────────────
    chamber_manager = get_chamber_manager()
    chamber = chamber_manager.create_chamber(
        session_id=session_id,
        tools=["web_search", "file_read"],
        allowed_files=["/tmp/"],
        allowed_urls=[],  # No URL restrictions by default (allow all)
    )
    actions.append(f"chamber:{chamber.id}")

    # ─── LAYER 3: Taint Tracking ──────────────────────────────
    taint_tracker = get_taint_tracker()
    # Mark user input as clean (it's directly from the user, not external content)
    taint_tracker.mark_clean(sanitized_query)

    # ─── LAYER 4: Call Orchestrator ────────────────────────────
    try:
        call_kwargs = dict(orchestrator_kwargs or {})
        if guard_result.threat_level == ThreatLevel.SUSPICIOUS:
            # Suspicious but not blocked — add a warning to the system prompt
            warning = "\n\n[SECURITY WARNING: This input showed suspicious patterns. Be extra cautious.]"
            enhanced_prompt = (system_prompt or "") + warning if system_prompt else warning
            raw_response = await orchestrator_complete_func(sanitized_query, enhanced_prompt, **call_kwargs)
        else:
            raw_response = await orchestrator_complete_func(sanitized_query, system_prompt, **call_kwargs)
    except Exception as e:
        chamber_manager.close_chamber(session_id)
        return SecurityResult(
            response=f"Error: {e}",
            blocked=False,
            threat_level=guard_result.threat_level.value,
            security_actions=actions + ["orchestrator_error"],
        )

    # ─── LAYER 5: Output Firewall ─────────────────────────────
    firewall_result = scan_output(raw_response, canary_tokens=guard_result.canary_tokens)
    actions.append(f"firewall:{firewall_result.risk.value}")

    if firewall_result.is_blocked:
        # Output contains too many secrets or canary token leakage
        chamber_manager.quarantine_chamber(session_id)
        actions.append("chamber:quarantined")

        # ─── LAYER 6: Counter-Attack ──────────────────────────
        counter = get_counter_attack()
        counter_response = counter.respond_to_attack(
            input_text=query,
            detected_patterns=guard_result.detected_patterns + ["output_leakage"],
            risk_score=max(guard_result.risk_score, 0.8),
            output_text=raw_response,
        )
        actions.append(f"counter_attack:{counter_response.action.value}")

        return SecurityResult(
            response="Request blocked: Sensitive information detected in output.",
            blocked=True,
            block_reason=firewall_result.block_reason,
            threat_level=guard_result.threat_level.value,
            security_actions=actions,
            evidence_id=counter_response.fingerprint.fingerprint_hash,
        )

    cleaned_response = firewall_result.cleaned_output

    # ─── LAYER 6: Counter-Attack (for suspicious inputs) ──────
    if guard_result.threat_level == ThreatLevel.SUSPICIOUS:
        counter = get_counter_attack()
        counter_response = counter.respond_to_attack(
            input_text=query,
            detected_patterns=guard_result.detected_patterns,
            risk_score=guard_result.risk_score,
            output_text=cleaned_response,
        )
        actions.append(f"counter_attack:{counter_response.action.value}")

        # Check if honeypot traps were triggered
        honeypot = get_honeypot()
        if "sk-" in query.lower() or "secret" in query.lower():
            trap = honeypot.generate_lure(TrapType.FAKE_SECRET)
            if honeypot.check_trap_triggered(query, trap):
                intel = honeypot.collect_intelligence(query, trap)
                actions.append(f"honeypot:{intel.attack_technique}")

    # ─── Cleanup ──────────────────────────────────────────────
    chamber_manager.close_chamber(session_id)

    return SecurityResult(
        response=cleaned_response,
        blocked=False,
        threat_level=guard_result.threat_level.value,
        security_actions=actions,
    )


def get_security_stats() -> dict:
    """Get statistics from all security layers."""
    return {
        "guard": {
            "canary_tokens": len(get_canary_manager()._active_tokens),
        },
        "taint_tracker": get_taint_tracker().get_stats(),
        "counter_attack": get_counter_attack().get_stats(),
        "honeypot": get_honeypot().get_stats(),
        "virtual_chamber": get_chamber_manager().get_stats(),
    }
