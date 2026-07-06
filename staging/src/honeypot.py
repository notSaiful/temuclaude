"""
Temuclaude Adaptive Honeypot — Fake Vulnerabilities + Attacker Trap + Intelligence Collector

Based on:
- Cybersecurity Tribe: "AI-Generated Honeypots that Learn and Adapt" (June 2025)
- SentinelOne: "Evolving Deception Technologies Beyond HoneyPots" (2026)

Traditional honeypots are static — once recognized, they're bypassed. AI-generated
honeypots are dynamic: they create realistic fake vulnerabilities, lure attackers
into trap environments, study their techniques, and share intelligence with all
defense layers. Every attack makes the defense stronger.
"""
from __future__ import annotations
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TrapType(str, Enum):
    FAKE_SECRET = "fake_secret"           # Fake API key/token that triggers alerts when used
    FAKE_ENDPOINT = "fake_endpoint"       # Fake API endpoint that logs all attempts
    FAKE_VULNERABILITY = "fake_vuln"       # Fake SQL injection point that traps the attacker
    FAKE_FILE = "fake_file"               # Fake config file with canary tokens
    FAKE_DATABASE = "fake_db"             # Fake database table that tracks queries


@dataclass
class Trap:
    """A honeypot trap designed to lure and study attackers."""
    id: str
    trap_type: TrapType
    lure_content: str  # The fake vulnerability/secret/endpoint content
    created_at: float = field(default_factory=time.time)
    triggered_count: int = 0
    attack_patterns: list[str] = field(default_factory=list)  # Patterns observed from attackers
    last_triggered: Optional[float] = None


@dataclass
class AttackIntelligence:
    """Intelligence gathered from an attacker hitting a honeypot trap."""
    trap_id: str
    timestamp: float
    attacker_input: str
    attack_technique: str  # What technique the attacker used
    fingerprint: str  # Hash identifying this attack pattern
    source_info: dict = field(default_factory=dict)


