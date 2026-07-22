"""
TemuClaude — Modal Deployment
8-Model Multi-Model AI Orchestration (OpenAI-compatible API)
Quality-first Modal implementation of the documented TemuClaude Pro pipeline.
"""
import os
import json
import re
import time
import asyncio
import hashlib
import logging
import uuid
from datetime import date
from typing import Optional

import modal

app = modal.App("temuclaude-prod")
logger = logging.getLogger(__name__)

# The web gateway allows 115 seconds for Modal and the Modal function itself
# allows 120.  Keep a bounded window for one reliable single-model rescue
# rather than racing it against every normal orchestration request.
ORCHESTRATION_DEADLINE_SECONDS = 85
FALLBACK_DEADLINE_SECONDS = 25
# A single slow upstream must never consume the entire request budget.  These
# limits leave enough room for synthesis, verification, and the final rescue.
PANEL_ROLE_TIMEOUT_SECONDS = 30
PANEL_SYNTHESIS_TIMEOUT_SECONDS = 25
QUALITY_QA_TIMEOUT_SECONDS = 12
QUALITY_REPAIR_TIMEOUT_SECONDS = 12
CODE_ARTIFACT_TIMEOUT_SECONDS = 35

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("httpx==0.28.1", "fastapi==0.115.6")
)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PLAN_MONTHLY_LIMITS = {
    "developer": 50000,
    "pro": 500000,
    # Max is a paid API plan (see website/lib/plans.ts).  Keeping this list
    # aligned prevents valid Max keys from being rejected at the Modal hop.
    "max": 1000000,
    "enterprise": -1,
}

# ── Quality-first Pro model pool ───────────────────────────────
# Keep these roles aligned with README.md and the public model documentation.
M_GLM = "z-ai/glm-5.2"
M_DEEPSEEK = "deepseek/deepseek-v4-pro"
M_GEMINI = "google/gemini-3.5-flash"
M_KIMI = "moonshotai/kimi-k3"
M_KIMI_FRONTIER = "~moonshotai/kimi-latest"
M_MINIMAX = "minimax/minimax-m3"
M_LUNA = "openai/gpt-5.6-luna"
M_GROK = "x-ai/grok-4.5"
M_NEMOTRON = "nvidia/nemotron-3-ultra-550b-a55b"
REQUIRED_QUALITY_MODELS = frozenset((
    M_GLM, M_DEEPSEEK, M_KIMI, M_MINIMAX, M_GEMINI,
    M_LUNA, M_KIMI_FRONTIER, M_GROK, M_NEMOTRON,
))


class Result:
    __slots__ = ("success", "content", "tokens")
    def __init__(self, success: bool, content: str, tokens: int):
        self.success = success
        self.content = content
        self.tokens = tokens


def _supabase_headers() -> Optional[dict]:
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SERVICE_KEY")
    )
    if not key:
        return None
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _supabase_url() -> str:
    return (os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "").rstrip("/")


async def validate_customer_api_key(client, raw_key: str) -> Optional[dict]:
    """Validate a customer tmc_ key against Supabase and return the app user."""
    if not raw_key.startswith("tmc_"):
        return None

    base = _supabase_url()
    headers = _supabase_headers()
    if not base or not headers:
        return None

    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    key_resp = await client.get(
        f"{base}/rest/v1/temuclaude_api_keys",
        headers=headers,
        params={"key_hash": f"eq.{key_hash}", "select": "id,user_id", "limit": "1"},
    )
    if key_resp.status_code != 200:
        return None
    rows = key_resp.json()
    if not rows:
        return None

    key_record = rows[0]
    await client.patch(
        f"{base}/rest/v1/temuclaude_api_keys",
        headers={**headers, "Prefer": "return=minimal"},
        params={"id": f"eq.{key_record['id']}"},
        json={"last_used": int(time.time())},
    )

    user_resp = await client.get(
        f"{base}/rest/v1/temuclaude_users",
        headers=headers,
        params={"id": f"eq.{key_record['user_id']}", "select": "id,email,plan", "limit": "1"},
    )
    if user_resp.status_code != 200:
        return None
    users = user_resp.json()
    return users[0] if users else None


async def get_monthly_usage(client, user_id: str) -> int:
    base = _supabase_url()
    headers = _supabase_headers()
    if not base or not headers:
        return 0

    month_start = date.today().replace(day=1).isoformat()
    resp = await client.get(
        f"{base}/rest/v1/temuclaude_usage",
        headers=headers,
        params={
            "user_id": f"eq.{user_id}",
            "query_date": f"gte.{month_start}",
            "select": "query_count",
        },
    )
    if resp.status_code != 200:
        return 0
    return sum(int(row.get("query_count") or 0) for row in resp.json())


async def increment_customer_usage(client, user_id: str, prompt_tokens: int, completion_tokens: int) -> None:
    base = _supabase_url()
    headers = _supabase_headers()
    if not base or not headers:
        return

    today = date.today().isoformat()
    usage_resp = await client.get(
        f"{base}/rest/v1/temuclaude_usage",
        headers=headers,
        params={
            "user_id": f"eq.{user_id}",
            "query_date": f"eq.{today}",
            "select": "query_count,input_tokens,output_tokens",
            "limit": "1",
        },
    )
    current = usage_resp.json()[0] if usage_resp.status_code == 200 and usage_resp.json() else {}
    payload = {
        "user_id": user_id,
        "query_date": today,
        "query_count": int(current.get("query_count") or 0) + 1,
        "input_tokens": int(current.get("input_tokens") or 0) + prompt_tokens,
        "output_tokens": int(current.get("output_tokens") or 0) + completion_tokens,
    }
    await client.post(
        f"{base}/rest/v1/temuclaude_usage",
        headers={**headers, "Prefer": "resolution=merge-duplicates,return=minimal"},
        params={"on_conflict": "user_id,query_date"},
        json=payload,
    )


async def call_model(client, model: str, messages: list, temp: float = 0.6, max_tok: int = 4096) -> Result:
    """Call one exact model, retrying through another OpenRouter provider if needed.

    A role is never silently substituted with a different model. Both attempts
    preserve the model ID while OpenRouter selects an available provider.
    """
    try:
        # Prepend English system prompt if user didn't provide one
        msgs = messages
        if not any(m.get("role") == "system" for m in messages):
            msgs = [{"role": "system", "content": "You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct."}] + messages
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        for attempt in range(2):
            # Some valid role models reject OpenRouter's optional precision
            # filters with a 404. Keep provider fallback enabled, but avoid
            # constraining the provider to a parameter set it cannot serve.
            provider = {"allow_fallbacks": True, "sort": "throughput"}
            r = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json={
                    "model": model,
                    "messages": msgs,
                    "temperature": temp,
                    "max_tokens": max_tok,
                    "provider": provider,
                },
                # Two bounded exact-model attempts fit inside the 30-second
                # panel role deadline, leaving time for synthesis and QA.
                timeout=12,
            )
            if r.status_code != 200:
                logger.warning("OpenRouter request failed for %s with HTTP %s (attempt %s)", model, r.status_code, attempt + 1)
                continue
            d = r.json()
            msg = d.get("choices", [{}])[0].get("message", {})
            c = msg.get("content") or msg.get("reasoning") or ""
            if not c:
                rd = msg.get("reasoning_details")
                if isinstance(rd, list):
                    c = "".join(x.get("text", "") for x in rd if isinstance(x, dict))
            c = (c or "").strip()
            if c:
                return Result(True, c, d.get("usage", {}).get("total_tokens", 0))
            logger.warning("OpenRouter returned empty content for %s (attempt %s)", model, attempt + 1)
        return Result(False, "", 0)
    except Exception as exc:
        logger.warning("OpenRouter request failed for %s: %s", model, type(exc).__name__)
        return Result(False, "", 0)


