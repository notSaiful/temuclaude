# TemuClaude Playground capability audit — 2026-07-12

## Evidence used

- [OpenAI Codex documentation](https://developers.openai.com/codex/) — a coding agent is most useful when work is grounded in a repository/workspace, tool use, review, and verification rather than a chat transcript alone.
- [Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage) — resumable sessions, bounded turns, workspace scope, and explicit permission modes are essential interaction patterns.
- [Hermes tools reference](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools/) — durable memory, files, terminal/browser tools, skills, delegation, and safe execution should be separately visible capabilities, not hidden claims.
- [E2B templates](https://e2b.dev/docs/template/quickstart) and [secured access](https://e2b.dev/docs/sandbox/secured-access) — prebuilt, version-pinned isolated environments and authenticated controller access are the correct base for runnable builds.
- [Obsidian Vault API](https://docs.obsidian.md/Plugins/Vault) — a vault should be accessed through a user-installed, opt-in local connector; it must not be copied to a hosted product by default.
- [Vercel Git deployments](https://vercel.com/docs/git/vercel-for-github) — previews and production promotion are distinct operations.

## Verified product state

| Capability | Current state | Release claim |
| --- | --- | --- |
| Chat, pins, delete, compact work log | Implemented; history is browser-local | Available |
| Pro/Lite composer selection | Implemented | Available |
| HTML artifact download | Implemented for complete fenced or raw HTML documents | Available |
| Same-page HTML preview | Implemented with an opaque-origin iframe and restrictive CSP | Available |
| Isolated static HTML preview | Implemented with a short-lived E2B sandbox, no sandbox internet, no product secrets | Available when E2B is configured |
| Durable project/file API | Implemented, ownership-checked, and connected to the Playground project sidebar and “Save to project” action | Available for HTML files |
| Project ZIP export | Implemented with a 100-file / 5 MB bound and traversal rejection | Available |
| Isolated saved-project preview | Implemented with a pinned E2B Node 24 template, no sandbox internet, 5-minute expiry, and a sandboxed iframe | Available for static projects and a saved `server.mjs`/`server.js` |
| Durable chat and revisions | Not implemented | Do not claim |
| React/package-install build | Not implemented | Do not claim |
| GitHub/Vercel deployment from Playground | Not implemented | Do not claim |
| Agent task graph and approvals | Not implemented | Do not claim |
| Image/video/music Playground jobs | Existing backend research only; no verified Playground job flow | Do not claim |
| Obsidian connector | Not implemented | Do not claim |

### Live infrastructure checks completed

- Static isolated HTML preview: sandbox creation, public preview health check, downloadable artifact URL, and teardown passed.
- Isolated Node-service preview: an HTML route and a local JSON API route both returned HTTP 200 from a short-lived, internet-disabled, credential-free sandbox.
- Pinned project-preview template: the E2B Node 24 template was built with one CPU and 1 GB memory; a saved project returned HTTP 200 from the isolated public preview URL and was destroyed after the test.

This provides a user-facing runnable-project path for saved static files and small Node services. It is **not** a general React/package-install builder: dependency installation, external network access, arbitrary build commands, and persistent sandbox sessions remain intentionally unavailable until their controls and cost limits are tested.

## Product decision

The goal is not an unverifiable claim that TemuClaude is “better than Codex, Claude Code, and Hermes combined.” The measurable goal is a secure, inspectable creative-agent workspace with a smaller, clearer capability set that can be proven through end-to-end tests.

Every capability must satisfy all of the following before it is advertised:

1. The result is durable in the user’s project and exportable.
2. The action has an explicit permission boundary and a visible audit event.
3. The execution environment has no TemuClaude, GitHub, Vercel, or provider secrets.
4. There is an automated success case and a deliberate failure case.
5. Cost, timeout, and cancellation behaviour are observable.

## Implementation plan

### Phase 1 — durable artifact workflow (complete)

- Link the Playground to the existing authenticated projects/files API.
- Allow generated HTML to be saved as a project file as well as downloaded.
- Record file hashes, file paths, and save events; reject traversal and files above the existing 1 MB limit.
- Keep browser-local chat history as a compatibility fallback until durable message migration is tested.

### Phase 2 — project revisions and exports

- Add immutable artifact revisions and durable chat messages in a new Supabase migration.
- Add server-side ZIP generation with strict archive/file-count/byte bounds.
- Move chats to project-backed sessions after a migration and recovery test.

### Phase 3 — runnable project sessions

- Build and pin a TemuClaude E2B template containing only the approved runtime/toolchain.
- Use per-user short-lived sandbox sessions, secure E2B access, a command allowlist, fixed disk/CPU/time/output budgets, and no product credentials.
- Start with static HTML and a local Node service template. Add package installation only after a network egress policy and a dependency allowlist are verified.

### Phase 4 — permissioned agent execution

- Add a coordinator plus bounded planner, builder, test, and reviewer workers.
- Persist an immutable task graph, tool events, model/cost data, and approvals.
- Require approval for commands outside the safe allowlist, dependency installation, network access, file write, Git operations, connector use, and deployment.

### Phase 5 — integrations

- GitHub/Vercel: create preview branches and preview deployments only after explicit approval; require a separate production promotion approval.
- Obsidian: release a read-only local connector first, scoped to user-selected folders/notes with cited excerpts; writes need a second approval.
- Media: expose image/video/music as queued, budgeted artifacts only after the existing providers, retention, and download flows pass end-to-end tests.

## Original game evaluation

`Signal Lost: Fluorescent Maze` is the official original demo. It can be evaluated for load time, keyboard controls, restart, asset-free portability, download, and preview isolation. It must not be presented as a recreation, comparison, or substitute for *Escape the Backrooms*.

## Release gates

- A “runnable project” badge requires a successful build, preview health check, test report, and downloadable artifact.
- A “deploy” button remains absent until the explicit approval and Git/Vercel flows exist.
- A connector stays unavailable until its least-privilege, consent, delete/export, and recovery cases are tested.
- Any failing security, cost, or ownership test disables the affected feature behind a server-side flag.
