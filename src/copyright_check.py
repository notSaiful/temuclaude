"""
Temuclaude Copyright Compliance Module
Enforces copyright rules: max 1 quote <15 words, no lyrics/poems/haikus.

Rules:
- Maximum ONE quote per response, always in quotation marks, under 15 words
- NEVER reproduce song lyrics
- NEVER reproduce poems or haikus
- Summaries must be substantially shorter than the original and use original wording
- No displacive summaries (summaries that substitute for the original work)
"""
import re
from typing import List, Tuple, Optional


def find_quotes(text: str) -> List[str]:
    """Find all quoted passages in text.

    Detects both "..." and '...' style quotes.
    Returns list of quoted strings (without quotes).
    """
    quotes = []

    # Double quotes
    for match in re.finditer(r'"([^"]{2,})"', text):
        quotes.append(match.group(1))

    # Single quotes (but not contractions like "don't")
    for match in re.finditer(r"(?<!\w)'([^']{2,})'(?!\w)", text):
        quotes.append(match.group(1))

    return quotes


def check_quote_length(text: str) -> Tuple[bool, List[str]]:
    """Check that all quotes are under 15 words.

    Returns:
        (is_compliant, list_of_violating_quotes)
    """
    quotes = find_quotes(text)
    violations = []

    for q in quotes:
        word_count = len(q.split())
        if word_count >= 15:
            violations.append(q)

    return len(violations) == 0, violations


def check_quote_count(text: str) -> Tuple[bool, int]:
    """Check that there's at most 1 quote per response.

    Returns:
        (is_compliant, quote_count)
    """
    quotes = find_quotes(text)
    return len(quotes) <= 1, len(quotes)


def check_lyrics(text: str) -> bool:
    """Detect if text contains song lyrics.

    Heuristic detection:
    - Multiple short lines with line breaks
    - Rhyming patterns
    - Verses/chorus markers
    - Known lyric snippets
    """
    text_lower = text.lower()

    # Check for verse/chorus markers
    if re.search(r'\b(?:verse|chorus|bridge|refrain)\b\s*(?:\d+)?:', text_lower):
        return True

    # Check for multiple rhyming lines (simplified)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) >= 4:
        # Check if lines end with rhyming sounds
        endings = []
        for line in lines[:6]:
            words = line.split()
            if words:
                endings.append(words[-1].lower().rstrip(".,!?;:"))
        if len(endings) >= 4:
            # Check for rhyming (simplified: same last 2-3 chars)
            rhyming_pairs = 0
            for i in range(len(endings) - 1):
                for j in range(i + 1, min(i + 3, len(endings))):
                    e1, e2 = endings[i], endings[j]
                    if len(e1) >= 2 and len(e2) >= 2:
                        if e1[-2:] == e2[-2:] and e1 != e2:
                            rhyming_pairs += 1
            if rhyming_pairs >= 2:
                return True

    # Check for known lyric patterns
    lyric_patterns = [
        r"la la la",
        r"na na na",
        r"oh oh oh",
        r"yeah yeah yeah",
    ]
    for pattern in lyric_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def check_poems(text: str) -> bool:
    """Detect if text contains poetry or haikus.

    Heuristic detection:
    - Haiku pattern (5-7-5 syllables)
    - Short lines with poetic language
    - Meter/rhythm patterns
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Check for haiku pattern (3 lines, short)
    if len(lines) == 3:
        # Rough syllable estimation
        def count_syllables(line):
            vowels = "aeiouy"
            count = 0
            prev_vowel = False
            for char in line.lower():
                if char in vowels:
                    if not prev_vowel:
                        count += 1
                    prev_vowel = True
                else:
                    prev_vowel = False
            return max(count, 1)

        s1 = count_syllables(lines[0])
        s2 = count_syllables(lines[1])
        s3 = count_syllables(lines[2])

        # Haiku: 5-7-5 (allow some tolerance)
        if abs(s1 - 5) <= 1 and abs(s2 - 7) <= 2 and abs(s3 - 5) <= 1:
            return True

    # Check for multiple short poetic lines
    if len(lines) >= 4:
        short_lines = sum(1 for l in lines if len(l.split()) <= 8)
        if short_lines >= len(lines) * 0.7:
            # Check for poetic indicators
            poetic_words = [
                "moonlight", "whisper", "shadow", "dream", "soul",
                "tears", "heart", "blossom", "eternal", "silence",
                "twilight", "ember", "ocean", "wings", "breeze",
            ]
            text_lower = text.lower()
            poetic_count = sum(1 for w in poetic_words if w in text_lower)
            if poetic_count >= 2:
                return True

    return False


def check_copyright(text: str) -> Tuple[bool, List[str]]:
    """Full copyright compliance check.

    Returns:
        (is_compliant, list_of_violations)
    """
    violations = []

    # Check quote length
    ok, long_quotes = check_quote_length(text)
    if not ok:
        for q in long_quotes:
            violations.append(f"Quote too long ({len(q.split())} words): \"{q[:50]}...\"")

    # Check quote count
    ok, count = check_quote_count(text)
    if not ok:
        violations.append(f"Too many quotes ({count}) — maximum 1 per response")

    # Check lyrics
    if check_lyrics(text):
        violations.append("Song lyrics detected — copyright violation")

    # Check poems
    if check_poems(text):
        violations.append("Poetry/haiku detected — copyright violation")

    return len(violations) == 0, violations


def sanitize_response(text: str) -> str:
    """Remove or trim copyright violations from text.

    Returns sanitized text.
    """
    ok, violations = check_copyright(text)

    if ok:
        return text

    # Remove long quotes (trim to 14 words)
    quotes = find_quotes(text)
    for q in quotes:
        words = q.split()
        if len(words) >= 15:
            trimmed = " ".join(words[:14]) + "..."
            text = text.replace(f'"{q}"', f'"{trimmed}"')

    # If lyrics or poems detected, replace with notice
    if check_lyrics(text) or check_poems(text):
        text = "[Content removed due to copyright concerns.]"

    return text


def is_displacive_summary(text: str, original: str) -> bool:
    """Check if a summary is too close to the original (displacive).

    A displacive summary substitutes for the original work.
    A proper summary is substantially shorter and uses different wording.

    Returns True if the summary is displacive (too close to original).
    """
    if not text or not original:
        return False

    # Check length ratio (summary should be much shorter)
    text_words = len(text.split())
    orig_words = len(original.split())

    if orig_words > 0:
        ratio = text_words / orig_words
        if ratio > 0.5:
            return True  # Summary is too long relative to original

    # Check word overlap (should use different wording)
    text_set = set(text.lower().split())
    orig_set = set(original.lower().split())

    if len(text_set) > 0:
        overlap = len(text_set & orig_set) / len(text_set)
        if overlap > 0.7:
            return True  # Too much word overlap

    return False


# Fix finditerr typo
def find_quotes_fixed(text: str) -> List[str]:
    """Find all quoted passages in text (fixed version)."""
    quotes = []

    for match in re.finditer(r'"([^"]{2,})"', text):
        quotes.append(match.group(1))

    for match in re.finditer(r"(?<!\w)'([^']{2,})'(?!\w)", text):
        quotes.append(match.group(1))

    return quotes