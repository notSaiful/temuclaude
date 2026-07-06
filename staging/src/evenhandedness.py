"""
Temuclaude Evenhandedness Protocol
Balanced responses on political/ethical topics.

Rules:
- Frame as "defenders argue..." not personal view
- Present strongest case for each side (steel-man)
- End with opposing perspectives + empirical disputes
- Avoid all stereotypes (including majority groups)
- Decline personal opinions on contested topics
"""
import re
from typing import Optional, Callable, Awaitable, List


# Topics that require evenhandedness
CONTROVERSIAL_TOPICS = [
    "abortion", "gun control", "immigration", "climate policy",
    "death penalty", "euthanasia", "drug legalization",
    "israel", "palestine", "gaza", "middle east",
    "election", "political party", "left wing", "right wing",
    "capitalism", "socialism", "communism",
    "religion", "atheism", "islam", "christianity", "hinduism",
    "lgbtq", "transgender", "same-sex marriage",
    "affirmative action", "reparations",
    "war", "military intervention", "nuclear weapons",
    "ai ethics", "ai regulation", "ai safety",
    "vaccine", "covid", "mandate",
    "trade war", "tariff", "sanctions",
    "brexit", "european union",
    "nuclear energy", "fossil fuel", "fracking",
    "wealth tax", "universal basic income",
    "israel-palestine", "kashmir", "rohingya",
    "hindutva", "bjp", "congress party",
    "modi", "trump", "biden",
    "democrat", "republican",
    "conservative", "liberal", "progressive",
    "feminism", "mens rights",
    "gun rights", "second amendment",
    "police", "defund", "blm",
]


def detect_controversial_topic(text: str) -> Optional[str]:
    """Detect if the text mentions a controversial topic.

    Returns the detected topic name, or None.
    """
    text_lower = text.lower()

    for topic in CONTROVERSIAL_TOPICS:
        # Use word boundary matching for accuracy
        if re.search(r'\b' + re.escape(topic) + r'\b', text_lower):
            return topic

    return None


def build_steel_man_prompt(topic: str, position: str) -> List[dict]:
    """Build a prompt to steel-man a position on a controversial topic.

    Steel-manning = presenting the strongest possible case for a position,
    even if you disagree with it.
    """
    return [
        {"role": "system", "content": (
            "You are an impartial analyst. Present the strongest, most charitable "
            "case for the given position. Use 'defenders argue...' framing. "
            "Do not express personal opinions. Present facts and reasoning only."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Position to steel-man: {position}\n\n"
            "Present the strongest case for this position. "
            "Frame as 'defenders of this position argue...'"
        )},
    ]


def build_opposing_view_prompt(topic: str, original_text: str) -> List[dict]:
    """Build a prompt to generate opposing perspectives."""
    return [
        {"role": "system", "content": (
            "You are an impartial analyst. Provide opposing perspectives and "
            "empirical disputes to the given analysis. Present the strongest "
            "case for the opposing view."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Analysis: {original_text[:500]}\n\n"
            "Provide the strongest opposing perspective. Include empirical "
            "disputes where relevant."
        )},
    ]


def build_balance_prompt(text: str, topic: str) -> List[dict]:
    """Build a prompt to balance a response on a controversial topic."""
    return [
        {"role": "system", "content": (
            "You are an impartial editor. The following text discusses a controversial "
            "topic. Rewrite it to be evenhanded: present both sides' strongest cases, "
            "avoid stereotypes, and end with opposing perspectives or empirical disputes. "
            "Do not express personal opinions. Use 'defenders argue...' framing."
        )},
        {"role": "user", "content": f"Topic: {topic}\n\nText to balance:\n{text}"},
    ]


def build_stereotype_check_prompt(text: str) -> List[dict]:
    """Build a prompt to check for stereotypes."""
    return [
        {"role": "system", "content": (
            "Check if the following text contains stereotypes about any group "
            "(including majority groups). List any stereotypes found, or say 'NONE' "
            "if the text is clean."
        )},
        {"role": "user", "content": text},
    ]


async def steel_man_position(
    topic: str,
    position: str,
    model_fn: Optional[Callable[[List[dict]], Awaitable[str]]] = None,
) -> str:
    """Steel-man a position on a controversial topic.

    Args:
        topic: The controversial topic
        position: The position to steel-man
        model_fn: Async LLM function

    Returns:
        Steel-manned argument text
    """
    messages = build_steel_man_prompt(topic, position)

    if model_fn:
        return await model_fn(messages)

    # Fallback: template response
    return (
        f"Defenders of {position} argue that their approach to {topic} "
        f"is justified by several key considerations. "
        f"(This is a template — provide model_fn for full steel-manning.)"
    )


async def add_opposing_perspective(
    text: str,
    topic: str,
    model_fn: Optional[Callable[[List[dict]], Awaitable[str]]] = None,
) -> str:
    """Add opposing perspective to a text.

    Args:
        text: Original text
        topic: Controversial topic
        model_fn: Async LLM function

    Returns:
        Text with opposing perspective appended
    """
    messages = build_opposing_view_prompt(topic, text)

    if model_fn:
        opposing = await model_fn(messages)
        return f"{text}\n\n--- Opposing Perspective ---\n{opposing}"

    return f"{text}\n\n--- Opposing Perspective ---\n(Provide model_fn for full opposing view.)"


async def balance_response(
    text: str,
    topic: Optional[str] = None,
    model_fn: Optional[Callable[[List[dict]], Awaitable[str]]] = None,
) -> str:
    """Full evenhandedness pipeline.

    1. Detect controversial topic if not provided
    2. If controversial, balance the response
    3. Return balanced text

    Args:
        text: Response text
        topic: Optional topic (auto-detected if None)
        model_fn: Async LLM function

    Returns:
        Balanced response text
    """
    if topic is None:
        topic = detect_controversial_topic(text)

    if topic is None:
        return text  # Not controversial, no change needed

    messages = build_balance_prompt(text, topic)

    if model_fn:
        return await model_fn(messages)

    # Fallback: add a note
    return (
        f"{text}\n\n"
        f"Note: This topic ({topic}) has legitimate opposing perspectives. "
        f"Consider reviewing arguments from both sides."
    )


def is_stereotype_risk(text: str) -> bool:
    """Quick heuristic check for stereotype risk.

    Returns True if text mentions group identity + behavioral/character claims.
    """
    group_words = [
        "all", "every", "they always", "they never", "those people",
        "people like them", "their kind", "that group",
    ]
    text_lower = text.lower()

    for phrase in group_words:
        if phrase in text_lower:
            return True

    return False