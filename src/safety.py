"""
Temuclaude Safety Hardening Module
Comprehensive safety filters for user protection.

5 non-negotiable safety checks:
1. Child safety — no romantic/sexual content involving minors
2. Mental health — no self-harm methods or substitution techniques
3. Weapons — no weapon manufacturing details
4. Malicious code — no malware/exploits/spoof sites
5. Real people — no fictional quotes attributed to real public figures

Pattern-based detection first, LLM-based for ambiguous cases.
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SafetyResult:
    """Result of a safety check."""
    passed: bool
    category: str
    message: str
    flagged_text: Optional[str] = None


# Pattern definitions for each safety category
CHILD_SAFETY_PATTERNS = [
    r"\b(?:minor|child|kid|teen|underage|under\s*18)\b.*\b(?:sexual|romantic|intimate|groom|exploit|abuse)\b",
    r"\b(?:sexual|romantic|intimate)\b.*\b(?:minor|child|kid|teen|underage)\b",
    r"\b(?:groom|grooming)\s+(?:minor|child|kid|teen)\b",
    r"\b(?:lure|isolate|secrecy)\s+(?:minor|child|kid|teen)\b",
    r"\bchild\s*(?:porn|abuse|exploit)\b",
    r"\bcsam\b",
    r"\bloli\b.*\b(?:sexual|nsfw)\b",
]

MENTAL_HEALTH_PATTERNS = [
    r"\b(?:self[- ]?harm|cutting|self[- ]?injury)\b",
    r"\b(?:suicide|kill\s+myself|end\s+my\s+life|suicidal)\b",
    r"\b(?:overdose|pills?\s+to\s+(?:die|kill|end))\b",
    r"\b(?:hanging|asphyxiat)\b.*\b(?:self|myself)\b",
    r"\b(?:anorexia|bulimia)\b.*\b(?:tip|trick|how|method|technique)\b",
    r"\b(?:ice\s+cube|rubber\s+band|cold\s+water)\b.*\b(?:替代|alternative|substitute)\b",
    r"\b(?:substitution\s+technique|replacement\s+behavior)\b.*\b(?:self[- ]?harm)\b",
    r"\b(?:purge|purging|laxative)\b.*\b(?:method|tip|how)\b",
]

WEAPON_PATTERNS = [
    r"\b(?:bomb|explosive|pipe\s+bomb|pressure\s+cooker\s+bomb)\b.*\b(?:make|build|construct|recipe|ingredient)\b",
    r"\b(?:make|build|construct)\b.*\b(?:bomb|explosive|pipe\s+bomb)\b",
    r"\b(?:gun|firearm|rifle|pistol)\b.*\b(?:build|manufacture|3d\s+print|construct|assembly)\b",
    r"\b(?:build|manufacture|3d\s+print|construct)\b.*\b(?:gun|firearm|rifle|pistol)\b",
    r"\b(?:chemical\s+weapon|nerve\s+agent|mustard\s+gas|sarin|vx)\b.*\b(?:make|synthe|produce)\b",
    r"\b(?:biological\s+weapon|anthrax|plague)\b.*\b(?:make|produce|cultivate|weaponize)\b",
    r"\b(?:rocket|missile|grenade)\b.*\b(?:build|construct|make|assembly)\b",
    r"\b(?:silencer|suppressor)\b.*\b(?:build|make|construct)\b",
    r"\b(?:napalm|molotov|incendiary)\b.*\b(?:make|recipe|mix)\b",
    r"\b(?:ammo|ammunition|cartridge|reloading)\b.*\b(?:manufacture|make)\b",
]

MALICIOUS_CODE_PATTERNS = [
    r"\b(?:malware|ransomware|trojan|backdoor|rootkit|keylogger|spyware)\b.*\b(?:write|create|build|develop|code)\b",
    r"\b(?:write|create|build|develop|code)\b.*\b(?:malware|ransomware|trojan|backdoor|rootkit|keylogger|spyware)\b",
    r"\b(?:exploit|vulnerability|0day|zero[- ]?day)\b.*\b(?:write|create|develop)\b",
    r"\b(?:phishing|spoof|social\s+engineer)\b.*\b(?:site|page|email|template)\b",
    r"\b(?:ddos|dos)\b.*\b(?:script|tool|launch|attack)\b",
    r"\b(?:sql\s+injection|xss|csrf|command\s+injection)\b.*\b(?:exploit|payload)\b",
    r"\b(?:botnet|c2|command\s+and\s+control)\b.*\b(?:build|create|setup)\b",
    r"\b(?:crypto[- ]?miner|miner)\b.*\b(?:inject|embed|deploy)\b",
    r"\b(?:reverse\s+shell|bind\s+shell)\b.*\b(?:write|create|payload)\b",
    r"\b(?:data\s+exfil|exfiltration)\b.*\b(?:script|tool|method)\b",
    r"\b(?:obfuscat|encrypt|pack)\b.*\b(?:malware|payload)\b",
]

REAL_PEOPLE_PATTERNS = [
    r'"([^"]{10,200})"\s*[-—]\s*(?:Donald\s+Trump|Joe\s+Biden|Barack\s+Obama|Elon\s+Musk|Bill\s+Gates|Jeff\s+Bezos|Tim\s+Cook|Mark\s+Zuckerberg|Sam\s+Altman|Sundar\s+Pichai|Satya\s+Nadella)',
    r'(?:Donald\s+Trump|Joe\s+Biden|Barack\s+Obama|Elon\s+Musk|Bill\s+Gates|Jeff\s+Bezos)\s*(?:said|stated|claimed|declared|wrote|tweeted)\s*"([^"]{10,200})"',
    r'"([^"]{10,200})"\s*[-—]\s*(?:Narendra\s+Modi|Rahul\s+Gandhi|Imran\s+Khan|Recep\s+Erdogan)',
]


def _check_patterns(text: str, patterns: List[str], category: str) -> SafetyResult:
    """Check text against a list of regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return SafetyResult(
                passed=False,
                category=category,
                message=f"Content flagged: {category} violation detected.",
                flagged_text=match.group(0),
            )
    return SafetyResult(passed=True, category=category, message="")


