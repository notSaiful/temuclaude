"""
TemuClaude — Modal Deployment
8-Model Multi-Model AI Orchestration (OpenAI-compatible API)
Exact port of the tested Vercel pipeline.
"""
import os
import json
import re
import time
import asyncio
from typing import Optional

import modal

app = modal.App("temuclaude")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("httpx==0.28.1", "fastapi==0.115.6")
)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── 8-MODEL POOL ──────────────────────────────────────────────
M_GLM = "z-ai/glm-5.2"
M_DEEPSEEK = "deepseek/deepseek-v4-pro"
M_GEMINI = "google/gemini-3.5-flash"
M_HY3 = "tencent/hy3-preview"
M_MINIMAX = "minimax/minimax-m3"
M_MIMO = "xiaomi/mimo-v2.5"
M_NEMOTRON = "nvidia/nemotron-3-ultra-550b-a55b:free"
M_CLAUDE = "anthropic/claude-sonnet-5"


class Result:
    __slots__ = ("success", "content", "tokens")
    def __init__(self, success: bool, content: str, tokens: int):
        self.success = success
        self.content = content
        self.tokens = tokens


async def call_model(client, model: str, messages: list, temp: float = 0.6, max_tok: int = 4096) -> Result:
    """Call a model via OpenRouter with reasoning field fallback.
    Prepends English enforcement system prompt to ensure consistent English output."""
    try:
        # Prepend English system prompt if user didn't provide one
        msgs = messages
        if not any(m.get("role") == "system" for m in messages):
            msgs = [{"role": "system", "content": "You are TemuClaude, an AI assistant. Always respond in clear, professional English. Be concise and direct."}] + messages
        r = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": msgs,
                "temperature": temp,
                "max_tokens": max_tok,
            },
            timeout=90,
        )
        if r.status_code != 200:
            return Result(False, "", 0)
        d = r.json()
        msg = d.get("choices", [{}])[0].get("message", {})
        c = msg.get("content") or ""
        if not c:
            # Fallback 1: reasoning field
            c = msg.get("reasoning") or ""
        if not c:
            # Fallback 2: reasoning_details array
            rd = msg.get("reasoning_details")
            if isinstance(rd, list):
                c = "".join(x.get("text", "") for x in rd if isinstance(x, dict))
        # Strip whitespace
        c = (c or "").strip()
        return Result(bool(c), c, d.get("usage", {}).get("total_tokens", 0))
    except Exception:
        return Result(False, "", 0)


def classify(text: str) -> str:
    """Difficulty Classifier — heuristic, no API call.
    Code generation tasks route to 'medium' (single strong model) not 'hard' (full MoA)."""
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

    # Code generation detection — route to medium (single model), not hard (MoA)
    is_code_gen = bool(re.search(r'\b(build|create|generate|write|make|develop|implement|code|html|css|javascript|python|function|class|component|game|website|webpage|app|script|program|landing page|dashboard)\b', l, re.I)) and \
                  bool(re.search(r'\b(html|css|js|javascript|python|code|function|component|page|game|app|script|file|complete)\b', l, re.I))
    if is_code_gen:
        return "medium"

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
    return (score, r.tokens, feedback)


async def reflexion(client, q: str, prev_answer: str, feedback: str, max_tok: int) -> Result:
    return await call_model(client, M_DEEPSEEK, [
        {"role": "system", "content": "You are answering a question. A previous attempt received feedback. Use it to improve. Output ONLY the improved answer."},
        {"role": "user", "content": f"Question: {q}\n\nPrevious answer: {prev_answer}\n\nFeedback: {feedback}\n\nImproved answer:"},
    ], 0.4, max_tok)


async def orchestrate(client, messages: list, temp: float, max_tok: int) -> dict:
    start = time.time()
    tokens = 0
    q = messages[-1]["content"] if messages else ""
    diff = classify(q)
    math_q = is_math(q)
    creative = is_creative(q)
    multimodal = is_multimodal(q)

    # TRIVIAL: Hy3 Preview
    if diff == "trivial":
        r = await call_model(client, M_HY3, messages, temp, max_tok)
        if r.success and r.content:
            return {"content": r.content, "tokens": r.tokens, "tier": "trivial", "time": int((time.time() - start) * 1000)}
        r2 = await call_model(client, M_GLM, messages, temp, max_tok)
        return {"content": r2.content, "tokens": r2.tokens, "tier": "trivial-fallback", "time": int((time.time() - start) * 1000)}

    # MEDIUM: Route to best specialist
    if diff == "medium":
        model = M_GLM
        if math_q:
            model = M_DEEPSEEK
        elif creative:
            model = M_MINIMAX
        elif multimodal:
            model = M_MIMO
        r = await call_model(client, model, messages, temp, max_tok)
        return {"content": r.content, "tokens": r.tokens, "tier": "medium", "time": int((time.time() - start) * 1000)}

    # HARD: Full 8-Model MoA Pipeline

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
                frontier = await call_model(client, M_CLAUDE, messages, temp, max_tok)
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
                frontier = await call_model(client, M_CLAUDE, messages, temp, max_tok)
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
            frontier = await call_model(client, M_CLAUDE, messages, temp, max_tok)
            tokens += frontier.tokens
            if frontier.success and frontier.content:
                qa3_score, qa3_tokens, _ = await qa_gate(client, q, frontier.content)
                tokens += qa3_tokens
                if qa3_score > qa_score:
                    final = frontier.content
    return {"content": final, "tokens": tokens, "tier": "hard", "time": int((time.time() - start) * 1000)}


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("openrouter-key")],
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

    @api.get("/v1/models")
    async def list_models():
        return {"object": "list", "data": [{"id": "temuclaude", "object": "model", "owned_by": "temuclaude"}]}

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

            # Auth check (optional)
            auth_key = request.headers.get("authorization", "").replace("Bearer ", "")
            master_key = os.environ.get("TEMUCLAUDE_MASTER_KEY", "")
            if master_key and auth_key != master_key:
                return JSONResponse(
                    {"error": {"message": "Invalid API key", "type": "authentication_error"}},
                    status_code=401,
                )

            client = httpx.AsyncClient(timeout=60)

            # Timeout safeguard: 45s → single GLM fallback
            pipeline_task = asyncio.ensure_future(orchestrate(client, messages, temp, max_tok))

            async def timeout_fallback():
                await asyncio.sleep(45)
                r = await call_model(client, M_GLM, messages, 0.6, max_tok)
                return {"content": r.content, "tokens": r.tokens, "tier": "timeout-fallback", "time": 45000}

            fallback_task = asyncio.ensure_future(timeout_fallback())

            done, pending = await asyncio.wait(
                [pipeline_task, fallback_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
            result = done.pop().result()
            await client.aclose()

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
                    "prompt_tokens": sum(len(m.get("content", "").split()) for m in messages),
                    "completion_tokens": len(result["content"].split()) if result["content"] else 0,
                    "total_tokens": result["tokens"],
                },
            })
        except Exception as e:
            return JSONResponse(
                {"error": {"message": f"Internal server error: {str(e)}", "type": "server_error"}},
                status_code=500,
            )

    return api


@app.function(image=image)
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