def has_usable_content(result: Optional[dict]) -> bool:
    """Only emit completions that contain a non-empty assistant response."""
    return bool(isinstance(result, dict) and isinstance(result.get("content"), str) and result["content"].strip())


def has_complete_quality_panel(result: Optional[dict]) -> bool:
    """A quality response is valid only after every required role completed."""
    if not has_usable_content(result):
        return False
    completed = result.get("completed_models") if isinstance(result, dict) else None
    return isinstance(completed, list) and REQUIRED_QUALITY_MODELS.issubset(set(completed))


async def complete_with_rescue(client, messages: list, temp: float, max_tok: int) -> dict:
    """Run the required full panel and fail closed if it cannot complete."""
    try:
        result = await asyncio.wait_for(
            orchestrate(client, messages, temp, max_tok),
            timeout=ORCHESTRATION_DEADLINE_SECONDS,
        )
        if has_complete_quality_panel(result):
            return result
        logger.warning("Modal orchestration was incomplete; refusing a partial-panel response")
        return result
    except asyncio.TimeoutError:
        logger.warning("Modal orchestration exceeded %ss; refusing a partial-panel response", ORCHESTRATION_DEADLINE_SECONDS)
    except Exception:
        logger.exception("Modal orchestration failed; refusing a partial-panel response")
    return {
        "content": "",
        "tokens": 0,
        "tier": "full-panel-unavailable",
        "time": int(ORCHESTRATION_DEADLINE_SECONDS * 1000),
        "requested_models": list(REQUIRED_QUALITY_MODELS),
        "completed_models": [],
    }


def classify(text: str) -> str:
    """Difficulty Classifier — heuristic, no API call.
    Production code generation is a hard artifact task and receives the full
    documented Pro panel, synthesis, QA, and repair path."""
    l = text.lower()
    wc = len(text.split())
    s = 0
    if wc > 100:
        s += 4
    elif wc > 50:
        s += 2
    elif wc > 20:
        s += 1
    if re.search(r'\b(solve|calculate|derivative|integral|equation|prove|theorem|factor|simplify|evaluate|compute|matrix|probability|limit|optimi[sz]e)\b', l, re.I):
        s += 3
    if len(re.findall(r'[+\-*/^=<>]', text)) > 3:
        s += 2
    if re.search(r'\b(because|therefore|if.*then|contradiction|inference|deduce|imply|assume|prove that|show that|explain why|reason)\b', l, re.I):
        s += 2
    if re.search(r'\b(then|after|next|finally|step by step|how long|how many|show your work)\b', l, re.I):
        s += 2
    if len(re.findall(r'[;,.]', text)) > 3:
        s += 1
    if re.search(r'\b(if|when|where|given|assuming|suppose)\b', l, re.I):
        s += 1

    # Code generation detection — artifact quality benefits from independent
    # implementation, UI, product, and repair reviewers; do not collapse it
    # into a single draft merely because it contains code-related keywords.
    is_code_gen = bool(re.search(r'\b(build|create|generate|write|make|develop|implement|code|html|css|javascript|python|function|class|component|game|website|webpage|app|script|program|landing page|dashboard)\b', l, re.I)) and \
                  bool(re.search(r'\b(html|css|js|javascript|python|code|function|component|page|game|app|script|file|complete)\b', l, re.I))
    if is_code_gen:
        return "hard"

    if re.search(r'\b(function|code|debug|program|algorithm|python|javascript|implement|write.*code|compile|runtime|complexity|recursive|sort|search)\b', l, re.I):
        s += 3

    if s >= 7:
        return "hard"
    if s >= 3:
        return "medium"
    return "trivial"


def is_math(text: str) -> bool:
    return bool(re.search(r'\b(solve|calculate|derivative|integral|equation|prove|theorem|sum|product|factor|simplify|evaluate|compute|find.*value|matrix|probability|limit|optimi[sz]e)\b', text, re.I)) or \
           (bool(re.search(r'\d', text)) and bool(re.search(r'[+\-*/^=]', text)))


def is_creative(text: str) -> bool:
    return bool(re.search(r'\b(write|story|poem|creative|imagine|describe|narrative|character|dialogue|screenplay|lyrics|essay|blog|article)\b', text, re.I))


def is_multimodal(text: str) -> bool:
    return bool(re.search(r'\b(image|picture|photo|video|visual|diagram|chart|screenshot|see|look at|describe.*image)\b', text, re.I))


async def self_consistency(client, q: str, max_tok: int) -> tuple:
    """3 samples at temp 0.7, majority vote."""
    results = await asyncio.gather(
        call_model(client, M_DEEPSEEK, [{"role": "user", "content": q}], 0.7, max_tok),
        call_model(client, M_DEEPSEEK, [{"role": "user", "content": q}], 0.7, max_tok),
        call_model(client, M_DEEPSEEK, [{"role": "user", "content": q}], 0.7, max_tok),
    )
    samples = [r.content.strip() for r in results if r.success and r.content]
    tokens = sum(r.tokens for r in results)
    if not samples:
        return ("", tokens)

    def extract(t: str) -> str:
        boxed = re.search(r'\\boxed\{([^}]+)\}', t)
        if boxed:
            return boxed.group(1).strip()
        lines = [x for x in t.split('\n') if x.strip()]
        last = lines[-1].strip() if lines else ""
        if len(last) < 50:
            return last
        m = re.search(r'(?:answer is|final answer is|=|equals|result is|x\s*=)\s*[:\s]*([^\n.]+)', t, re.I)
        return m.group(1).strip() if m else last

    finals = [extract(s) for s in samples]
    counts: dict = {}
    for a in finals:
        counts[a] = counts.get(a, 0) + 1

    best, best_count = samples[0], 0
    for i, f in enumerate(finals):
        if counts[f] > best_count:
            best_count = counts[f]
            best = samples[i]
    return (best, tokens)


