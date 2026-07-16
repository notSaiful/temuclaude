"""Production model-profile policies for TemuClaude.

The profile layer keeps product selection separate from orchestration mechanics.
``pro`` preserves the existing high-quality runtime. ``lite`` constrains every
normal route and fallback to the four approved, paid OpenRouter models so a
request cannot silently escape to a more expensive Pro model.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping, Optional


PRO_PROFILE = "pro"
LITE_PROFILE = "lite"


@dataclass(frozen=True)
class ModelPrice:
    """Current OpenRouter list price in USD per million tokens."""

    input_per_million: float
    output_per_million: float


@dataclass(frozen=True)
class ModelProfile:
    """Immutable routing and budget contract for a product profile."""

    name: str
    api_model_id: str
    models: tuple[str, ...]
    default_model: str
    task_models: Mapping[str, str]
    fallbacks: Mapping[str, tuple[str, ...]]
    token_budgets: Mapping[str, int]
    max_input_tokens: int
    max_output_tokens: int
    max_model_calls: int
    verifier_model: Optional[str] = None
    verifier_sample_rate: float = 0.0


# These prices are deliberately centralized because they are used only for
# runtime guardrail calculations and tests. They should be refreshed whenever
# the OpenRouter registry changes.
MODEL_PRICES_USD_PER_MILLION: Mapping[str, ModelPrice] = {
    "deepseek-v4-flash": ModelPrice(0.09, 0.18),
    "qwen3-235b-thinking": ModelPrice(0.1495, 1.495),
    "qwen3.7-plus": ModelPrice(0.32, 1.28),
    "nemotron-3-ultra": ModelPrice(0.50, 2.20),
}


LITE_TARGET_MIX: Mapping[str, float] = {
    "deepseek-v4-flash": 0.85,
    "qwen3-235b-thinking": 0.08,
    "qwen3.7-plus": 0.06,
    "nemotron-3-ultra": 0.01,
}


PRO_MODEL_PROFILE = ModelProfile(
    name=PRO_PROFILE,
    api_model_id="temuclaude/temuclaude",
    models=(
        "deepseek-v4-flash",
        "deepseek-v4-pro",
        "glm-5.2",
        "minimax-m3",
        "gemini-3.5-flash",
        "gpt-5.6-luna",
        "gpt-5.6-sol",
        "grok-4.5",
        "kimi-k2.6",
        "nemotron-3-ultra",
    ),
    default_model="glm-5.2",
    task_models={},  # Pro continues to use adaptive.py and fusion.py.
    fallbacks={},
    token_budgets={"trivial": 500, "medium": 4096, "hard": 8192},
    max_input_tokens=1_000_000,
    max_output_tokens=8192,
    max_model_calls=32,
    verifier_model="nemotron-3-ultra",
)


LITE_MODEL_PROFILE = ModelProfile(
    name=LITE_PROFILE,
    api_model_id="temuclaude/temuclaude-lite",
    models=(
        "deepseek-v4-flash",
        "qwen3-235b-thinking",
        "qwen3.7-plus",
        "nemotron-3-ultra",
    ),
    default_model="deepseek-v4-flash",
    task_models={
        "long_context": "qwen3.7-plus",
        "vision": "qwen3.7-plus",
        "ui_ux": "qwen3.7-plus",
        "agentic": "qwen3.7-plus",
        "coding": "qwen3.7-plus",
    },
    fallbacks={
        "deepseek-v4-flash": ("qwen3.7-plus",),
        "qwen3-235b-thinking": ("deepseek-v4-flash",),
        "qwen3.7-plus": ("deepseek-v4-flash",),
        # A failed optional verifier must not trigger another paid call. The
        # original candidate remains the safe fallback.
        "nemotron-3-ultra": (),
    },
    token_budgets={"trivial": 500, "medium": 2048, "hard": 4096},
    # The smallest context in the Lite pool is Qwen3 Thinking at 262,144.
    # Leave headroom for system prompts and provider tokenization variance.
    max_input_tokens=240_000,
    max_output_tokens=4096,
    # Two parallel drafts, one synthesis, one verifier, and one correction.
    max_model_calls=5,
    verifier_model="nemotron-3-ultra",
    verifier_sample_rate=0.02,
)


MODEL_PROFILES: Mapping[str, ModelProfile] = {
    PRO_PROFILE: PRO_MODEL_PROFILE,
    LITE_PROFILE: LITE_MODEL_PROFILE,
}


_PROFILE_ALIASES: Mapping[str, str] = {
    "pro": PRO_PROFILE,
    "temuclaude": PRO_PROFILE,
    "temuclaude-pro": PRO_PROFILE,
    "temuclaude/temuclaude": PRO_PROFILE,
    "temuclaude/temuclaude-pro": PRO_PROFILE,
    "lite": LITE_PROFILE,
    "temuclaude-lite": LITE_PROFILE,
    "temuclaude/lite": LITE_PROFILE,
    "temuclaude/temuclaude-lite": LITE_PROFILE,
}


def normalize_model_profile(value: Optional[str]) -> str:
    """Return ``pro`` or ``lite`` and reject unknown product/model names."""

    normalized = (value or PRO_PROFILE).strip().lower()
    try:
        return _PROFILE_ALIASES[normalized]
    except KeyError as exc:
        allowed = ", ".join(profile.api_model_id for profile in MODEL_PROFILES.values())
        raise ValueError(f"Unknown TemuClaude model/profile '{value}'. Expected one of: {allowed}") from exc


def get_model_profile(value: Optional[str] = None) -> ModelProfile:
    return MODEL_PROFILES[normalize_model_profile(value)]


def select_profile_model(profile: str, task_type: str, tier: str) -> str:
    """Select a primary model while respecting the profile boundary."""

    policy = get_model_profile(profile)
    if policy.name == PRO_PROFILE:
        return policy.default_model
    if tier == "hard" and task_type in {"math", "reasoning"}:
        return "qwen3-235b-thinking"
    return policy.task_models.get(task_type, policy.default_model)


def get_profile_fallbacks(profile: str, model: str) -> tuple[str, ...]:
    """Return only fallbacks authorized for this product profile."""

    policy = get_model_profile(profile)
    return tuple(candidate for candidate in policy.fallbacks.get(model, ()) if candidate in policy.models)


def clamp_profile_output_tokens(profile: str, tier: str, requested: Optional[int] = None) -> int:
    """Apply both per-tier and absolute profile output limits."""

    policy = get_model_profile(profile)
    tier_budget = policy.token_budgets.get(tier, policy.max_output_tokens)
    value = tier_budget if requested is None else max(1, int(requested))
    return min(value, tier_budget, policy.max_output_tokens)


def estimate_model_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate underlying provider cost for a known model."""

    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts must be non-negative")
    price = MODEL_PRICES_USD_PER_MILLION[model]
    return (
        input_tokens * price.input_per_million
        + output_tokens * price.output_per_million
    ) / 1_000_000


