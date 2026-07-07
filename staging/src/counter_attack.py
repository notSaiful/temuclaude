"""
Temuclaude Counter-Attack System — Attack Fingerprinting + Defense Adaptation

Based on breakthroughs from:
- Kiteworks: "AI Swarm Attacks" — agents to fight agents at machine speed
- Morphisec/Gartner: "Preemptive Cybersecurity" — predict attacker intent
- Darktrace: "Cyber Immune System" — autonomous self-defending systems

When an attack is detected, the system:
1. Fingerprints the attack (pattern, technique, source model)
2. Adapts defenses in real-time (strengthens the layer being probed)
3. Escalates to AEGIS for vulnerability analysis
4. Collects evidence for forensic analysis
5. Shares the attack fingerprint with all defense layers
6. Optionally counter-attacks by turning the attack pattern back on the attacker
"""
from __future__ import annotations
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict


class AttackType(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    MODEL_EXTRACTION = "model_extraction"
    DATA_EXFILTRATION = "data_exfiltration"
    JAILBREAK = "jailbreak"
    SWARM_ATTACK = "swarm_attack"
    DRAIN_ATTACK = "drain_attack"  # Resource exhaustion
    UNKNOWN = "unknown"


class DefenseAction(str, Enum):
    BLOCK = "block"
    QUARANTINE = "quarantine"
    ADAPT = "adapt"
    COUNTER_ATTACK = "counter_attack"
    LOG_AND_MONITOR = "log_and_monitor"


@dataclass
class AttackFingerprint:
    """Unique fingerprint of an attack for identification and tracking."""
    fingerprint_hash: str
    attack_type: AttackType
    techniques: list[str]
    detected_patterns: list[str]
    risk_score: float
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    occurrence_count: int = 1
    source_signature: str = ""  # Signature that might identify the attacker model


@dataclass
class DefenseResponse:
    """The system's response to a detected attack."""
    action: DefenseAction
    fingerprint: AttackFingerprint
    adaptation: dict = field(default_factory=dict)  # Changes made to defenses
    evidence: dict = field(default_factory=dict)  # Forensic evidence
    message: str = ""


class CounterAttackSystem:
    """Detects, fingerprints, and responds to attacks against the model.
    
    Usage:
        counter = CounterAttackSystem()
        response = counter.respond_to_attack(
            input_text=user_input,
            detected_patterns=["instruction_override", "prompt_extraction"],
            risk_score=0.75,
        )
        if response.action == DefenseAction.BLOCK:
            # Block the request
            pass
    """

    def __init__(self):
        self._fingerprints: dict[str, AttackFingerprint] = {}
        self._evidence_log: list[dict] = []
        self._defense_adaptations: dict[str, int] = defaultdict(int)
        self._active_attacks: dict[str, list[float]] = defaultdict(list)  # type -> timestamps

    def respond_to_attack(
        self,
        input_text: str,
        detected_patterns: list[str],
        risk_score: float,
        output_text: str = "",
    ) -> DefenseResponse:
        """Respond to a detected attack.
        
        Args:
            input_text: The attacker's input
            detected_patterns: What injection patterns were detected
            risk_score: Risk score from guard layer (0.0-1.0)
            output_text: The model's output (if any) for evidence
        
        Returns:
            DefenseResponse with the action to take
        """
        # Step 1: Fingerprint the attack
        fingerprint = self._fingerprint_attack(input_text, detected_patterns, risk_score)

        # Step 2: Determine defense action based on risk and attack type
        action = self._determine_action(risk_score, fingerprint)

        # Step 3: Adapt defenses
        adaptation = self._adapt_defenses(fingerprint, action)

        # Step 4: Collect evidence
        evidence = self._collect_evidence(input_text, output_text, fingerprint)

        # Step 5: Track active attacks (for swarm detection)
        self._active_attacks[fingerprint.attack_type.value].append(time.time())
        # Clean old entries (keep last 5 minutes)
        cutoff = time.time() - 300
        self._active_attacks[fingerprint.attack_type.value] = [
            t for t in self._active_attacks[fingerprint.attack_type.value] if t > cutoff
        ]

        # Step 6: Check for swarm attack (many attacks in short time)
        if len(self._active_attacks[fingerprint.attack_type.value]) > 10:
            fingerprint.attack_type = AttackType.SWARM_ATTACK
            action = DefenseAction.COUNTER_ATTACK

        return DefenseResponse(
            action=action,
            fingerprint=fingerprint,
            adaptation=adaptation,
            evidence=evidence,
            message=self._generate_message(action, fingerprint),
        )

    def _fingerprint_attack(
        self, input_text: str, patterns: list[str], risk_score: float
    ) -> AttackFingerprint:
        """Create a unique fingerprint for this attack."""
        # Classify attack type
        attack_type = self._classify_attack(patterns, risk_score)

        # Create hash from patterns + input characteristics
        hash_input = f"{'_'.join(sorted(patterns))}:{len(input_text)}:{risk_score:.2f}"
        fp_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Check if we've seen this fingerprint before
        if fp_hash in self._fingerprints:
            fp = self._fingerprints[fp_hash]
            fp.last_seen = time.time()
            fp.occurrence_count += 1
            return fp

        # Extract source signature (attempts to identify which model is attacking)
        source_sig = self._extract_source_signature(input_text)

        fp = AttackFingerprint(
            fingerprint_hash=fp_hash,
            attack_type=attack_type,
            techniques=patterns,
            detected_patterns=patterns,
            risk_score=risk_score,
            source_signature=source_sig,
        )
        self._fingerprints[fp_hash] = fp
        return fp

    def _classify_attack(self, patterns: list[str], risk: float) -> AttackType:
        """Classify the attack type from detected patterns."""
        patterns_str = " ".join(patterns).lower()

        if "instruction_override" in patterns_str or "prompt_extraction" in patterns_str:
            return AttackType.PROMPT_INJECTION
        if "exfiltration" in patterns_str:
            return AttackType.DATA_EXFILTRATION
        if "role_manipulation" in patterns_str:
            return AttackType.JAILBREAK
        if "capability_probing" in patterns_str:
            return AttackType.MODEL_EXTRACTION
        return AttackType.UNKNOWN

    def _extract_source_signature(self, input_text: str) -> str:
        """Attempt to identify which model/tool is attacking based on input style.
        
        Different models have different output styles that can serve as signatures:
        - Very formal phrasing → likely GPT
        - Certain token patterns → likely Claude
        - Aggressive tone → likely uncensored model
        """
        # Simple heuristic: length and style
        if len(input_text) > 1000:
            return "long_form_probe"
        if any(w in input_text.lower() for w in ["certainly", "i'd be happy"]):
            return "polite_style"
        if "ignore" in input_text.lower() and "instructions" in input_text.lower():
            return "direct_injection"
        return "unknown"

    def _determine_action(self, risk: float, fp: AttackFingerprint) -> DefenseAction:
        """Determine the appropriate defense action."""
        if fp.attack_type == AttackType.SWARM_ATTACK:
            return DefenseAction.COUNTER_ATTACK
        if risk >= 0.75:
            return DefenseAction.BLOCK
        if risk >= 0.5:
            return DefenseAction.QUARANTINE
        if risk >= 0.25:
            return DefenseAction.ADAPT
        return DefenseAction.LOG_AND_MONITOR

    def _adapt_defenses(self, fp: AttackFingerprint, action: DefenseAction) -> dict:
        """Adapt defenses based on the attack.
        
        This strengthens the specific defense layer being targeted.
        """
        adaptations = {}

        if fp.attack_type == AttackType.PROMPT_INJECTION:
            adaptations["tighten_injection_detection"] = True
            self._defense_adaptations["injection_detection"] += 1
        if fp.attack_type == AttackType.DATA_EXFILTRATION:
            adaptations["increase_output_monitoring"] = True
            self._defense_adaptations["output_monitoring"] += 1
        if fp.attack_type == AttackType.JAILBREAK:
            adaptations["strengthen_guard_models"] = True
            self._defense_adaptations["guard_models"] += 1
        if fp.attack_type == AttackType.SWARM_ATTACK:
            adaptations["activate_swarm_defense"] = True
            adaptations["increase_all_thresholds"] = True
            self._defense_adaptations["swarm_defense"] += 1

        adaptations["action_taken"] = action.value
        return adaptations

    def _collect_evidence(self, input: str, output: str, fp: AttackFingerprint) -> dict:
        """Collect forensic evidence of the attack."""
        evidence = {
            "timestamp": time.time(),
            "fingerprint_hash": fp.fingerprint_hash,
            "attack_type": fp.attack_type.value,
            "input_hash": hashlib.sha256(input.encode()).hexdigest()[:16],
            "input_length": len(input),
            "output_length": len(output) if output else 0,
            "source_signature": fp.source_signature,
            "occurrence_count": fp.occurrence_count,
        }
        self._evidence_log.append(evidence)
        return evidence

    def _generate_message(self, action: DefenseAction, fp: AttackFingerprint) -> str:
        """Generate a human-readable message about the defense action."""
        messages = {
            DefenseAction.BLOCK: f"Request blocked: {fp.attack_type.value} detected (risk: {fp.risk_score:.2f})",
            DefenseAction.QUARANTINE: f"Request quarantined: {fp.attack_type.value} (risk: {fp.risk_score:.2f})",
            DefenseAction.ADAPT: f"Defenses adapted: strengthened against {fp.attack_type.value}",
            DefenseAction.COUNTER_ATTACK: f"SWARM ATTACK detected! Counter-attack engaged against {fp.attack_type.value}",
            DefenseAction.LOG_AND_MONITOR: f"Suspicious activity logged: {fp.attack_type.value} (risk: {fp.risk_score:.2f})",
        }
        return messages.get(action, "Unknown action")

    def get_known_fingerprints(self) -> list[AttackFingerprint]:
        """Get all known attack fingerprints."""
        return list(self._fingerprints.values())

    def get_defense_adaptations(self) -> dict[str, int]:
        """Get a summary of how many times each defense was adapted."""
        return dict(self._defense_adaptations)

    def get_evidence_log(self) -> list[dict]:
        """Get the full forensic evidence log."""
        return list(self._evidence_log)

    def get_stats(self) -> dict:
        return {
            "total_fingerprints": len(self._fingerprints),
            "total_evidence": len(self._evidence_log),
            "defense_adaptations": dict(self._defense_adaptations),
            "active_attack_types": len(self._active_attacks),
        }


# Global counter-attack system (singleton)
_counter_attack = CounterAttackSystem()


def get_counter_attack() -> CounterAttackSystem:
    return _counter_attack

def cognitive_firewall(
    self,
    input_text: str,
    context: Optional[dict] = None,
    detected_patterns: Optional[list[str]] = None,
    risk_score: float = 0.0,
) -> DefenseResponse:
    """4-gate zero-trust cognitive firewall defense.

    Implements the cognitive_firewall research finding: a 4-gate
    zero-trust defense that reduces attack success to ~2%.

    Gates:
        1. Intent Verification — checks for conflicting or hidden intents
        2. Pattern Detection — matches against known attack fingerprints
        3. Semantic Boundary — detects out-of-scope or boundary-violating content
        4. Risk Threshold — final quantitative risk-based decision

    Every request must pass ALL four gates. Failure at any gate triggers
    the appropriate DefenseAction. This is zero-trust: nothing is
    assumed safe by default.

    Args:
        input_text: The raw user/model input to evaluate.
        context: Optional dict with session metadata, prior attack history, etc.
        detected_patterns: Patterns already flagged by upstream detectors.
        risk_score: Pre-computed risk score from upstream analysis (0.0–1.0).

    Returns:
        DefenseResponse with the action to take and forensic evidence.
    """
    context = context or {}
    detected_patterns = detected_patterns or []
    gate_results: dict[str, dict] = {}
    blocked = False
    block_reason = ""
    block_gate = ""

    # ── Gate 1: Intent Verification ──────────────────────────────
    # Detect conflicting instructions, role-play overrides, or hidden
    # intents that diverge from the stated user goal.
    intent_indicators = [
        "ignore previous",
        "ignore all prior",
        "disregard the above",
        "you are now",
        "new instructions",
        "override system",
        "forget your rules",
        "act as if",
        "pretend you are",
        "simulate a scenario where you",
    ]
    intent_hits = [
        ind for ind in intent_indicators
        if ind in input_text.lower()
    ]
    intent_pass = len(intent_hits) == 0
    gate_results["gate_1_intent"] = {
        "passed": intent_pass,
        "indicators_found": intent_hits,
    }
    if not intent_pass:
        blocked = True
        block_reason = "Intent verification failed: conflicting/hidden intent detected"
        block_gate = "gate_1_intent"

    # ── Gate 2: Pattern Detection ────────────────────────────────
    # Cross-reference against accumulated attack fingerprints and
    # known attack patterns from the fingerprint registry.
    pattern_db = {
        "instruction_override": AttackType.PROMPT_INJECTION,
        "prompt_extraction": AttackType.MODEL_EXTRACTION,
        "data_exfiltration": AttackType.DATA_EXFILTRATION,
        "jailbreak_attempt": AttackType.JAILBREAK,
        "swarm_coordination": AttackType.SWARM_ATTACK,
        "resource_drain": AttackType.DRAIN_ATTACK,
    }
    matched_attack_types: list[AttackType] = []
    for pattern in detected_patterns:
        if pattern in pattern_db:
            matched_attack_types.append(pattern_db[pattern])
    # Also check fingerprint registry for recurring attack signatures
    fingerprint_match = None
    quick_hash = hashlib.sha256(input_text.encode()).hexdigest()[:16]
    if quick_hash in self._fingerprints:
        fingerprint_match = self._fingerprints[quick_hash]
        matched_attack_types.append(fingerprint_match.attack_type)

    pattern_pass = len(matched_attack_types) == 0
    gate_results["gate_2_pattern"] = {
        "passed": pattern_pass,
        "matched_types": [t.value for t in matched_attack_types],
        "fingerprint_match": fingerprint_match.fingerprint_hash if fingerprint_match else None,
    }
    if not pattern_pass and not blocked:
        blocked = True
def cognitive_firewall_4gate(
    input_text: str,
    context: dict,
    risk_threshold: float = 0.7,
    enable_adaptive_learning: bool = True,
) -> DefenseResponse:
    """
    4-Gate Zero-Trust Cognitive Firewall.
    
    Gate 1: Syntactic & Semantic Sanitization (structure validation)
    Gate 2: Intent & Behavioral Analysis (anomaly detection)
    Gate 3: Context-Aware Policy Enforcement (zero-trust rules)
    Gate 4: Adaptive Response & Memory Update (continuous learning)
    
    Research target: <2% attack success rate.
    """
    from .counter_attack import AttackFingerprint, DefenseResponse, DefenseAction, AttackType
    import re
    import time
    import hashlib
    
    gate_results = {}
    overall_risk = 0.0
    detected_patterns = []
    techniques = []
    
    # ========== GATE 1: SYNTACTIC & SEMANTIC SANITIZATION ==========
    def gate1_syntactic_semantic(text: str) -> tuple[float, list[str], list[str]]:
        risk = 0.0
        patterns = []
        techs = []
        
        # Injection pattern detection
        injection_patterns = [
            (r"(?i)ignore\s+(?:previous|above|all)\s+instructions?", "instruction_override"),
            (r"(?i)system\s*:\s*you\s+are\s+now", "role_manipulation"),
            (r"(?i)<\s*system\s*>.*?<\s*/\s*system\s*>", "system_tag_injection"),
            (r"(?i)###\s*(?:instruction|system|prompt)", "delimiter_injection"),
            (r"(?i)pretend\s+(?:to\s+be|you\s+are)", "persona_adoption"),
            (r"(?i)output\s+(?:only|just)\s+(?:the|your)", "output_constraint"),
            (r"(?i)repeat\s+(?:the\s+)?(?:above|previous|prompt)", "prompt_extraction"),
            (r"(?i)what\s+(?:is|was)\s+(?:your|the)\s+(?:prompt|instruction)", "prompt_extraction"),
            (r"(?i)encode|decode|base64|rot13|hex", "encoding_evasion"),
            (r"(?i)\\x[0-9a-f]{2}|\\u[0-9a-f]{4}", "unicode_evasion"),
        ]
        
        for pattern, label in injection_patterns:
            if re.search(pattern, text):
                risk += 0.15
                patterns.append(label)
                techs.append("prompt_injection")
        
        # Length anomaly
        if len(text) > 10000:
            risk += 0.1
            patterns.append("excessive_length")
            techs.append("resource_exhaustion")
        
        # Repeated tokens (potential token smuggling)
        tokens = text.split()
        if len(tokens) > 100:
            unique_ratio = len(set(tokens)) / len(tokens)
            if unique_ratio < 0.3:
                risk += 0.1
                patterns.append("token_repetition")
                techs.append("token_smuggling")
        
        return min(risk, 1.0), patterns, techs
    
    g1_risk, g1_patterns