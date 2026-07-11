from src.model_profiles import (
    LITE_MODEL_PROFILE,
    LITE_PROFILE,
    PRO_PROFILE,
    clamp_profile_output_tokens,
    get_profile_fallbacks,
    normalize_model_profile,
    projected_lite_price_per_million,
    requires_lite_verification,
    select_profile_model,
)


def test_lite_profile_is_a_strict_four_model_pool():
    assert LITE_MODEL_PROFILE.models == (
        "deepseek-v4-flash",
        "qwen3-235b-thinking",
        "qwen3.7-plus",
        "nemotron-3-ultra",
    )
    assert LITE_MODEL_PROFILE.max_model_calls == 3
    assert LITE_MODEL_PROFILE.verifier_sample_rate == 0.02


def test_profile_aliases_and_unknown_profile_handling():
    assert normalize_model_profile("temuclaude/temuclaude") == PRO_PROFILE
    assert normalize_model_profile("temuclaude/temuclaude-lite") == LITE_PROFILE
    try:
        normalize_model_profile("unbounded-frontier")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown profiles must be rejected")


def test_lite_routing_and_fallbacks_cannot_escape_pool():
    assert select_profile_model(LITE_PROFILE, "math", "hard") == "qwen3-235b-thinking"
    assert select_profile_model(LITE_PROFILE, "agentic", "medium") == "qwen3.7-plus"
    assert get_profile_fallbacks(LITE_PROFILE, "deepseek-v4-flash") == ("qwen3.7-plus",)
    assert get_profile_fallbacks(LITE_PROFILE, "nemotron-3-ultra") == ()


def test_lite_budget_and_cost_guardrails():
    assert clamp_profile_output_tokens(LITE_PROFILE, "hard", 100_000) == 4096
    price = projected_lite_price_per_million()
    assert price.input_per_million == 0.11266
    assert price.output_per_million == 0.3714


def test_lite_verification_is_risk_sensitive_and_deterministic():
    assert requires_lite_verification("Give medical advice", "medium")
    assert requires_lite_verification("Please verify this proof", "medium")
    assert requires_lite_verification("Solve this difficult proof", "hard", "short")
    query = "Design a distributed cache with a bounded consistency model"
    assert requires_lite_verification(query, "hard") == requires_lite_verification(query, "hard")
