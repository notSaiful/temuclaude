# TemuClaude Architecture

> Purpose: TemuClaude has **several independent orchestration implementations** that share a
> brand and architecture concepts but are **separate codepaths**. This document maps them,
> identifies which one website users actually hit, and records what is wired vs. not wired —
> so claims about capabilities match reality (see the project's truthfulness / sidq principle).

## TL;DR

- The **website (Vercel)** runs two TypeScript gateways. The public `/v1` **Pro** gateway
  **proxies to the Python engine** on Fly (Layer 1, live since 2026-07-17, env-gated on
  `TEMUCLAUDE_ENGINE_URL`); Lite and the streaming playground `/api/chat` stay on TS.
- The **Python orchestrator** (`src/orchestrator.py`) is a separate, richer 10-layer engine
  served by `api_server.py` (FastAPI; Fly, Mumbai). The `/v1` Pro gateway **does call it** — Pro
  completions forward to the engine, which applies **Layer 2 adaptive routing** (trivial/medium →
  fast path, hard → full gauntlet). Lite and the TS fallback do not reach the engine.
- Therefore the engine-only features (Z3/SMT, sandboxed code execution, MCTS / self-play,
  shepherding) **are** experienced by `/v1` Pro users **for hard queries** (via the proxy), and
  are **not** for trivial/medium Pro, Lite, or the playground. Public copy must scope them to
  "hard Pro queries." (The engine's QA gate is the **paid** Nemotron 3 Ultra model.)
- `modal_app.py` is a **wired-but-dormant** legacy entrypoint: `route.ts` imports it and calls it
  only when `TEMUCLAUDE_USE_MODAL_BACKEND==='true'`, which is **not set on prod**; and Pro/Lite
  return before the modal block, so it is unreachable in the live flow. Kept by decision.
- **No `src/` modules were deleted** in the conservative cleanup — nothing is genuinely dead
  (every module is at least test-imported). See [Cleanup decision](#cleanup-decision).
- **Known limitations / debt:** the engine extracts only `user_messages[-1]` (single-turn;
  multi-turn history is dropped at the proxy); the engine has **no rate limit** and its live key
  (`tmc_5e13…`, compromised from a prior transcript) is still active — rotation is pending the
  owner. The `/v1` gateway authenticates before body parsing (401, not 400) with a constant-time
  master-key compare.

---

## The four orchestration implementations

| # | Implementation | Path | Runtime | Called by website? |
|---|----------------|------|---------|--------------------|
| A | Python research orchestrator (10-layer) | `src/orchestrator.py` | FastAPI via `api_server.py` (Fly) | **Yes — `/v1` Pro proxies to it (since 2026-07-17)** |
| B | Legacy Modal app | `modal_app.py` | Modal | **No** (wired but dormant — `TEMUCLAUDE_USE_MODAL_BACKEND` not set on prod; unreachable) |
| C | TS public OpenAI-compatible gateway | `website/app/v1/chat/completions/route.ts` | Vercel (Node) | **Yes — the `temuclaude` model** (Pro → engine proxy; Lite → TS cascade; TS MoA = fallback only) |
| D | TS streaming playground chat | `website/app/api/chat/route.ts` | Vercel (Node) | **Yes — playground chat** (reimplements orchestration in TS; currently behind `main`) |

**Proxy wiring (Layer 1):** `route.ts` reads `TEMUCLAUDE_ENGINE_URL` + `TEMUCLAUDE_ENGINE_API_KEY`
and, for Pro models, forwards the completion to `${engineUrl}/v1/chat/completions` on Fly, passing
through the engine's UUID id. On any engine failure it falls back to a **single fast GLM call**
(never the full ~210s TS MoA), then 503. Lite bypasses the proxy (its own cost contract). Verified
on prod 2026-07-17: trivial + hard Pro return 41-char `chatcmpl-{uuid4().hex}` ids (engine
signature); Lite returns 22-char `chatcmpl-{Date.now()}` ids (TS cascade).

---

## C — Live public gateway (`/v1/chat/completions`, the `temuclaude` model)

This is the OpenAI-compatible endpoint website users and API clients call. **Since 2026-07-17,
Pro completions are proxied to the Python engine on Fly** (`TEMUCLAUDE_ENGINE_URL`), which runs
its own adaptive pipeline (Layer 2): trivial/medium → fast tier-dispatch path; hard → the full
gauntlet (MCTS, 10-sample self-consistency, generator-discriminator self-play, shepherding,
Nemotron QA gate, Z3/SMT, sandboxed code execution). The TS pipeline below is the **fallback**
used only when the engine is unreachable (a single fast GLM call) — not the primary Pro path.

The TS gateway's own pipeline (fallback / Lite):

1. **Classify** — `classify()` → `trivial` | `medium` | `hard`.
2. **Route** — Pro trivial → GLM quality floor; every nontrivial Pro request → full
   frontier/specialist MoA panel. DeepSeek V4 Flash is reserved for Lite or explicit savings routes.
3. **MoA fusion** — `aggregate()` blends a multi-model panel (`moa-fusion`).
4. **Self-consistency** — 3 samples + majority vote for math/reasoning.
5. **QA gate** — an **independent verifier model (Nemotron 3 Ultra, paid)** scores the answer
   (LLM-as-judge). The engine additionally applies Z3/SymPy/sandbox for hard Pro — the TS fallback does not.
6. **Reflexion** — if the QA gate flags issues, a corrective re-draft.
7. **Frontier adjudication** — frontier models propose in the initial panel and re-enter corrective escalation after a low QA score.

The Pro role matrix is explicit: GLM plans and synthesizes; DeepSeek owns the
hard technical core; Kimi owns coding-driven UI/UX implementation; MiniMax
reviews multimodal/product/long-context concerns; Gemini reviews visual UI and
accessibility; Luna provides a fast independent GPT-family proposal; Sol is the
frontier adjudicator; Grok finds and repairs code failures; Nemotron verifies.
Lite applies the same draft/synthesize/verify pattern inside its smaller
DeepSeek/Qwen/Nemotron allowlist.

`pipeline = ['moa-fusion', 'self-consistency', 'aggregation', 'qa-gate', 'reflexion', 'frontier-fallback']`

**No web-search stage** in this route.

## D — Streaming playground chat (`/api/chat`)

A richer, streaming pipeline used by the playground. Notably it **does** include a web-search
stage (`webSearch(query, 3)` for `knowledge`/`reasoning`/`creative` tasks, "LAYER 0: WEB SEARCH")
plus MoA 3-layer, self-consistency, code-verification layers, QA gate, reflexion, budget
forcing, and frontier escalation. Several "Z3/SMT" and code-verification layer comments exist
here, but verification is LLM-based; treat the layer labels as descriptive, not as proof of
solver/sandbox execution.

## A — Python orchestrator (`src/orchestrator.py`)

The full research engine. It **does** implement: Z3/SMT logical verification
(`verify_logical_with_z3`), sandboxed code execution (`verify_with_code`), MCTS / generator-
discriminator self-play (`MCTSReasoningSearch`, `generator_discriminator_loop`), shepherding,
budget forcing, GEPA prompt evolution, skills, etc. It is served by `api_server.py`
(FastAPI: `/health`, `/v1/models`, `/v1/chat/completions`) on Fly.

**Caveat:** since 2026-07-17, the `/v1` Pro gateway **does** proxy hard Pro queries to this
engine, so these capabilities reach `/v1` Pro users for hard queries. Trivial/medium Pro take the
engine's fast path (no gauntlet); Lite and the playground do not reach the engine.

---

## `src/` module wiring map

### Wired into the production Python orchestrator (`src/orchestrator.py` import set)
`models`, `logger`, `fusion`, `consistency`, `verifier`, `self_qa`, `skills_loader`,
`adaptive`, `gepa`, `tot`, `debate`, `skill_curator`, `pareto_tracker`, `preference_router`,
`step_telemetry`, `shepherding`, `ui_ux`, `cache`, `reasoning_tree`, `model_profiles`,
`memory_bank_v2` (lazy). `api_server.py` additionally imports `security_pipeline`.

### Not wired into any Python runtime (test-only / research; `prod_importers == 0`)
These modules are imported **only by tests**, never by `orchestrator.py`, `api_server.py`, or
`modal_app.py`:

`benchmark_promotion`, `browser`, `citation`, `code_executor`, `context_compression`,
`copyright_check`, `deep_research`, `evenhandedness`, `github_integration`,
`meta_orchestrator`, `prompt_engine`, `safety`, `self_moa`, `sequential_thinking`,
`team_reasoning`, `time_utils`, `tone`, `unified_routing`, `vision`, `web_search`.

Notes:
- **`web_search` is not wired into the Python orchestrator.** (Web search *is* used by the TS
  `/api/chat` streaming route, via `webSearch()`, but not by the public `/v1` gateway and not
  by the Python engine.)
- **`code_executor` is not wired into the orchestrator** — the wired code-verification path is
  `verifier.verify_with_code`. `code_executor` is an alternative/sandbox implementation
  exercised only by its own tests.
- Several of these (`deep_research`, `web_search`, `self_moa`, `sequential_thinking`,
  `team_reasoning`, `vision`, `tot`, `debate`) are techniques named in `BEAT-HLE-HONEST.md` —
  i.e. active research, not stale code.

---

## Cleanup decision (conservative)

**No `src/` modules were deleted.** Rationale:

- A module is "genuinely dead" only if it has **zero importers anywhere** (production *and*
  tests). The only such file is `__init__.py` (the package marker — must keep).
- Every other module is at least test-imported; deleting it would break the test suite and
  remove research code.
- `modal_app.py` is unreferenced by anything, but is **kept by prior decision**.

**Recommended follow-up (owner's call):** review the `prod_importers == 0` list above. Any
module you want to retire must be deleted **together with its tests**; otherwise the suite
breaks. This was intentionally left to the owner because it is a content/research decision,
not a mechanical one.

---

## How to keep this honest

- Public website copy must describe **C and D** (the TS gateways users actually hit), not A.
- Z3 / SymPy / sandbox / MCTS / self-play are **live** for **hard Pro queries via `/v1`** (the
  gateway proxies to the engine since 2026-07-17). They are **not** live for trivial/medium Pro,
  Lite, or the playground — claims must scope them to "hard Pro queries."
- Benchmark scores are **projected, not measured** (see `BEAT-HLE-HONEST.md` and the
  `/docs#projected-scores` page). Do not present them as verified.
