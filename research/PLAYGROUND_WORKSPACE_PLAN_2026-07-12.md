# TemuClaude Upgrade Plan: Creative Agent Workspace

## Research inputs

- OpenAI Codex use cases — coding tasks combine a workspace, tools, testing, previews, and deployable results.
  https://developers.openai.com/codex/use-cases
- Claude Code CLI reference — users need explicit permission modes, resumable work, and bounded agent turns.
  https://docs.anthropic.com/en/docs/claude-code/cli-usage
- Hermes Agent tools — useful patterns are persistent projects, tools, skills, memory, browser control, and delegated tasks.
  https://hermes-agent.nousresearch.com/docs/reference/tools-reference/
- E2B sandbox documentation — untrusted builds need isolated, short-lived microVMs with file and preview support.
  https://e2b.dev/
- Vercel deployment documentation — Git-backed preview URLs should be separate from production promotion.
  https://vercel.com/docs/git/vercel-for-github
- Obsidian Vault API — vault notes can be searched and edited through an opt-in local connector.
  https://docs.obsidian.md/Plugins/Vault

## Objective

Make TemuClaude the best place to turn an idea into a tested, downloadable, and reviewable result while keeping every risky action visible and permissioned.

Success is measured by:

- 95% of approved build jobs produce a preview or a clear build error.
- 99% of sandbox jobs are isolated from product credentials and other users.
- A user can download every generated project as a ZIP and every single-file HTML result directly.
- Preview, test, model, tool, file, and deployment events are recorded per project.
- Lite build jobs stay within a stated budget; Pro agent jobs show an estimate before expensive steps.

## Product decisions

### Keep now

- Chat history, pinned chats, work log, Pro/Lite switch, model cost display, direct code delivery.
- Single-file HTML download and the sandboxed in-browser preview.
- Existing image, video, and audio orchestration modules as back-end capabilities, not unverified Playground promises.

### Add next

1. **Projects and artifacts**
   - A project has files, versions, generated media, chat history, and a durable activity timeline.
   - Use a file tree and side-by-side preview/diff view, not a second chat transcript.
   - Store immutable artifact versions and provide ZIP download.

2. **Sandbox build and preview**
   - Run user and model code in one short-lived sandbox per project revision.
   - Static HTML previews use the current iframe path.
   - React, Node, and full-stack previews use a sandbox URL behind an authenticated proxy; no user secrets enter the sandbox by default.
   - Limit CPU, memory, disk, time, output, package installs, and network egress. Destroy sandboxes after inactivity.

3. **Agent workspace**
   - One coordinator plans work; specialist agents receive only the files and tools needed for their task.
   - Roles: product planner, UI builder, application engineer, test runner, reviewer, and release agent.
   - The user approves any command, package install, external connection, Git operation, or deployment according to the selected permission mode.
   - Show concise completed work by default; expandable rows show commands, files changed, tests, cost, and model used.

4. **Build, test, and deployment flow**
   - Create a preview branch or isolated artifact first.
   - Run tests and browser checks before a preview is offered.
   - Provide a visible Deploy action; never publish or connect GitHub/Vercel without an explicit user approval.
   - Use Vercel preview deployments for Git-backed projects. Production promotion is a separate approval.

5. **Media and multimodal work**
   - Add image, video, music, and voice jobs as first-class artifacts with their source prompt, provider, cost, status, and download URL.
   - Start in shadow mode against the existing media orchestrators. Do not expose a media control until provider credentials, queueing, retention, and cost caps are tested.

6. **Obsidian and user memory**
   - Do not copy a vault to TemuClaude by default.
   - Ship an opt-in Obsidian plugin or local MCP connector with a read-only search mode first.
   - Let users choose folders and notes per project, show cited excerpts, and ask before writing notes back.
   - Keep user memory separate from model training and make deletion/export obvious.

## Implementation phases

1. **Artifact foundation**
   - Add project, artifact, revision, file, job, tool-event, and preview records in Supabase.
   - Add authorization rules so project files and logs are private to their owner.
   - Add a migration, API tests, and a project sidebar.

2. **Safe previews**
   - Keep iframe previews for standalone HTML.
   - Add a sandbox provider interface and a disabled-by-default E2B-compatible runner.
   - Add a signed preview proxy, short expiry, no product secrets, sandbox budgets, and a kill switch.

3. **Agent execution**
   - Add a task graph with a coordinator and limited specialist workers.
   - Add permission prompts, command allowlists, cancellation, resumable jobs, structured telemetry, and cost caps.
   - Run the coordinator in shadow mode before it can modify project files.

4. **Git and deployment**
   - Add GitHub OAuth scopes only when the user connects a repository.
   - Create branches and Vercel Preview URLs after explicit approval.
   - Require a separate approval for production deployment and preserve rollback metadata.

5. **Media, Obsidian, and evaluations**
   - Connect the existing media pipeline through queued jobs and artifact storage.
   - Add the read-only Obsidian connector.
   - Publish an evaluation suite covering web apps, games, API services, media jobs, cost, security, and failure recovery.

## Original game test

Create an original project called **Signal Lost: Fluorescent Maze**. It may use the broad liminal-space horror genre but must not use Escape the Backrooms names, levels, code, artwork, sounds, characters, or claims of equivalence.

The acceptance test is practical: an HTML game loads in the Preview panel, supports keyboard play, includes a restart path, is downloadable, and passes an automated browser smoke test. Visual quality should be judged against an internal rubric for lighting, frame rate, controls, audio, and player clarity—not against a commercial game.

## Rollback plan

- `PLAYGROUND_SANDBOX_ENABLED=false` disables container previews and agents.
- `PLAYGROUND_DEPLOY_ENABLED=false` disables Git/Vercel actions.
- `PLAYGROUND_MEDIA_ENABLED=false` keeps media jobs internal.
- The existing static HTML preview remains available as the safe fallback.
- Disable a model route when provider model mismatch, sandbox failure rate, or cost cap breach crosses the configured threshold.

## Verification plan

- Unit tests for project access, file limits, artifact versioning, signed preview URLs, and permission gates.
- Integration tests that build a static game, a React app, and a small API service in separate sandboxes.
- Browser tests for preview, stop, retry, download, delete, and deploy approval flows.
- Security checks for sandbox isolation, secret redaction, path traversal, archive safety, egress limits, and cross-user access.
- Cost and latency dashboards by model, project, tool, and job type.

## Release criteria

- No preview executes with TemuClaude, Vercel, GitHub, or provider secrets inside it.
- Every external action is permissioned, logged, and reversible where possible.
- Every user-visible result has download/export support and a clear failure state.
- Sandbox preview and deploy claims are made only after end-to-end tests pass in production-like infrastructure.