async def aggregate(client, q: str, responses: list, max_tok: int) -> Result:
    text = "\n\n---\n\n".join(f"{r['name']}: {r['content']}" for r in responses)
    return await call_model(client, M_GLM, [
        {"role": "system", "content": """You are an expert answer synthesizer. Analyze the responses for:
1. CONSENSUS — what most agree on (likely correct)
2. CONTRADICTIONS — where they disagree, determine which is correct
3. BEST INSIGHTS — extract unique points from each
4. ERRORS — fix any mistakes

Provide ONE definitive answer. Do NOT mention the analysis. Output ONLY the final answer."""},
        {"role": "user", "content": f"Question: {q}\n\nResponses:\n{text}\n\nProvide the definitive answer:"},
    ], 0.3, max_tok)


async def qa_gate(client, q: str, a: str) -> tuple:
    """5-rubric score by Nemotron (FREE, independent judge)."""
    r = await call_model(client, M_NEMOTRON, [
        {"role": "system", "content": """Score this answer on 5 rubrics (1-10 each):
LC — Logical Coherence
FC — Factual Correctness
CM — Completeness
GA — Goal Alignment
CL — Clarity

Output:
AVERAGE: X
FEEDBACK: <one sentence>"""},
        {"role": "user", "content": f"Question: {q}\nAnswer: {a}\n\nScore:"},
    ], 0.0, 500)

    avg = re.search(r'AVERAGE:\s*(\d+(?:\.\d+)?)', r.content or "", re.I)
    fb = re.search(r'FEEDBACK:\s*(.+)', r.content or "", re.I)
    score = float(avg.group(1)) if avg else 0
    if not score and r.content:
        rubric_scores = re.findall(r'(?:LC|FC|CM|GA|CL):\s*(\d+)', r.content, re.I)
        if len(rubric_scores) >= 3:
            nums = [int(s) for s in rubric_scores if int(s) > 0]
            if nums:
                score = sum(nums) / len(nums)
    if not score:
        score = 5  # Default to 5 (triggers reflexion) not 7 (skips it)
    feedback = fb.group(1).strip() if fb else "Improve completeness and clarity"
    return (score, r.tokens, feedback, r.success)


async def reflexion(client, q: str, prev_answer: str, feedback: str, max_tok: int) -> Result:
    return await call_model(client, M_DEEPSEEK, [
        {"role": "system", "content": "You are answering a question. A previous attempt received feedback. Use it to improve. Output ONLY the improved answer."},
        {"role": "user", "content": f"Question: {q}\n\nPrevious answer: {prev_answer}\n\nFeedback: {feedback}\n\nImproved answer:"},
    ], 0.4, max_tok)


def is_code_artifact_request(text: str) -> bool:
    """Whether the caller expects a runnable or inspectable code artifact."""
    l = text.lower()
    asks_to_build = bool(re.search(
        r'\b(build|create|generate|write|make|develop|implement|code)\b', l
    ))
    artifact_target = bool(re.search(
        r'\b(game|website|webpage|web page|site|web app|landing page|dashboard|html|css|javascript|app|component|file)\b', l
    ))
    return asks_to_build and artifact_target


async def generate_code_artifact(client, q: str, panel_synthesis: str, max_tok: int) -> Result:
    """Turn the full panel's reviewed design into a complete, previewable artifact.

    Kimi is deliberately the delivery model here: the panel has already used
    every Pro role for planning and criticism, while this pass needs one model
    to preserve a coherent runnable implementation rather than blend snippets
    from reviewers into an incomplete response.
    """
    return await call_model(client, M_KIMI, [
        {"role": "system", "content": """You are TemuClaude's final implementation engineer.
Return ONLY the complete requested artifact, with no explanation before or after it.
For a webpage or browser game, return one self-contained, runnable HTML document
beginning with <!doctype html> and include its CSS and JavaScript inline. It must
work without build tools, external packages, or network access. Implement the
requested interactions, responsive layout, keyboard/touch accessibility, and a
clear restart or reset path for games. Never return a plan, pseudo-code, partial
snippet, markdown prose, or an ellipsis."""},
        {"role": "user", "content": f"""Original request:
{q}

The complete Pro model panel has already planned and reviewed this work. Use the
reviewed direction below to implement the final artifact, correcting conflicts
yourself. Deliver the complete runnable artifact now.

Panel synthesis:
{panel_synthesis}"""},
    ], 0.2, max_tok)


ROLE_PROMPTS = {
    M_GLM: "You are the planning and synthesis lead. Build a complete answer with dependencies, edge cases, and a clear execution path.",
    M_DEEPSEEK: "You are the rigorous reasoning specialist. Derive the technical, mathematical, or logical core and check it carefully.",
    M_KIMI: "You are the UI/UX and implementation specialist. Review interaction, usability, accessibility, and production implementation details when relevant.",
    M_MINIMAX: "You are the long-context, creative, multimodal, and product specialist. Check product completeness, visual coherence, and user value.",
    M_GEMINI: "You are the visual UI, accessibility, multimodal, and tool-use reviewer. Identify observable interaction and accessibility issues.",
    M_LUNA: "Produce an independent solution. Seek a distinct approach, tool opportunities, and omissions in likely consensus.",
    M_KIMI_FRONTIER: "You are the frontier adjudicator. Solve complex professional tasks rigorously and identify where weaker proposals can fail.",
    M_GROK: "You are the coding-agent critic and repair specialist. Hunt bugs, unsafe assumptions, integration failures, and missing tests.",
}


async def role_candidate(client, model: str, messages: list, temp: float, max_tok: int) -> Result:
    """Run one documented Pro role without replacing the caller's conversation."""
    return await call_model(client, model, [
        {"role": "system", "content": ROLE_PROMPTS[model]},
        *messages,
    ], temp, max_tok)


