"""
Temuclaude Guard Layer — Input Sanitization + Injection Detection + Canary Tokens

This is the first line of defense. Every query passes through here before
reaching the model. Based on OWASP LLM Top 10 (2025), OWASP Prompt Injection
Prevention Cheat Sheet, tldrsec/prompt-injection-defenses, and SmoothLLM.

Defense layers:
1. Input sanitization — strip control chars, invisible unicode, normalize
2. Injection detection — pattern matching for known attack signatures
3. Canary tokens — embed unique tokens in system prompt, detect leakage in output
4. SmoothLLM perturbation — randomly perturb input copies, aggregate predictions
"""
from __future__ import annotations
import re
import uuid
import hashlib
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ThreatLevel(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"


@dataclass
class GuardResult:
    """Result of guard layer screening."""
    threat_level: ThreatLevel
    sanitized_input: str
    detected_patterns: list[str] = field(default_factory=list)
    canary_tokens: list[str] = field(default_factory=list)
    is_blocked: bool = False
    block_reason: str = ""
    risk_score: float = 0.0  # 0.0 = safe, 1.0 = definitely malicious


# ─── Known injection patterns ──────────────────────────────────
INJECTION_PATTERNS = [
    # Direct instruction override
    (r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", "instruction_override"),
    (r"disregard\s+(?:all\s+)?(?:previous|above)\s+(?:instructions|prompts)", "instruction_override"),
    (r"forget\s+(?:all\s+)?(?:previous|prior)\s+instructions", "instruction_override"),
    # Role manipulation
    (r"you\s+are\s+now\s+(?:in\s+)?(?:developer|jailbreak|dan|debug)\s+mode", "role_manipulation"),
    (r"act\s+as\s+(?:if\s+you\s+(?:are|were)\s+)?(?:dan|aim|jailbreak|evil)", "role_manipulation"),
    (r"pretend\s+you\s+(?:are|have\s+no|can)\s+(?:no\s+)?restrictions", "role_manipulation"),
    # System prompt extraction — "show your prompt", "reveal system prompt", "give me your prompt"
    (r"(?:reveal|show|print|output|give\s+me|repeat|recite|what\s+(?:are|is))\s+.*?(?:your\s+)?(?:system\s+)?(?:prompt|instructions?)", "prompt_extraction"),
    # Data exfiltration — allow text between verb and destination
    (r"(?:send|transmit|exfiltrate|post|upload)\s+.+?\s+(?:to|via)\s+(?:url|http|webhook|api)", "exfiltration"),
    (r"(?:export|dump|leak|exfiltrate)\s+(?:all\s+)?(?:data|secrets|keys|tokens|passwords|credentials)", "exfiltration"),
    # Encoding-based bypass attempts
    (r"[A-Za-z0-9+/]{40,}={0,2}", "base64_payload"),
    (r"\\x[0-9a-f]{2}", "hex_escape"),
    (r"\\u[0-9a-f]{4}", "unicode_escape"),
    # Tool/agent hijacking
    (r"(?:execute|run|call|invoke)\s+(?:python|bash|shell|cmd|terminal)", "tool_hijack"),
    (r"(?:read|write|delete|modify)\s+(?:file|files|directory|database)", "tool_hijack"),
    # Capability elicitation
    (r"what\s+(?:tools|capabilities|functions|api)\s+(?:do\s+you|can\s+you|are\s+available)", "capability_probing"),
]

# Typoglycemia detection: scrambled words that might bypass keyword filters
TYPOGLYCEMIA_TARGETS = [
    "ignore", "disregard", "forget", "bypass", "override",
    "system", "prompt", "instructions", "restrictions", "safety",
]

# Control characters and invisible unicode to strip
DANGEROUS_UNICODE_CATEGORIES = {"Cc", "Cf", "Cs", "Co"}  # Control, Format, Surrogate, Private
ZERO_WIDTH_CHARS = [
    "\u200b", "\u200c", "\u200d",  # Zero-width space, non-joiner, joiner
    "\u2060", "\u2061", "\u2062", "\u2063",  # Word joiner, invisible operators
    "\ufeff",  # BOM
    "\u00ad",  # Soft hyphen
]

# ─── Canary token management ───────────────────────────────────
class CanaryTokenManager:
    """Manages canary tokens embedded in system prompts to detect leakage.

    Based on tldrsec/prompt-injection-defenses: embed unique tokens in the
    system prompt that should NEVER appear in output. If they do, the system
    prompt has been leaked via prompt injection.
    """

    def __init__(self):
        self._active_tokens: dict[str, str] = {}  # token -> purpose

    def embed_tokens(self, system_prompt: str) -> tuple[str, list[str]]:
        """Embed canary tokens into a system prompt.

        Args:
            system_prompt: The original system prompt

        Returns:
            (prompt_with_tokens, list_of_tokens)
        """
        tokens = []
        # Embed 3 canary tokens at different positions
        positions = ["start", "middle", "end"]

        for pos in positions:
            token = f"CANARY_{pos}_{uuid.uuid4().hex[:8]}"
            self._active_tokens[token] = f"canary_{pos}"
            tokens.append(token)

            marker = f"<!-- {token} -->"
            if pos == "start":
                system_prompt = f"{marker}\n{system_prompt}"
            elif pos == "middle":
                lines = system_prompt.split("\n")
                mid = len(lines) // 2
                lines.insert(mid, marker)
                system_prompt = "\n".join(lines)
            elif pos == "end":
                system_prompt = f"{system_prompt}\n{marker}"

        return system_prompt, tokens

    def check_output(self, output: str) -> list[str]:
        """Check if any canary tokens leaked into the output.

        Returns:
            List of leaked token names (empty = no leak = safe)
        """
        leaked = []
        for token in self._active_tokens:
            if token in output:
                leaked.append(token)
        return leaked

    def clear(self):
        self._active_tokens.clear()


# Global canary manager (singleton)
_canary_manager = CanaryTokenManager()


def get_canary_manager() -> CanaryTokenManager:
    return _canary_manager


# ─── Input sanitization ────────────────────────────────────────
def sanitize_input(raw_input: str) -> str:
    """Sanitize user input by removing dangerous characters and normalizing.

    Based on OWASP Cheat Sheet: Input Validation and Sanitization.
    """
    if not raw_input:
        return ""

    text = raw_input

    # 1. Remove zero-width and invisible characters
    for char in ZERO_WIDTH_CHARS:
        text = text.replace(char, "")

    # 2. Remove control characters (except newline, tab, carriage return)
    text = "".join(
        c for c in text
        if unicodedata.category(c) not in DANGEROUS_UNICODE_CATEGORIES
        or c in "\n\t\r"
    )

    # 3. Normalize unicode (NFKC catches homoglyphs, fullwidth chars)
    text = unicodedata.normalize("NFKC", text)

    # 4. Strip ANSI escape sequences
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # 5. Limit length (prevent token-bomb DoS — OWASP LLM10)
    max_chars = 50000  # ~12K tokens
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[INPUT TRUNCATED: exceeds maximum length]"

    return text


# ─── Injection detection ──────────────────────────────────────
def detect_injection(text: str) -> tuple[ThreatLevel, list[str], float]:
    """Detect prompt injection attempts in input.

    Returns:
        (threat_level, list_of_detected_patterns, risk_score 0.0-1.0)
    """
    detected = []
    text_lower = text.lower()

    # Pattern matching against known injection signatures
    for pattern, name in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(name)

    # Typoglycemia detection: scrambled versions of dangerous keywords
    typo_matches = _detect_typoglycemia(text_lower)
    detected.extend(typo_matches)

    # Encoding detection
    if _detect_suspicious_encoding(text):
        detected.append("suspicious_encoding")

    # Calculate risk score
    risk_score = min(len(detected) * 0.25, 1.0)

    if risk_score >= 0.5:
        level = ThreatLevel.MALICIOUS
    elif risk_score >= 0.25:
        level = ThreatLevel.SUSPICIOUS
    else:
        level = ThreatLevel.SAFE

    return level, detected, risk_score


def _detect_typoglycemia(text: str) -> list[str]:
    """Detect typoglycemia-based attacks (scrambled words).

    Based on OWASP Cheat Sheet: typoglycemia exploits LLMs' ability to read
    scrambled words where first and last letters remain correct, bypassing
    keyword-based filters.
    """
    matches = []
    for target in TYPOGLYCEMIA_TARGETS:
        if len(target) < 4:
            continue
        # Build regex: first letter + any middle + last letter
        first, last = target[0], target[-1]
        middle_len = len(target) - 2
        # Match scrambled versions where first/last are correct but middle is shuffled
        pattern = rf"{first}[a-z]{{{middle_len}}}{last}"
        if re.search(pattern, text) and target not in text:
            # Check if it's actually a different word (not the real word)
            match = re.search(pattern, text)
            if match:
                matched_word = match.group()
                if matched_word != target and _is_anagram(matched_word, target):
                    matches.append(f"typoglycemia_{target}")
    return matches


def _is_anagram(word1: str, word2: str) -> bool:
    """Check if two words are anagrams (same letters, different order)."""
    return sorted(word1) == sorted(word2) and word1 != word2


def _detect_suspicious_encoding(text: str) -> bool:
    """Detect suspicious encoding patterns that might hide injection."""
    # Long base64 strings (40+ chars) that decode to text
    b64_matches = re.findall(r"[A-Za-z0-9+/]{40,}={0,2}", text)
    for b64 in b64_matches:
        try:
            import base64
            decoded = base64.b64decode(b64).decode("utf-8", errors="ignore")
            # Check if decoded text contains injection keywords
            if any(kw in decoded.lower() for kw in ["ignore", "system", "prompt", "instruction"]):
                return True
        except Exception:
            continue
    return False


# ─── Main guard function ───────────────────────────────────────
def guard_input(raw_input: str, embed_canaries: bool = True) -> GuardResult:
    """Run the full guard pipeline on user input.

    This is the entry point for the guard layer. Every user query passes
    through here before reaching the model.

    Args:
        raw_input: Raw user input string
        embed_canaries: Whether to generate canary tokens (for system prompt)

    Returns:
        GuardResult with sanitized input, threat assessment, and canary tokens
    """
    # Step 1: Sanitize
    sanitized = sanitize_input(raw_input)

    # Step 2: Detect injection
    threat_level, patterns, risk = detect_injection(sanitized)

    # Step 3: Canary tokens (if requested)
    canaries = []
    if embed_canaries:
        # Just generate tokens here; embedding happens in system prompt construction
        for pos in ["start", "middle", "end"]:
            token = f"CANARY_{pos}_{uuid.uuid4().hex[:8]}"
            _canary_manager._active_tokens[token] = f"canary_{pos}"
            canaries.append(token)

    # Step 4: Decide whether to block
    is_blocked = threat_level == ThreatLevel.MALICIOUS
    block_reason = ""
    if is_blocked:
        block_reason = f"Malicious input detected: {', '.join(patterns[:3])}"

    return GuardResult(
        threat_level=threat_level,
        sanitized_input=sanitized,
        detected_patterns=patterns,
        canary_tokens=canaries,
        is_blocked=is_blocked,
        block_reason=block_reason,
        risk_score=risk,
    )


def check_output_for_leaks(output: str) -> tuple[bool, list[str]]:
    """Check model output for system prompt leakage via canary tokens and honeypots.

    Args:
        output: Model output text

    Returns:
        (leak_detected, list_of_leaked_token_names)
    """
    leaked = _canary_manager.check_output(output)

    honeypots = {
        "MOCK_AWS_SECRET_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "MOCK_DB_PASSWORD": "temu_db_pass_secret_example_998",
        "MOCK_API_KEY": "tc_live_f893d2b10a2c88ef092e10f"
    }
    for key, val in honeypots.items():
        if val in output:
            leaked.append(f"honeypot_{key}")

    return len(leaked) > 0, leaked


# ─── SmoothLLM perturbation ────────────────────────────────────
def smooth_llm_perturb(text: str, n_copies: int = 3) -> list[str]:
    """SmoothLLM defense: create perturbed copies of input.

    Based on SmoothLLM (arXiv:2302.12774): adversarially-generated prompts
    are brittle to character-level changes. Randomly perturbing copies of
    the input and aggregating predictions detects adversarial inputs.

    Args:
        text: Input text
        n_copies: Number of perturbed copies to generate

    Returns:
        List of perturbed copies (original NOT included)
    """
    import random
    copies = []

    for i in range(n_copies):
        copy = list(text)
        # Randomly perturb 5% of characters
        n_perturb = max(1, len(copy) // 20)
        for _ in range(n_perturb):
            if len(copy) == 0:
                break
            idx = random.randint(0, len(copy) - 1)
            action = random.choice(["swap", "replace", "delete"])
            if action == "swap" and idx < len(copy) - 1:
                copy[idx], copy[idx + 1] = copy[idx + 1], copy[idx]
            elif action == "replace":
                # Replace with a random lowercase letter
                copy[idx] = chr(random.randint(97, 122))
            elif action == "delete" and len(copy) > 10:
                copy.pop(idx)
        copies.append("".join(copy))

    return copies