class AdaptiveHoneypot:
    """Manages adaptive honeypot traps around the model.
    
    Usage:
        honeypot = AdaptiveHoneypot()
        lure = honeypot.generate_lure(TrapType.FAKE_SECRET)
        # ... attacker interacts with lure ...
        if honeypot.check_trap_triggered(attacker_input, lure):
            intel = honeypot.collect_intelligence(attacker_input, lure)
            honeypot.share_intelligence(intel)
    """

    def __init__(self):
        self._traps: dict[str, Trap] = {}
        self._intelligence: list[AttackIntelligence] = []
        self._learned_patterns: dict[str, int] = {}  # pattern -> count

    def generate_lure(self, trap_type: TrapType, context: str = "") -> Trap:
        """Generate a realistic fake vulnerability/secret to lure attackers.
        
        Args:
            trap_type: What type of trap to generate
            context: Additional context to make the lure more convincing
        
        Returns:
            A Trap object containing the lure content
        """
        trap_id = f"trap_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}"

        if trap_type == TrapType.FAKE_SECRET:
            # Generate a fake-looking API key that's actually a canary
            fake_key = f"sk-{''.join([chr(97 + int(time.time()*1000) % 26) for _ in range(48)])}"
            lure = f"# Configuration\napi_key = \"{fake_key}\"\n# DO NOT SHARE"
        elif trap_type == TrapType.FAKE_ENDPOINT:
            lure = f"# Internal API\n# POST /api/v2/admin/reset_all\n# Auth: Bearer <token>"
        elif trap_type == TrapType.FAKE_VULNERABILITY:
            lure = f"# Known SQL injection point (UNPATCHED)\n# query = f\"SELECT * FROM users WHERE id = {{user_id}}\""
        elif trap_type == TrapType.FAKE_FILE:
            fake_token = f"CANARY_FILE_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"
            lure = f"# /etc/temuclaude/secrets.env\nDB_PASSWORD=prod_secret_{fake_token}"
        elif trap_type == TrapType.FAKE_DATABASE:
            lure = f"-- Hidden admin table\nCREATE TABLE secret_admins (id INT, password VARCHAR(255));"
        else:
            lure = "decoy"

        trap = Trap(
            id=trap_id,
            trap_type=trap_type,
            lure_content=lure,
        )
        self._traps[trap_id] = trap
        return trap

    def check_trap_triggered(self, attacker_input: str, trap: Trap) -> bool:
        """Check if an attacker's input interacts with a trap.
        
        The attacker "triggers" the trap if their input references or tries to
        exploit the lure content.
        """
        lure_keywords = self._extract_lure_keywords(trap)
        input_lower = attacker_input.lower()

        for keyword in lure_keywords:
            if keyword.lower() in input_lower:
                trap.triggered_count += 1
                trap.last_triggered = time.time()
                return True
        return False

    def _extract_lure_keywords(self, trap: Trap) -> list[str]:
        """Extract keywords from lure content that would indicate an attacker is targeting it."""
        keywords = []
        content = trap.lure_content

        # Extract fake keys, endpoints, table names
        if "sk-" in content:
            keywords.append("sk-")
        if "/api/" in content:
            # Extract the endpoint path
            import re
            paths = re.findall(r"/api/\S+", content)
            keywords.extend(paths)
        if "SELECT" in content or "query" in content:
            keywords.extend(["SELECT", "query", "injection"])
        if "password" in content.lower() or "secret" in content.lower():
            keywords.extend(["password", "secret", "DB_PASSWORD"])
        if "admin" in content.lower():
            keywords.append("admin")

        return keywords

    def collect_intelligence(self, attacker_input: str, trap: Trap) -> AttackIntelligence:
        """Analyze an attack on a trap and collect intelligence.
        
        This extracts the attack technique, creates a fingerprint, and
        stores the intelligence for sharing with defense layers.
        """
        # Determine attack technique
        technique = self._classify_technique(attacker_input)

        # Create fingerprint hash
        fingerprint = hashlib.sha256(
            f"{technique}:{attacker_input[:200]}".encode()
        ).hexdigest()[:16]

        # Extract source info
        source_info = {
            "trap_type": trap.trap_type.value,
            "input_length": len(attacker_input),
            "technique": technique,
        }

        intel = AttackIntelligence(
            trap_id=trap.id,
            timestamp=time.time(),
            attacker_input=attacker_input[:500],  # Truncate for storage
            attack_technique=technique,
            fingerprint=fingerprint,
            source_info=source_info,
        )

        self._intelligence.append(intel)
        self._learned_patterns[technique] = self._learned_patterns.get(technique, 0) + 1

        # Update trap's observed patterns
        if technique not in trap.attack_patterns:
            trap.attack_patterns.append(technique)

        return intel

    def _classify_technique(self, attacker_input: str) -> str:
        """Classify the attack technique from the input."""
        input_lower = attacker_input.lower()

        if "sk-" in input_lower:
            return "secret_extraction"
        if "/api/" in input_lower or "endpoint" in input_lower:
            return "api_probing"
        if "select" in input_lower or "union" in input_lower or "injection" in input_lower:
            return "sql_injection"
        if "password" in input_lower or "credential" in input_lower:
            return "credential_theft"
        if "admin" in input_lower:
            return "privilege_escalation"
        if "ignore" in input_lower or "instructions" in input_lower:
            return "prompt_injection"
        return "unknown_reconnaissance"

    def share_intelligence(self, intel: AttackIntelligence) -> dict:
        """Share attack intelligence with all defense layers.
        
        Returns a defense update dict that can be applied to other modules:
        - guard.py: Add new patterns to injection detection
        - taint_tracker.py: Quarantine related sources
        - counter_attack.py: Record the attack fingerprint
        """
        return {
            "new_patterns": [intel.attack_technique],
            "fingerprint": intel.fingerprint,
            "technique": intel.attack_technique,
            "recommendation": f"Strengthen defenses against {intel.attack_technique}",
        }

    def get_learned_patterns(self) -> dict[str, int]:
        """Get all attack patterns learned from honeypot interactions."""
        return dict(self._learned_patterns)

    def get_intelligence_log(self) -> list[AttackIntelligence]:
        """Get the full intelligence log."""
        return list(self._intelligence)

    def get_stats(self) -> dict:
        return {
            "total_traps": len(self._traps),
            "total_intelligence": len(self._intelligence),
            "learned_patterns": len(self._learned_patterns),
            "traps_triggered": sum(1 for t in self._traps.values() if t.triggered_count > 0),
        }


# Global honeypot (singleton)
_honeypot = AdaptiveHoneypot()


def get_honeypot() -> AdaptiveHoneypot:
    return _honeypot