async def bounded_role_candidate(client, model: str, messages: list, temp: float, max_tok: int) -> Result:
    """Return a usable panel candidate without allowing one model to stall MoA."""
    try:
        return await asyncio.wait_for(
            role_candidate(client, model, messages, temp, max_tok),
            timeout=PANEL_ROLE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("Quality panel role timed out: %s", model)
        return Result(False, "", 0)


async def run_quality_first_panel(client, messages: list, q: str, temp: float, max_tok: int, math_q: bool) -> tuple:
    """Hard-Pro panel: all documented specialists propose, then synthesize and verify."""
    role_models = [M_GLM, M_DEEPSEEK, M_KIMI, M_MINIMAX, M_GEMINI, M_LUNA, M_KIMI_FRONTIER, M_GROK]
    # Panel members are reviewers and planners, not eight competing final
    # artifact generators.  Keeping their drafts concise preserves the full
    # role diversity while reserving the output/latency budget for GLM's final
    # synthesis (which receives the caller's requested max token budget).
    draft_max_tok = min(max_tok, 900)
    results = await asyncio.gather(*[
        bounded_role_candidate(client, model, messages, temp, draft_max_tok) for model in role_models
    ])
    candidates = [
        {"name": model, "content": result.content}
        for model, result in zip(role_models, results)
        if result.success and result.content
    ]
    tokens = sum(result.tokens for result in results)
    if len(candidates) != len(role_models):
        logger.warning("Quality panel incomplete: %s/%s proposal roles completed", len(candidates), len(role_models))
        return "", tokens, [candidate["name"] for candidate in candidates]

    # Math gets an additional self-consistency candidate from the reasoning
    # specialist; it complements, rather than displaces, the full panel.
    if math_q:
        consistent, sc_tokens = await self_consistency(client, q, draft_max_tok)
        tokens += sc_tokens
        if consistent:
            candidates.append({"name": "DeepSeek self-consistency", "content": consistent})

    try:
        synthesis = await asyncio.wait_for(
            aggregate(client, q, candidates, max_tok),
            timeout=PANEL_SYNTHESIS_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("Quality panel synthesis timed out; returning strongest completed candidate")
        return "", tokens, [candidate["name"] for candidate in candidates]
    tokens += synthesis.tokens
    completed_models = [candidate["name"] for candidate in candidates]
    if synthesis.success and synthesis.content:
        completed_models.append(M_GLM)
    return (
        synthesis.content if synthesis.success and synthesis.content else candidates[0]["content"],
        tokens,
        completed_models,
    )


async def orchestrate(client, messages: list, temp: float, max_tok: int, deadline_seconds: int = ORCHESTRATION_DEADLINE_SECONDS) -> dict:
    start = time.time()
    tokens = 0
    q = messages[-1]["content"] if messages else ""
    diff = classify(q)
    math_q = is_math(q)
    creative = is_creative(q)
    multimodal = is_multimodal(q)

    # Pro is deliberately all-model for every task class. Difficulty now
    # changes only optional work (for example, DeepSeek self-consistency for
    # math); it must never collapse a paid Pro request into one model.
    # Full documented Pro panel → GLM synthesis → Nemotron QA →
    # corrective specialist pass → Kimi K3 adjudication when the QA gate remains low.
    role_models = [M_GLM, M_DEEPSEEK, M_KIMI, M_MINIMAX, M_GEMINI, M_LUNA, M_KIMI_FRONTIER, M_GROK]
    requested_models = [*role_models, M_NEMOTRON]
    final, tokens, completed_models = await run_quality_first_panel(client, messages, q, temp, max_tok, math_q)
    if not final:
        return {"content": "", "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000), "requested_models": requested_models, "completed_models": completed_models}

    # A synthesis is an excellent answer for prose, but it is not a reliable
    # delivery format for an interactive artifact.  For webpages and games,
    # retain the all-model panel as the architecture/review stage and give Kimi
    # a dedicated, full-budget implementation pass.  Playground can then open
    # the returned HTML directly in its sandboxed preview instead of exposing
    # users to a mixture of reviewer notes and code fragments.
    if is_code_artifact_request(q):
        remaining = deadline_seconds - 5 - (time.time() - start)
        if remaining > 0:
            try:
                artifact = await asyncio.wait_for(
                    generate_code_artifact(client, q, final, max_tok),
                    timeout=min(CODE_ARTIFACT_TIMEOUT_SECONDS, remaining),
                )
            except asyncio.TimeoutError:
                logger.warning("Code artifact delivery timed out; retaining quality-panel synthesis")
                artifact = Result(False, "", 0)
            tokens += artifact.tokens
            if artifact.success and artifact.content:
                final = artifact.content
                completed_models.append(M_KIMI)

    # Preserve a completed quality-panel answer if QA or repair cannot finish
    # within the remaining request window.  A verifier must improve a result,
    # never cause an otherwise usable artifact to be discarded.
    remaining = deadline_seconds - 5 - (time.time() - start)
    if remaining <= 0:
        return {"content": "", "tokens": tokens, "tier": "hard-quality-panel-qa-unavailable", "time": int((time.time() - start) * 1000), "requested_models": requested_models, "completed_models": completed_models}
    try:
        qa_score, qa_tokens, qa_feedback, qa_succeeded = await asyncio.wait_for(
            qa_gate(client, q, final),
            timeout=min(QUALITY_QA_TIMEOUT_SECONDS, remaining),
        )
    except asyncio.TimeoutError:
        logger.warning("Quality QA timed out; delivering completed panel answer")
        return {"content": "", "tokens": tokens, "tier": "hard-quality-panel-qa-unavailable", "time": int((time.time() - start) * 1000), "requested_models": requested_models, "completed_models": completed_models}
    tokens += qa_tokens
    if not qa_succeeded:
        return {"content": "", "tokens": tokens, "tier": "hard-quality-panel-qa-unavailable", "time": int((time.time() - start) * 1000), "requested_models": requested_models, "completed_models": completed_models}
    completed_models.append(M_NEMOTRON)
    if qa_score < 8:
        remaining = deadline_seconds - 5 - (time.time() - start)
        if remaining <= 0:
            return {"content": final, "tokens": tokens, "tier": "hard-quality-panel", "time": int((time.time() - start) * 1000), "requested_models": requested_models, "completed_models": list(dict.fromkeys(completed_models))}
        try:
            improved = await asyncio.wait_for(
                reflexion(client, q, final, qa_feedback, max_tok),
                timeout=min(QUALITY_REPAIR_TIMEOUT_SECONDS, remaining),
            )
        except asyncio.TimeoutError:
            logger.warning("Quality repair timed out; delivering verified panel answer")
            improved = Result(False, "", 0)
        tokens += improved.tokens
        if improved.success and improved.content:
            # The repair consumes explicit independent QA feedback.  A second
            # judge call is optional telemetry, not a reason to lose the
            # corrected artifact under a tight deadline.
            final = improved.content
            completed_models.append(M_DEEPSEEK)
    return {
        "content": final, "tokens": tokens, "tier": "hard-quality-panel", "time": int((time.time() - start) * 1000),
        "requested_models": requested_models, "completed_models": list(dict.fromkeys(completed_models)),
    }

    # Legacy implementation retained below temporarily for diff review.
    # MATH: self-consistency replaces single DeepSeek call
    if math_q:
        r1, r3, sc = await asyncio.gather(
            call_model(client, M_GLM, messages, temp, max_tok),
            call_model(client, M_GEMINI, messages, temp, max_tok),
            self_consistency(client, q, max_tok),
        )
        tokens += r1.tokens + r3.tokens + sc[1]
        l1 = []
        if r1.success and r1.content:
            l1.append({"name": "Model A (GLM-5.2)", "content": r1.content})
        if sc[0]:
            l1.append({"name": "Model B (DeepSeek, self-consistency)", "content": sc[0]})
        if r3.success and r3.content:
            l1.append({"name": "Model C (Gemini 3.5 Flash)", "content": r3.content})
        if not l1:
            return {"content": "", "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}
        agg = await aggregate(client, q, l1, max_tok)
        tokens += agg.tokens
        final = agg.content if (agg.success and agg.content) else l1[0]["content"]
        qa_score, qa_tokens, qa_feedback = await qa_gate(client, q, final)
        tokens += qa_tokens
        if qa_score < 8:
            ref = await reflexion(client, q, final, qa_feedback, max_tok)
            tokens += ref.tokens
            if ref.success and ref.content:
                qa2_score, qa2_tokens, _ = await qa_gate(client, q, ref.content)
                tokens += qa2_tokens
                if qa2_score > qa_score:
                    final = ref.content
            if qa_score < 6:
                frontier = await call_model(client, M_KIMI_FRONTIER, messages, temp, max_tok)
                tokens += frontier.tokens
                if frontier.success and frontier.content:
                    qa3_score, qa3_tokens, _ = await qa_gate(client, q, frontier.content)
                    tokens += qa3_tokens
                    if qa3_score > qa_score:
                        final = frontier.content
        return {"content": final, "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}

    # CREATIVE: Route to MiniMax M3 as 3rd proposer
    if creative:
        r1, r2, r3 = await asyncio.gather(
            call_model(client, M_GLM, messages, temp, max_tok),
            call_model(client, M_DEEPSEEK, messages, temp, max_tok),
            call_model(client, M_MINIMAX, messages, temp, max_tok),
        )
        tokens += r1.tokens + r2.tokens + r3.tokens
        l1 = []
        if r1.success and r1.content:
            l1.append({"name": "Model A (GLM-5.2)", "content": r1.content})
        if r2.success and r2.content:
            l1.append({"name": "Model B (DeepSeek V4 Pro)", "content": r2.content})
        if r3.success and r3.content:
            l1.append({"name": "Model C (MiniMax M3, creative)", "content": r3.content})
        if not l1:
            return {"content": "", "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}
        agg = await aggregate(client, q, l1, max_tok)
        tokens += agg.tokens
        final = agg.content if (agg.success and agg.content) else l1[0]["content"]
        qa_score, qa_tokens, qa_feedback = await qa_gate(client, q, final)
        tokens += qa_tokens
        if qa_score < 8:
            ref = await reflexion(client, q, final, qa_feedback, max_tok)
            tokens += ref.tokens
            if ref.success and ref.content:
                qa2_score, qa2_tokens, _ = await qa_gate(client, q, ref.content)
                tokens += qa2_tokens
                if qa2_score > qa_score:
                    final = ref.content
            if qa_score < 6:
                frontier = await call_model(client, M_KIMI_FRONTIER, messages, temp, max_tok)
                tokens += frontier.tokens
                if frontier.success and frontier.content:
                    qa3_score, qa3_tokens, _ = await qa_gate(client, q, frontier.content)
                    tokens += qa3_tokens
                    if qa3_score > qa_score:
                        final = frontier.content
        return {"content": final, "tokens": tokens, "tier": "hard-creative", "time": int((time.time() - start) * 1000)}

    # HARD (general): 3 proposals from GLM + DeepSeek + Gemini
    r1, r2, r3 = await asyncio.gather(
        call_model(client, M_GLM, messages, temp, max_tok),
        call_model(client, M_DEEPSEEK, messages, temp, max_tok),
        call_model(client, M_GEMINI, messages, temp, max_tok),
    )
    tokens += r1.tokens + r2.tokens + r3.tokens
    l1 = []
    if r1.success and r1.content:
        l1.append({"name": "Model A (GLM-5.2)", "content": r1.content})
    if r2.success and r2.content:
        l1.append({"name": "Model B (DeepSeek V4 Pro)", "content": r2.content})
    if r3.success and r3.content:
        l1.append({"name": "Model C (Gemini 3.5 Flash)", "content": r3.content})
    if not l1:
        return {"content": "", "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}
    agg = await aggregate(client, q, l1, max_tok)
    tokens += agg.tokens
    final = agg.content if (agg.success and agg.content) else l1[0]["content"]
    qa_score, qa_tokens, qa_feedback = await qa_gate(client, q, final)
    tokens += qa_tokens
    if qa_score < 8:
        ref = await reflexion(client, q, final, qa_feedback, max_tok)
        tokens += ref.tokens
        if ref.success and ref.content:
            qa2_score, qa2_tokens, _ = await qa_gate(client, q, ref.content)
            tokens += qa2_tokens
            if qa2_score > qa_score:
                final = ref.content
        if qa_score < 6:
            frontier = await call_model(client, M_KIMI_FRONTIER, messages, temp, max_tok)
            tokens += frontier.tokens
            if frontier.success and frontier.content:
                qa3_score, qa3_tokens, _ = await qa_gate(client, q, frontier.content)
                tokens += qa3_tokens
                if qa3_score > qa_score:
                    final = frontier.content
    return {"content": final, "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("temuclaude-prod"),
        modal.Secret.from_name("temuclaude-gateway"),
        modal.Secret.from_name("temuclaude-supabase"),
    ],
    scaledown_window=300,
    timeout=120,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def serve():
    """FastAPI server wrapping the orchestration pipeline."""
    import httpx
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    api = FastAPI(title="TemuClaude API")

    @api.get("/")
    async def root():
        return {"status": "ok", "model": "temuclaude"}

    @api.get("/models")
    @api.get("/v1/models")
    async def list_models():
        return {
            "data": [
                {
                    "id": "temuclaude/temuclaude",
                    "name": "TemuClaude",
                    "created": 1778398147,
                    "input_modalities": ["text"],
                    "output_modalities": ["text"],
                    "quantization": "fp16",
                    "context_length": 8192,
                    "max_output_length": 4096,
                    "pricing": {
                        "prompt": "0.000002",        # Cost per prompt token in USD ($2.00 / 1M)
                        "completion": "0.000008",    # Cost per completion token in USD ($8.00 / 1M)
                        "image": "0",
                        "request": "0",
                        "input_cache_read": "0"
                    },
                    "supported_sampling_parameters": ["temperature", "max_tokens"],
                    "supported_features": ["reasoning"],
                    "description": "TemuClaude — 8-Model Multi-Model AI Orchestration (OpenAI-compatible)",
                    "is_ready": True,
                    "is_free": False,
                    "discount_to_user": 0,
                    "capacity_tpm": 1000000,
                    "openrouter": {
                        "slug": "temuclaude/temuclaude"
                    },
                    "datacenters": [
                        {
                            "country_code": "US"
                        }
                    ]
                }
            ]
        }

    @api.get("/health")
    async def health():
        return {"status": "ok"}

    @api.get("/v1/chat/completions")
    async def model_info():
        return JSONResponse({
            "status": "ok",
            "model": "temuclaude",
            "description": "TemuClaude — 8-Model Multi-Model AI Orchestration (OpenAI-compatible)",
            "models": [
                {"name": "GLM-5.2", "role": "Orchestrator + Aggregator", "iq": 51},
                {"name": "DeepSeek V4 Pro", "role": "Reasoning + Self-Consistency + Reflexion", "iq": 44},
                {"name": "Gemini 3.5 Flash", "role": "Legal/Health Specialist", "iq": 50},
                {"name": "Hy3 Preview", "role": "Trivial Router (cheapest)", "iq": None},
                {"name": "MiniMax M3", "role": "Vision + Creative", "iq": 44},
                {"name": "MiMo-V2.5", "role": "Multimodal", "iq": 40},
                {"name": "Nemotron", "role": "QA Gate (FREE)", "iq": 38},
                {"name": "Claude Sonnet 5", "role": "Frontier Fallback", "iq": 53},
            ],
            "pipeline": ["moa-fusion", "self-consistency", "aggregation", "qa-gate", "reflexion", "frontier-fallback"],
        })

    @api.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        try:
            body = await request.json()
            messages = body.get("messages", [])
            model_name = body.get("model", "temuclaude")
            temp = body.get("temperature", 0.6)
            max_tok = body.get("max_tokens", 4096)

            if not messages or not isinstance(messages, list):
                return JSONResponse(
                    {"error": {"message": "messages array is required", "type": "invalid_request_error"}},
                    status_code=400,
                )

            async with httpx.AsyncClient(timeout=60) as client:
                # Auth check: website gateway uses master key; direct users use tmc_ keys.
                auth_key = request.headers.get("authorization", "").replace("Bearer ", "")
                # A dedicated gateway key can be rotated independently of the
                # provider/Supabase credentials stored in the legacy app secret.
                master_key = os.environ.get("TEMUCLAUDE_GATEWAY_KEY") or os.environ.get("TEMUCLAUDE_MASTER_KEY", "")
                direct_user = None
                if master_key and auth_key == master_key:
                    pass
                elif auth_key.startswith("tmc_"):
                    direct_user = await validate_customer_api_key(client, auth_key)
                    if not direct_user:
                        return JSONResponse(
                            {"error": {"message": "Invalid API key", "type": "authentication_error"}},
                            status_code=401,
                        )
                    plan = direct_user.get("plan") or "free"
                    if plan not in PLAN_MONTHLY_LIMITS:
                        return JSONResponse(
                            {"error": {"message": "API access requires a Developer, Pro, Max, or Enterprise plan.", "type": "permission_error"}},
                            status_code=403,
                        )
                    monthly_limit = PLAN_MONTHLY_LIMITS[plan]
                    if monthly_limit >= 0 and await get_monthly_usage(client, direct_user["id"]) >= monthly_limit:
                        return JSONResponse(
                            {"error": {"message": "Monthly API quota exceeded.", "type": "rate_limit_error"}},
                            status_code=429,
                        )
                elif master_key:
                    return JSONResponse(
                        {"error": {"message": "Invalid API key", "type": "authentication_error"}},
                        status_code=401,
                    )

                result = await complete_with_rescue(client, messages, temp, max_tok)
                if not has_usable_content(result):
                    return JSONResponse(
                        {"error": {"message": "TemuClaude could not produce a completion. Please retry shortly.", "type": "server_error"}},
                        status_code=503,
                    )

                prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
                completion_tokens = len(result["content"].split())
                if direct_user:
                    await increment_customer_usage(client, direct_user["id"], prompt_tokens, completion_tokens)

            return JSONResponse({
                "id": f"chatcmpl-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": result["content"]},
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": result["tokens"],
                },
                # The gateway uses this to show the real orchestration shape
                # instead of collapsing the Modal service into one model.
                "orchestration": {
                    "tier": result.get("tier", "unknown"),
                    "requested_models": result.get("requested_models", [M_GLM]),
                    "completed_models": result.get("completed_models", []),
                    "telemetry_version": 1,
                },
            })
        except Exception as e:
            return JSONResponse(
                {"error": {"message": f"Internal server error: {str(e)}", "type": "server_error"}},
                status_code=500,
            )

    @api.post("/v1/jobs/{job_id}/start")
    async def start_generation_job(job_id: str, request: Request):
        """Accept a durable job quickly; its worker must never occupy this HTTP request."""
        auth_key = request.headers.get("authorization", "").replace("Bearer ", "")
        master_key = os.environ.get("TEMUCLAUDE_GATEWAY_KEY") or os.environ.get("TEMUCLAUDE_MASTER_KEY", "")
        if not master_key or auth_key != master_key:
            return JSONResponse({"error": {"message": "Invalid API key", "type": "authentication_error"}}, status_code=401)
        if not re.fullmatch(r"gen_[0-9a-fA-F-]{36}", job_id):
            return JSONResponse({"error": {"message": "Invalid generation job ID", "type": "invalid_request_error"}}, status_code=400)
        # Modal owns scheduling/retries after this point.  Returning 202 avoids
        # the 150-second Modal web-endpoint limit for maximum-quality runs.
        await run_generation_job.spawn.aio(job_id)
        return JSONResponse({"id": job_id, "status": "queued"}, status_code=202)

    return api


async def _generation_job_request(client, method: str, path: str, *, params: Optional[dict] = None, payload: Optional[dict] = None):
    """Call Supabase REST with the service credential; never expose it to users."""
    base = _supabase_url()
    headers = _supabase_headers()
    if not base or not headers:
        raise RuntimeError("Supabase durable-job configuration is unavailable")
    response = await client.request(method, f"{base}{path}", headers=headers, params=params, json=payload)
    if response.status_code >= 300:
        raise RuntimeError(f"Durable-job storage request failed ({response.status_code})")
    return response


async def _generation_job_event(client, job_id: str, stage: str, event: str, detail: Optional[dict] = None) -> None:
    await _generation_job_request(client, "POST", "/rest/v1/temuclaude_generation_job_events", payload={
        "job_id": job_id, "stage": stage, "event": event, "detail": detail or {}, "created_at": int(time.time()),
    })


async def _update_generation_job(client, job_id: str, changes: dict) -> None:
    changes["updated_at"] = int(time.time())
    await _generation_job_request(
        client, "PATCH", "/rest/v1/temuclaude_generation_jobs",
        params={"id": f"eq.{job_id}"}, payload=changes,
    )


MAXIMUM_QUALITY_REPAIR_REVISIONS = 8
MAXIMUM_QUALITY_MAX_WORKER_ATTEMPTS = 1000
MAXIMUM_QUALITY_ACCEPTANCE_SCORE = 8.0


class DurableStageRetry(RuntimeError):
    """A provider/stage is recoverable; retain its checkpoint and requeue."""


async def _load_generation_job(client, job_id: str) -> Optional[dict]:
    response = await _generation_job_request(
        client, "GET", "/rest/v1/temuclaude_generation_jobs",
        params={"id": f"eq.{job_id}", "select": "*", "limit": "1"},
    )
    rows = response.json()
    return rows[0] if rows else None


async def _ensure_job_active(client, job_id: str) -> None:
    job = await _load_generation_job(client, job_id)
    if not job or job.get("status") == "cancel_requested":
        if job and job.get("status") == "cancel_requested":
            await _update_generation_job(client, job_id, {"status": "cancelled", "stage": "cancelled", "lease_expires_at": None})
            await _generation_job_event(client, job_id, "cancelled", "cancelled")
        raise asyncio.CancelledError("generation job was cancelled")


async def _checkpoint_generation_stage(client, job_id: str, stage: str, state: dict, *, status: str = "running") -> None:
    await _ensure_job_active(client, job_id)
    await _update_generation_job(client, job_id, {
        "status": status, "stage": stage, "stage_results": state,
        # A short renewable lease lets the recovery scheduler take over after
        # a preemption without running duplicate providers for hours.
        "lease_expires_at": int(time.time()) + 900,
    })
    await _generation_job_event(client, job_id, stage, "checkpointed")


def _validate_html_artifact(content: str) -> dict:
    """Deterministic artifact gate before the model QA pass.

    This deliberately rejects common partial model outputs. Browser-isolated
    interaction checks are added by the web sandbox stage after the artifact is
    stored; no LLM is allowed to waive these structural requirements.
    """
    text = content.strip()
    lower = text.lower()
    errors = []
    if not lower.startswith("<!doctype html"):
        errors.append("missing_doctype")
    if "<html" not in lower or "</html>" not in lower:
        errors.append("missing_html_document")
    if "<script" not in lower:
        errors.append("missing_javascript")
    if "<style" not in lower:
        errors.append("missing_css")
    if len(text) < 400:
        errors.append("artifact_too_short")
    if "</script>" not in lower or "</style>" not in lower:
        errors.append("unclosed_asset_block")
    if "..." in text or "todo" in lower:
        errors.append("placeholder_content")
    return {"passed": not errors, "errors": errors, "length": len(text)}


async def _run_isolated_preview(client, html: str, user_id: str) -> dict:
    """Launch the artifact in the existing E2B preview service and require health."""
    base = (os.environ.get("TEMUCLAUDE_WEB_URL") or "https://temuclaude.com").rstrip("/")
    key = os.environ.get("TEMUCLAUDE_GATEWAY_KEY") or os.environ.get("TEMUCLAUDE_MASTER_KEY", "")
    if not key:
        raise DurableStageRetry("sandbox_gateway_key_unavailable")
    response = await client.post(
        f"{base}/api/internal/sandbox-validation",
        headers={"x-temuclaude-internal-key": key, "Content-Type": "application/json"},
        json={"html": html, "user_id": user_id},
        timeout=70,
    )
    if response.status_code != 200:
        raise DurableStageRetry(f"sandbox_preview_unavailable:{response.status_code}")
    payload = response.json()
    preview = payload.get("preview") if isinstance(payload, dict) else None
    if not isinstance(preview, dict) or not isinstance(preview.get("previewUrl"), str):
        raise DurableStageRetry("sandbox_preview_invalid_response")
    return {
        "passed": True,
        "sandbox_id": preview.get("sandboxId"),
        "preview_url": preview.get("previewUrl"),
        "expires_at": preview.get("expiresAt"),
    }


async def _durable_panel(client, messages: list, state: dict, job_id: str) -> list:
    role_models = [M_GLM, M_DEEPSEEK, M_KIMI, M_MINIMAX, M_GEMINI, M_LUNA, M_KIMI_FRONTIER, M_GROK]
    panel = state.setdefault("panel", {})
    for model in role_models:
        if isinstance(panel.get(model), str) and panel[model].strip():
            continue
        await _ensure_job_active(client, job_id)
        result = await bounded_role_candidate(client, model, messages, 0.6, 900)
        if not result.success or not result.content:
            raise DurableStageRetry(f"panel_role_unavailable:{model}")
        panel[model] = result.content
        await _checkpoint_generation_stage(client, job_id, "panel", state)
    return [{"name": model, "content": panel[model]} for model in role_models]


async def _durable_synthesis(client, q: str, candidates: list, state: dict, job_id: str) -> str:
    synthesis = state.get("synthesis")
    if isinstance(synthesis, str) and synthesis.strip():
        return synthesis
    await _ensure_job_active(client, job_id)
    result = await aggregate(client, q, candidates, 4096)
    if not result.success or not result.content:
        raise DurableStageRetry("synthesis_unavailable")
    state["synthesis"] = result.content
    await _checkpoint_generation_stage(client, job_id, "synthesis", state)
    return result.content


async def _durable_artifact(client, q: str, synthesis: str, state: dict, job_id: str) -> str:
    artifact = state.get("artifact")
    if isinstance(artifact, str) and artifact.strip():
        return artifact
    await _ensure_job_active(client, job_id)
    result = await generate_code_artifact(client, q, synthesis, 4096)
    if not result.success or not result.content:
        raise DurableStageRetry("artifact_delivery_unavailable")
    state["artifact"] = result.content
    await _checkpoint_generation_stage(client, job_id, "artifact", state)
    return result.content


async def _durable_qa(client, q: str, answer: str, state: dict, job_id: str) -> tuple:
    qa = state.get("qa")
    if isinstance(qa, dict) and isinstance(qa.get("score"), (int, float)):
        return float(qa["score"]), str(qa.get("feedback") or "")
    await _ensure_job_active(client, job_id)
    score, _, feedback, succeeded = await qa_gate(client, q, answer)
    if not succeeded:
        raise DurableStageRetry("qa_unavailable")
    state["qa"] = {"score": score, "feedback": feedback}
    await _checkpoint_generation_stage(client, job_id, "qa", state, status="validating")
    return score, feedback


async def _schedule_generation_retry(client, job_id: str, state: dict, attempt: int, reason: str) -> None:
    if attempt >= MAXIMUM_QUALITY_MAX_WORKER_ATTEMPTS:
        await _update_generation_job(client, job_id, {"status": "needs_review", "stage": "needs_review", "last_error_code": reason, "stage_results": state, "lease_expires_at": None})
        await _generation_job_event(client, job_id, "needs_review", "retry_budget_exhausted", {"reason": reason, "attempt": attempt})
        return
    delay_seconds = min(300, 2 ** min(8, max(1, attempt)))
    await _update_generation_job(client, job_id, {"status": "waiting_retry", "last_error_code": reason, "stage_results": state, "lease_expires_at": None, "next_run_at": int(time.time()) + delay_seconds})
    await _generation_job_event(client, job_id, "retry", "scheduled", {"reason": reason, "attempt": attempt, "delay_seconds": delay_seconds})
    # The scheduler also recovers this job if this hand-off is interrupted.
    await asyncio.sleep(delay_seconds)
    await run_generation_job.spawn.aio(job_id)


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("temuclaude-prod"),
        modal.Secret.from_name("temuclaude-gateway"),
        modal.Secret.from_name("temuclaude-supabase"),
    ],
    timeout=86400,
)
async def run_generation_job(job_id: str):
    """Run one durable maximum-quality job outside any web request.

    State is checkpointed in Supabase, so a later recovery worker can resume
    after a container interruption instead of asking the browser to retry.
    """
    import httpx

    async with httpx.AsyncClient(timeout=120) as client:
        # Atomically claim the job. Duplicate dispatches are harmless: only a
        # queued/retryable job with no live lease can produce a worker payload.
        response = await _generation_job_request(
            client, "POST", "/rest/v1/rpc/temuclaude_claim_generation_job",
            payload={"p_job_id": job_id, "p_lease_token": str(uuid.uuid4()), "p_lease_seconds": 900},
        )
        rows = response.json()
        if not rows:
            return
        job = rows[0]
        messages = job.get("messages")
        if not isinstance(messages, list) or not messages:
            await _update_generation_job(client, job_id, {"status": "failed", "stage": "failed", "last_error_code": "invalid_messages"})
            await _generation_job_event(client, job_id, "failed", "failed", {"code": "invalid_messages"})
            return

        attempt = int(job.get("attempt") or 0)
        state = job.get("stage_results") if isinstance(job.get("stage_results"), dict) else {}
        q = messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""
        await _update_generation_job(client, job_id, {"status": "running", "stage": str(job.get("stage") or "panel"), "stage_results": state})
        await _generation_job_event(client, job_id, str(job.get("stage") or "panel"), "started", {"attempt": attempt})
        try:
            candidates = await _durable_panel(client, messages, state, job_id)
            synthesis = await _durable_synthesis(client, q, candidates, state, job_id)
            is_artifact = str(job.get("request_kind")) == "artifact"
            content = await _durable_artifact(client, q, synthesis, state, job_id) if is_artifact else synthesis
            if is_artifact:
                validation = _validate_html_artifact(content)
                state["sandbox_validation"] = validation
                await _checkpoint_generation_stage(client, job_id, "sandbox_validation", state, status="validating")
                if not validation["passed"]:
                    raise DurableStageRetry("artifact_validation_failed:" + ",".join(validation["errors"]))
                state["sandbox_validation"] = await _run_isolated_preview(client, content, str(job.get("user_id") or ""))
                await _checkpoint_generation_stage(client, job_id, "sandbox_validation", state, status="validating")
            score, feedback = await _durable_qa(client, q, content, state, job_id)
            repairs = int(state.get("repair_count") or 0)
            while score < MAXIMUM_QUALITY_ACCEPTANCE_SCORE:
                if repairs >= MAXIMUM_QUALITY_REPAIR_REVISIONS:
                    await _update_generation_job(client, job_id, {"status": "needs_review", "stage": "needs_review", "last_error_code": "qa_threshold_not_met", "stage_results": state, "lease_expires_at": None})
                    await _generation_job_event(client, job_id, "needs_review", "qa_repair_budget_exhausted", {"score": score, "repairs": repairs})
                    return
                await _ensure_job_active(client, job_id)
                repairs += 1
                state["repair_count"] = repairs
                state.pop("qa", None)
                repair_prompt = f"{q}\n\nIndependent QA feedback to fix: {feedback}"
                repaired = await generate_code_artifact(client, repair_prompt, content, 4096) if is_artifact else await reflexion(client, q, content, feedback, 4096)
                if not repaired.success or not repaired.content:
                    raise DurableStageRetry("repair_unavailable")
                content = repaired.content
                state["artifact" if is_artifact else "synthesis"] = content
                await _checkpoint_generation_stage(client, job_id, "repair", state, status="validating")
                if is_artifact:
                    validation = _validate_html_artifact(content)
                    state["sandbox_validation"] = validation
                    await _checkpoint_generation_stage(client, job_id, "sandbox_validation", state, status="validating")
                    if not validation["passed"]:
                        raise DurableStageRetry("artifact_validation_failed:" + ",".join(validation["errors"]))
                    state["sandbox_validation"] = await _run_isolated_preview(client, content, str(job.get("user_id") or ""))
                    await _checkpoint_generation_stage(client, job_id, "sandbox_validation", state, status="validating")
                score, feedback = await _durable_qa(client, q, content, state, job_id)
            artifact = content if is_artifact else None
            await _ensure_job_active(client, job_id)
            await _update_generation_job(client, job_id, {
                "status": "completed", "stage": "completed", "completed_at": int(time.time()),
                "final_content": content, "final_artifact": artifact,
                "stage_results": state, "lease_expires_at": None,
            })
            await _generation_job_event(client, job_id, "completed", "completed", {"artifact": bool(artifact), "qa_score": score})
        except asyncio.CancelledError:
            return
        except DurableStageRetry as exc:
            await _schedule_generation_retry(client, job_id, state, attempt, str(exc))
        except Exception as exc:
            logger.exception("Durable generation job failed: %s", job_id)
            await _schedule_generation_retry(client, job_id, state, attempt, type(exc).__name__)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("temuclaude-prod"), modal.Secret.from_name("temuclaude-supabase")],
    schedule=modal.Period(minutes=5),
)
async def recover_generation_jobs():
    """Re-dispatch jobs whose prior worker exited or whose lease expired."""
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        response = await _generation_job_request(client, "POST", "/rest/v1/rpc/temuclaude_recover_generation_jobs", payload={"p_limit": 25})
        for job in response.json():
            job_id = job.get("id") if isinstance(job, dict) else None
            if isinstance(job_id, str):
                await run_generation_job.spawn.aio(job_id)


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("temuclaude-prod"),
        modal.Secret.from_name("temuclaude-gateway"),
        modal.Secret.from_name("temuclaude-supabase"),
    ],
)
async def test():
    """Local entrypoint to test the deployed endpoint."""
    import httpx
    url = await serve.get_web_url.aio()
    print(f"Server URL: {url}")

    async with httpx.AsyncClient(timeout=120) as client:
        # Health check
        r = await client.get(f"{url}/health")
        print(f"Health: {r.status_code} {r.json()}")

        # Chat test
        r = await client.post(
            f"{url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('TEMUCLAUDE_GATEWAY_KEY') or os.environ.get('TEMUCLAUDE_MASTER_KEY', '')}"},
            json={
                "model": "temuclaude",
                "messages": [{"role": "user", "content": "What is 2+2?"}],
                "temperature": 0.6,
                "max_tokens": 100,
            },
        )
        print(f"Chat: {r.status_code}")
        d = r.json()
        print(f"Response: {d.get('choices', [{}])[0].get('message', {}).get('content', '')[:200]}")
