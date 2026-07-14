# TemuClaude Architecture

> Purpose: TemuClaude has **several independent orchestration implementations** that share a
> brand and architecture concepts but are **separate codepaths**. This document maps them,
> identifies which one website users actually hit, and records what is wired vs. not wired —
> so claims about capabilities match reality (see the project's truthfulness / sidq principle).

## TL;DR

- The **website (Vercel)** runs two TypeScript gateways. Website users hit these, **not** the
  Python orchestrator.
- The **Python orchestrator** (`src/orchestrator.py`) is a separate, richer 10-layer engine
  served by `api_server.py` (FastAPI, Fly). The website **does not call it** — the TS routes
  reimplement orchestration standalone.
- Therefore features that exist only in the Python engine (Z3/SMT, sandboxed code execution,
  MCTS / self-play, shepherding) are **not** experienced by website users. Public copy must not
  claim them as live website features. (The live website gateway verifies with an
  **LLM-as-judge** — the Nemotron 3 Ultra QA gate — not Z3/SymPy/sandbox.)
- `modal_app.py` is an unreferenced legacy entrypoint, **kept by decision** (not removed).
- **No `src/` modules were deleted** in the conservative cleanup — nothing is genuinely dead
  (every module is at least test-imported). See [Cleanup decision](#cleanup-decision).

---

## The four orchestration implementations

| # | Implementation | Path | Runtime | Called by website? |
|---|----------------|------|---------|--------------------|
| A | Python research orchestrator (10-layer) | `src/orchestrator.py` | FastAPI via `api_server.py` (Fly) | **No** |
| B | Legacy Modal app | `modal_app.py` | Modal | **No** (unreferenced; kept by decision) |
| C | TS public OpenAI-compatible gateway | `website/app/v1/chat/completions/route.ts` | Vercel (Node) | **Yes — this is the `temuclaude` model** |
| D | TS streaming playground chat | `website/app/api/chat/route.ts` | Vercel (Node) | **Yes — playground chat** |

**Verification of separation:** searching the website gateway code (`website/app/v1`,
`website/app/api/chat`, `website/lib`) for any reference to the Python backend
(`fly.io`, `api_server`, `FLY_*`, `BACKEND_URL`, etc.) returns **nothing**. The TS routes
do not proxy to the Python engine; they reimplement orchestration in TypeScript.

---

## C — Live public gateway (`/v1/chat/completions`, the `temuclaude` model)

This is the OpenAI-compatible endpoint website users and API clients call. Its pipeline
(from the route's own `pipeline` array and function inventory):

1. **Classify** — `classify()` → `trivial` | `medium` | `hard`.
2. **Route** — trivial → DeepSeek V4 Flash (single cheap model); medium → a single strong
   specialist; hard → full MoA panel.
3. **MoA fusion** — `aggregate()` blends a multi-model panel (`moa-fusion`).
4. **Self-consistency** — 3 samples + majority vote for math/reasoning.
5. **QA gate** — an **independent verifier model (Nemotron 3 Ultra)** scores the answer
   (LLM-as-judge, *not* Z3/SymPy/sandbox execution).
6. **Reflexion** — if the QA gate flags issues, a corrective re-draft.
7. **Frontier fallback** — escalation only on verified failure.

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

**Caveat:** because the website does not call this engine, these capabilities do not reach
website users via the Vercel gateway. They are real in the Python runtime, not in the
website runtime.

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
- Any claim of Z3 / SymPy / sandbox / MCTS / self-play as a *live website* feature is
  inaccurate unless/until the website gateway proxies to the Python engine — which it
  currently does not.
- Benchmark scores are **projected, not measured** (see `BEAT-HLE-HONEST.md` and the
  `/docs#projected-scores` page). Do not present them as verified.