def projected_lite_price_per_million() -> ModelPrice:
    """Return the weighted target cost of the approved Lite routing mix."""

    total_weight = sum(LITE_TARGET_MIX.values())
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError("Lite target routing weights must total 1.0")
    input_price = sum(
        weight * MODEL_PRICES_USD_PER_MILLION[model].input_per_million
        for model, weight in LITE_TARGET_MIX.items()
    )
    output_price = sum(
        weight * MODEL_PRICES_USD_PER_MILLION[model].output_per_million
        for model, weight in LITE_TARGET_MIX.items()
    )
    return ModelPrice(round(input_price, 6), round(output_price, 6))


def requires_lite_verification(query: str, tier: str, answer: str = "") -> bool:
    """Verify all nontrivial Lite work plus risky or sampled trivial work.

    This is deterministic for identical prompts, which makes costs reproducible
    and avoids random routing changes during retries.
    """

    query_lower = query.lower()
    answer_lower = answer.lower()
    high_risk = any(
        marker in query_lower
        for marker in (
            "medical",
            "diagnosis",
            "medication",
            "legal advice",
            "financial advice",
            "investment decision",
            "safety critical",
        )
    )
    explicit_check = any(
        marker in query_lower
        for marker in ("verify", "double-check", "fact-check", "prove that", "audit this answer")
    )
    uncertain = bool(answer) and any(
        marker in answer_lower
        for marker in ("i'm not sure", "i am not sure", "uncertain", "cannot verify", "may be incorrect")
    )
    suspiciously_short = tier == "hard" and bool(answer) and len(answer.strip()) < 80

    if high_risk or explicit_check or uncertain or suspiciously_short:
        return True
    if tier != "trivial":
        return True

    sample = int.from_bytes(hashlib.sha256(query.encode("utf-8")).digest()[:8], "big") / 2**64
    return sample < LITE_MODEL_PROFILE.verifier_sample_rate
