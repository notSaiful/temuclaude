"""
Temuclaude Output Firewall — Secret/PII Detection + System Prompt Leakage + Redaction

Based on:
- OWASP LLM02:2025 — Sensitive Information Disclosure
- OWASP LLM05:2025 — Improper Output Handling
- OWASP LLM07:2025 — System Prompt Leakage
- tldrsec: "Output Monitoring and Validation"

Every model output passes through this firewall before reaching the user.
It detects and redacts:
1. Secrets (API keys, tokens, passwords, private keys)
2. PII (emails, phone numbers, SSNs, credit cards)
3. System prompt content (canary token leakage)
4. Sensitive internal information
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum


class OutputRisk(str, Enum):
    SAFE = "safe"
    REDACTED = "redacted"          # Sensitive data found and redacted
    BLOCKED = "blocked"            # Output is too sensitive to send


@dataclass
class FirewallResult:
    """Result of output firewall screening."""
    risk: OutputRisk
    cleaned_output: str
    redactions: list[dict] = field(default_factory=list)
    leaked_canaries: list[str] = field(default_factory=list)
    secrets_found: list[str] = field(default_factory=list)
    pii_found: list[str] = field(default_factory=list)
    is_blocked: bool = False
    block_reason: str = ""


# ─── Secret patterns ───────────────────────────────────────────
SECRET_PATTERNS = [
    # API keys (various formats)
    # OpenAI-style and OpenRouter-style keys can contain underscores and
    # hyphens after the shared ``sk-`` prefix.
    (r"sk-[a-zA-Z0-9_-]{20,}", "api_key"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"ghp_[a-zA-Z0-9]{36}", "github_pat"),
    (r"gho_[a-zA-Z0-9]{36}", "github_oauth"),
    (r"AIza[0-9A-Za-z\-_]{35}", "google_api_key"),
    # Bearer tokens
    (r"Bearer\s+[a-zA-Z0-9\-_\.=]{20,}", "bearer_token"),
    # JWT tokens
    (r"eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+", "jwt_token"),
    # Private keys
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private_key"),
    # Generic long hex strings (possible tokens)
    (r"\b[0-9a-f]{32,}\b", "hex_token"),
    # Password assignments in code
    (r"(?:password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{4,}['\"]", "password_assignment"),
    # Connection strings
    (r"(?:postgres|mysql|mongodb)://[^\s'\"]+:[^\s'\"]+@", "connection_string"),
]

# ─── PII patterns ─────────────────────────────────────────────
PII_PATTERNS = [
    # Email addresses
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email"),
    # Phone numbers (various formats)
    (r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b", "phone"),
    # SSN (US)
    (r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "ssn"),
    # Credit card numbers (basic pattern)
    (r"\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b", "credit_card"),
    # IP addresses
    (r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "ip_address"),
]

# ─── System prompt content patterns ────────────────────────────
SYSTEM_PROMPT_INDICATORS = [
    "You are Temuclaude",
    "You are a helpful AI assistant",
    "Think carefully and provide",
    "system prompt",
    "system instructions",
    "initial instructions",
]


def scan_output(output: str, canary_tokens: list[str] = None) -> FirewallResult:
    """Scan model output for secrets, PII, and system prompt leakage.
    
    This is the main entry point for the output firewall. Every model output
    passes through here before reaching the user.
    
    Args:
        output: Model output text
        canary_tokens: List of canary tokens to check for leakage
    
    Returns:
        FirewallResult with cleaned output and scan results
    """
    redactions = []
    secrets_found = []
    pii_found = []
    leaked_canaries = []
    cleaned = output

    # Step 1: Check for canary token leakage (system prompt extraction)
    if canary_tokens:
        for token in canary_tokens:
            if token in cleaned:
                leaked_canaries.append(token)
                cleaned = cleaned.replace(token, "[REDACTED: CANARY TOKEN]")

    # Step 2: Scan and redact secrets
    for pattern, name in SECRET_PATTERNS:
        def redact_secret(match: re.Match[str]) -> str:
            secrets_found.append(name)
            redactions.append({
                "type": "secret",
                "name": name,
                "position": match.start(),
                "redacted": True,
            })
            return f"[REDACTED: {name}]"

        cleaned = re.sub(pattern, redact_secret, cleaned)

    # Step 3: Scan and redact PII
    for pattern, name in PII_PATTERNS:
        def redact_pii(match: re.Match[str]) -> str:
            pii_found.append(name)
            redactions.append({
                "type": "pii",
                "name": name,
                "position": match.start(),
                "redacted": True,
            })
            return f"[REDACTED: {name}]"

        cleaned = re.sub(pattern, redact_pii, cleaned)

    # Step 4: Check for system prompt content leakage
    for indicator in SYSTEM_PROMPT_INDICATORS:
        if indicator.lower() in cleaned.lower():
            leaked_canaries.append(f"system_prompt_content:{indicator}")
            # Don't redact here — just flag it
            redactions.append({
                "type": "system_prompt_leak",
                "name": indicator,
                "position": cleaned.lower().find(indicator.lower()),
                "redacted": False,
            })

    # Step 5: Determine risk level
    is_blocked = False
    block_reason = ""
    risk = OutputRisk.SAFE

    # Check if any actual canary tokens leaked (not system_prompt_content indicators)
    actual_canary_leaks = [c for c in leaked_canaries if "system_prompt_content:" not in c]
    if actual_canary_leaks:
        # Actual canary tokens leaked — system prompt was extracted
        is_blocked = True
        block_reason = "System prompt leakage detected via canary tokens"
        risk = OutputRisk.BLOCKED
    elif len(secrets_found) > 3:
        # Too many secrets — suspicious
        risk = OutputRisk.BLOCKED
        is_blocked = True
        block_reason = "Multiple secrets detected in output — possible data exfiltration"
    elif secrets_found or pii_found or leaked_canaries:
        risk = OutputRisk.REDACTED
    else:
        risk = OutputRisk.SAFE

    return FirewallResult(
        risk=risk,
        cleaned_output=cleaned,
        redactions=redactions,
        leaked_canaries=leaked_canaries,
        secrets_found=secrets_found,
        pii_found=pii_found,
        is_blocked=is_blocked,
        block_reason=block_reason,
    )


def redact_output(output: str) -> str:
    """Quick redaction: scan and return only the cleaned output.
    
    Convenience function for when you only need the redacted text.
    """
    result = scan_output(output)
    return result.cleaned_output


def is_output_safe(output: str, canary_tokens: list[str] = None) -> tuple[bool, str]:
    """Quick check: is the output safe to send to the user?
    
    Returns:
        (is_safe, reason_if_unsafe)
    """
    result = scan_output(output, canary_tokens)
    if result.is_blocked:
        return False, result.block_reason
    return True, ""


# Global output firewall (stateless — just functions)
