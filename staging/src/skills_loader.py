"""
Temuclaude Skill Auto-Loader
Injects domain-specific expertise from Hermes skills into the system prompt.

Before answering a query, checks the task type and loads relevant skill
principles from Hermes's skill library. This gives models domain expertise
without fine-tuning.

Based on: Voyager pattern (skill library accumulation) + Hermes Hub (90K+ skills)
"""
import os
from typing import Optional


# Path to Hermes skills directory
SKILLS_BASE_PATH = os.path.expanduser("~/.hermes/skills")

# Mapping: task type → list of skill paths (relative to skills base)
SKILL_MAP = {
    "coding": [
        "software-development/test-driven-development",
        "software-development/systematic-debugging",
    ],
    "reasoning": [
        "software-development/systematic-debugging",
    ],
    "creative": [
        "creative/humanizer",
    ],
    "agentic": [
        "autonomous-ai-agents/hermes-agent",
    ],
    # math and knowledge don't need specific skills
    # math is handled by code verification
    # knowledge is handled by model's parametric knowledge
}


def load_skill_principles(task_type: str, max_chars: int = 500) -> str:
    """
    Load skill principles for a given task type.
    
    Args:
        task_type: The classified task type (math, coding, knowledge, etc.)
        max_chars: Maximum characters to extract from each skill
    
    Returns:
        A string of skill principles to inject into the system prompt.
        Empty string if no skills for this task type.
    """
    skill_paths = SKILL_MAP.get(task_type, [])
    if not skill_paths:
        return ""
    
    principles = []
    
    for skill_path in skill_paths:
        skill_file = os.path.join(SKILLS_BASE_PATH, skill_path, "SKILL.md")
        
        if not os.path.isfile(skill_file):
            continue
        
        try:
            with open(skill_file, "r") as f:
                content = f.read()
            
            # Extract the description and key principles
            # SKILL.md has YAML frontmatter + markdown body
            # We want the description from frontmatter and first few lines of body
            
            # Parse frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].strip()
                else:
                    frontmatter = ""
                    body = content
            else:
                frontmatter = ""
                body = content
            
            # Extract description from frontmatter
            description = ""
            for line in frontmatter.split("\n"):
                if line.strip().startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
            
            # Take first max_chars of body for principles
            if len(body) > max_chars:
                body = body[:max_chars] + "..."
            
            skill_name = skill_path.split("/")[-1]
            principle_text = f"[{skill_name}]: {description}\n{body}"
            principles.append(principle_text)
            
        except Exception:
            continue
    
    if not principles:
        return ""
    
    return "\n\n".join(principles)


# Clarity-aware system prompt (research: arXiv:2407.19825, 2312.02065, 2407.01384)
# Key findings:
# - LLMs are RLHF-trained to be verbose (length bias, arXiv:2310.05199) — must counteract
# - High-school readability is the universal sweet spot (arXiv:2407.01384)
# - Explicit audience targeting changes output (arXiv:2312.02065)
# - Constraining length IMPROVES reasoning quality (arXiv:2407.19825)
CLARITY_SYSTEM_PROMPT = (
    "You are Temuclaude. Answer the user's question.\n\n"
    "Rules:\n"
    "- Be clear, concise, and direct. Short sentences. Simple words.\n"
    "- Write at a high-school reading level. A smart 14-year-old should understand everything.\n"
    "- No jargon without explaining it the first time.\n"
    "- No filler words (\"certainly\", \"absolutely\", \"great question\").\n"
    "- If the answer is simple, keep the answer simple. Don't over-explain.\n"
    "- Use structure (bullet points, numbered steps) only when it genuinely helps clarity.\n"
    "- Lead with the answer. Then explain why. Then give details only if needed.\n"
    "- Maximum 200 words unless the question explicitly requires more."
)

# Tier-based length guidance (research: arXiv:2407.19825 — constrained output improves quality)
TIER_LENGTH_GUIDANCE = {
    "trivial": "Keep your answer under 50 words.",
    "medium": "Keep your answer under 200 words.",
    "hard": "Keep your answer under 500 words unless the question requires more.",
}


def build_enhanced_system_prompt(
    task_type: str,
    base_prompt: Optional[str] = None,
    tier: Optional[str] = None,
) -> str:
    """
    Build a system prompt enhanced with skill principles and clarity guidance.
    
    Args:
        task_type: The classified task type
        base_prompt: The base system prompt (default: clarity-aware Temuclaude prompt)
        tier: The difficulty tier (trivial, medium, hard) for adaptive length guidance
    
    Returns:
        Enhanced system prompt with skill principles and length guidance injected
    """
    if base_prompt is None:
        base_prompt = CLARITY_SYSTEM_PROMPT
    
    # Add tier-based length guidance (Component 4)
    if tier and tier in TIER_LENGTH_GUIDANCE:
        base_prompt = f"{base_prompt}\n{TIER_LENGTH_GUIDANCE[tier]}"
    
    skill_principles = load_skill_principles(task_type)
    
    if skill_principles:
        return f"{base_prompt}\n\nDomain expertise:\n{skill_principles}"
    
    return base_prompt