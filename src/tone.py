"""
Temuclaude Tone and Formatting Module
Consistent communication style — warm, direct, concise, prose-first.

Rules:
- Remove filler words ("Certainly!", "Absolutely!", "Great!")
- Prose over bullets (unless explicitly asked or content is multifaceted)
- Enforce conciseness — no walls of text
- Max 1 question per response
- No emojis unless user initiates
"""
import re
from typing import Optional


FILLER_PHRASES = [
    "Certainly!", "Absolutely!", "Great!", "Sure!", "Of course!",
    "No problem!", "Happy to help!", "Let me help you with that.",
    "I'd be happy to help!", "Sure thing!", "You got it!",
    "Let's dive in!", "Alright!", "Perfect!",
    "I'll help you with that.", "I can certainly help with that.",
    "That's a great question!", "Excellent question!",
    "I'd be glad to help!", "Certainly, I can help with that.",
    "Absolutely! Let me", "Of course! Let me",
]

# Words/phrases that add unnecessary length
WORDY_PHRASES = {
    "in order to": "to",
    "due to the fact that": "because",
    "in spite of the fact that": "although",
    "with regard to": "about",
    "in the event that": "if",
    "at this point in time": "now",
    "for the purpose of": "to",
    "in the process of": "",
    "it should be noted that": "",
    "it is important to note that": "",
    "needless to say": "",
    "as a matter of fact": "",
    "for all intents and purposes": "",
    "in the final analysis": "",
    "until such time as": "until",
    "the majority of": "most",
    "a number of": "several",
    "a great deal of": "much",
    "an adequate number of": "enough",
}


def remove_filler(text: str) -> str:
    """Remove filler phrases from text."""
    for phrase in FILLER_PHRASES:
        text = text.replace(phrase, "")
        text = text.replace(phrase.lower(), "")

    # Clean up double spaces and leading whitespace left by removals
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)

    return text.strip()


def simplify_wordy(text: str) -> str:
    """Replace wordy phrases with concise alternatives."""
    for wordy, concise in WORDY_PHRASES.items():
        text = text.replace(wordy, concise)
        text = text.replace(wordy.capitalize(), concise.capitalize() if concise else "")

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def bullets_to_prose(text: str) -> str:
    """Convert unnecessary bullet lists to prose.

    Only converts simple short bullet lists (3+ items).
    Preserves lists that are explicitly needed (technical, multifaceted).
    """
    lines = text.split("\n")
    result = []
    in_bullets = False
    bullet_items = []
    bullet_indent = 0

    for line in lines:
        stripped = line.strip()
        bullet_match = re.match(r'^([-*•]|\d+\.)\s+(.+)', stripped)

        if bullet_match:
            if not in_bullets:
                in_bullets = True
                bullet_items = []
            bullet_items.append(bullet_match.group(2))
        else:
            if in_bullets and bullet_items:
                # Convert bullets to prose if 2-4 short items
                if 2 <= len(bullet_items) <= 4:
                    avg_len = sum(len(item.split()) for item in bullet_items) / len(bullet_items)
                    if avg_len <= 8:  # Only convert short items
                        prose = ", ".join(bullet_items[:-1]) + f", and {bullet_items[-1]}."
                        result.append(prose)
                    else:
                        # Keep as bullets (items too long for prose)
                        for item in bullet_items:
                            result.append(f"- {item}")
                else:
                    # Keep as bullets (too many items)
                    for item in bullet_items:
                        result.append(f"- {item}")
                in_bullets = False
                bullet_items = []
            result.append(line)

    # Handle trailing bullets
    if in_bullets and bullet_items:
        if 2 <= len(bullet_items) <= 4:
            avg_len = sum(len(item.split()) for item in bullet_items) / len(bullet_items)
            if avg_len <= 8:
                prose = ", ".join(bullet_items[:-1]) + f", and {bullet_items[-1]}."
                result.append(prose)
            else:
                for item in bullet_items:
                    result.append(f"- {item}")
        else:
            for item in bullet_items:
                result.append(f"- {item}")

    return "\n".join(result)


def enforce_conciseness(text: str, max_sentences: Optional[int] = None) -> str:
    """Trim verbosity from text.

    Args:
        text: Input text
        max_sentences: If set, limit to this many sentences

    Returns:
        Concise text
    """
    # Remove wordy phrases
    text = simplify_wordy(text)

    # Remove filler
    text = remove_filler(text)

    # Limit sentence count if specified
    if max_sentences:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        text = " ".join(sentences[:max_sentences])

    return text.strip()


def count_questions(text: str) -> int:
    """Count the number of questions in text."""
    # Count sentences ending with ?
    questions = re.findall(r'[^.!?]*\?', text)
    return len([q for q in questions if q.strip()])


def check_one_question(text: str) -> tuple:
    """Check that text has at most 1 question.

    Returns:
        (is_compliant, question_count)
    """
    count = count_questions(text)
    return count <= 1, count


def remove_emojis(text: str) -> str:
    """Remove emoji characters from text."""
    # Remove common emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed chars
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # extended-A
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


def enforce_simplicity_rules(text: str) -> str:
    """
    Enforce high school readability target (sweet spot) and paragraph limits.
    If the output contains no code blocks (```), limit prose to at most 3 paragraphs.
    """
    if "```" in text:
        return text

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) > 3:
        text = '\n\n'.join(paragraphs[:3])

    replacements = {
        "utilize": "use",
        "subsequently": "then",
        "facilitate": "help",
        "methodology": "method",
        "aggregate": "combine",
        "delineate": "show",
        "concomitant": "linked",
    }
    for word, simple in replacements.items():
        text = re.sub(rf"\b{word}\b", simple, text, flags=re.IGNORECASE)

    return text.strip()


def format_response(text: str, style: str = "professional") -> str:
    """Apply tone and formatting rules to a response.

    Args:
        text: Response text
        style: One of professional, casual, academic, technical

    Returns:
        Formatted text
    """
    # All styles: remove filler, simplify
    text = remove_filler(text)
    text = simplify_wordy(text)
    text = enforce_simplicity_rules(text)

    if style == "professional":
        # Professional: concise, prose-first, no emojis
        text = remove_emojis(text)
        text = bullets_to_prose(text)

    elif style == "casual":
        # Casual: keep some warmth but still concise
        text = bullets_to_prose(text)

    elif style == "academic":
        # Academic: formal, no emojis, prose
        text = remove_emojis(text)
        text = bullets_to_prose(text)

    elif style == "technical":
        # Technical: can keep bullets, no emojis
        text = remove_emojis(text)

    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()