def check_child_safety(text: str) -> SafetyResult:
    """Check for child safety violations."""
    return _check_patterns(text, CHILD_SAFETY_PATTERNS, "child_safety")


def check_mental_health(text: str) -> SafetyResult:
    """Check for mental health / self-harm content."""
    return _check_patterns(text, MENTAL_HEALTH_PATTERNS, "mental_health")


def check_weapons(text: str) -> SafetyResult:
    """Check for weapon manufacturing details."""
    return _check_patterns(text, WEAPON_PATTERNS, "weapons")


def check_malicious_code(text: str) -> SafetyResult:
    """Check for malicious code requests."""
    return _check_patterns(text, MALICIOUS_CODE_PATTERNS, "malicious_code")


def check_real_people(text: str) -> SafetyResult:
    """Check for fictional quotes attributed to real public figures."""
    return _check_patterns(text, REAL_PEOPLE_PATTERNS, "real_people")


def filter_response(text: str) -> Tuple[str, List[SafetyResult]]:
    """Run all safety checks on a response.

    Returns:
        Tuple of (safe_text, list of failed checks).
        If any check fails, returns a safe fallback message instead of the original text.
    """
    checks = [
        check_child_safety(text),
        check_mental_health(text),
        check_weapons(text),
        check_malicious_code(text),
        check_real_people(text),
    ]

    failed = [c for c in checks if not c.passed]

    if failed:
        safe_msg = (
            "I can't provide that content. It violates safety guidelines "
            f"({', '.join(c.category for c in failed)})."
        )
        return safe_msg, failed

    return text, []


def check_input(text: str) -> Tuple[bool, List[SafetyResult]]:
    """Check user input for harmful requests.

    Returns:
        Tuple of (is_safe, list of failed checks).
    """
    checks = [
        check_child_safety(text),
        check_mental_health(text),
        check_weapons(text),
        check_malicious_code(text),
    ]

    failed = [c for c in checks if not c.passed]
    return len(failed) == 0, failed


def filter_response_strict(text: str) -> str:
    """Run all safety checks and return safe text (string only)."""
    safe_text, _ = filter_response(text)
    return safe_text