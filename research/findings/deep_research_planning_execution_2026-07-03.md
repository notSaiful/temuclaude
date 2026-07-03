# Deep Research: How the Best AI Agents, Software Teams, and Engineering Organizations Plan and Execute

## Research Date: 2026-07-03
## Source: Research Agent 2 (deleg_733a6e91)

---

## 1. HOW THE BEST AI AGENTS PLAN

### Claude Code
- Plugin-based workflows: feature-dev plugin uses 7-phase approach with specialized agents (code-explorer, code-architect, code-reviewer)
- Parallel agent review: code-review plugin runs 5 parallel Sonnet agents for compliance, bugs, context, PR history, comments
- Iterative loops: ralph-wiggum plugin enables self-referential loops until completion
- CLAUDE.md: context file shaping every conversation
- Pattern: Decompose → Design (specialized agents) → Execute → Review (parallel) → Iterate

### Hermes Agent
- /plan skill: writes markdown plan instead of executing immediately, saves to .hermes/plans/
- Progressive disclosure: 3-level loading (list ~3k tokens → view → reference)
- Self-improvement loop: creates skills from experience after complex tasks
- Skill bundles: group multiple skills under one slash command
- Memory: persistent across sessions with FTS5 recall
- Delegation: spawn isolated subagents for parallel workstreams
- Pattern: Plan first → Progressive disclosure → Execute → Learn (save skills) → Reuse

### What Makes Some Agents Better at Planning
1. Plan-first workflow (write plan before executing)
2. Progressive disclosure (load only what's needed)
3. Self-improvement (save learned procedures as skills)
4. Parallel review (multiple agents review from different angles)
5. Context management (maintain context without overflowing)
6. Iterative refinement (work same task repeatedly until done)
7. Verification loops (verify each step before proceeding)

---

## 2. SOFTWARE ENGINEERING PLANNING

### Design Docs at Google (Malte Ubl)
- Informal documents created BEFORE coding
- Document high-level implementation strategy and key design decisions with trade-offs
- "Our job is not to produce code per se, but rather to solve problems"

Structure:
1. Context and scope
2. Goals and non-goals (explicitly excluded items)
3. The actual design (overview then details, focus on trade-offs)
4. System-context diagram
5. APIs (sketch, don't formalize)
6. Data storage (rough form)
7. Degree of constraint (greenfield vs legacy)
8. Alternatives considered (most important section)
9. Cross-cutting concerns (security, privacy, observability)

Lifecycle: Creation → Review → Implementation & iteration → Maintenance

When NOT to write: obvious solutions, implementation manuals, rapid prototyping
Length: 10-20 pages for large projects, 1-3 pages for incremental

### Architecture Decision Records (ADRs)
- Capture ONE architectural decision: context, decision, consequences
- 1-2 pages, immutable once decided, stored in version control
- Format: Title → Status → Context → Decision → Consequences

---

## 3. PLANNING ANTI-PATTERNS

### Planning Fallacy
- Kahneman & Tversky: people estimate best-case, not realistic
- Software estimates off by 2-4x on average
- LLMs similarly exhibit optimism bias
- Fix: Reference class forecasting, add 2-4x buffer, decompose into smaller tasks

### Scope Creep Prevention
- Explicit non-goals
- Time-box (reduce scope, not extend time)
- Change control (scope additions require explicit acknowledgment)
- MVP-first

### Plan Then Ignore
- Cause: plan too detailed too early
- Fix: Rolling wave planning (near-term detailed, far-term outline)
- Fix: Treat plan as living document, update when reality differs
- Fix: Plan checkpoints at each milestone

---

## 4. EXECUTION DISCIPLINE

### Progressive Elaboration
Plans get more detailed as you learn more. Start high-level, add detail to current phase, keep future as outlines.

### Rolling Wave Planning
- Near-term: detailed (specific tasks, acceptance criteria)
- Mid-term: moderate detail (phases, rough tasks)
- Far-term: outline only (direction, not specifics)
- Replan next wave as you complete current one

### Turning Plans Into Action
1. Write plan to a file
2. Check plan before each work session
3. Track progress against plan
4. Update plan when reality differs
5. Use plan as checkpoint at milestones

### Effectiveness vs Efficiency
- Effectiveness (doing the right thing) > Efficiency (doing things right)
- Verify you're solving the right problem before optimizing the solution

---

## 5. REVIEW AND VERIFICATION

### Code Review Best Practices
Google: Every change requires review. Small changes (200 lines or less). LGTM culture.
Meta: Pre-commit review. Static analysis before human review.
Claude Code: 5 parallel agents (compliance, bugs, context, PR history, comments) with confidence scoring.

### Self-Review Checklist
1. Does it work? — Run it, don't assume
2. Does it handle edge cases? — Empty inputs, null values, concurrent access
3. Are there tests? — Unit + integration
4. Is it documented?
5. Does it handle errors gracefully?
6. Are there security implications?
7. Does it follow conventions?
8. What did you NOT do? — Explicitly list deferred items
9. What could break? — Pre-mortem
10. Is the definition of done met?

### Finding ALL Missing Pieces
- Checklist-driven review (fixed checklist, not memory)
- Pre-mortem: "Imagine this failed. What went wrong?"
- Adversarial review: try to break it
- Coverage analysis: what paths are NOT tested?
- Inversion: "What would I be embarrassed about if someone reviewed this?"
- Multi-angle review: security, performance, user, maintainer

### Definition of Done
□ Code written and follows conventions
□ Unit tests pass (>80% coverage of new code)
□ Integration tests pass
□ Code reviewed
□ Documentation updated
□ No known critical bugs
□ Deployed to staging and verified
□ Acceptance criteria met and confirmed

---

## 6. KNOWLEDGE STRUCTUREING FOR REUSE

### Formats
| Format | Best For | Scope |
|--------|----------|-------|
| Skill (SKILL.md) | Agent-reusable procedures | Procedural, with triggers and verification |
| Runbook | Operational procedures | Single task, prescriptive |
| Playbook | Scenario responses | Multi-step with decision points |
| SOP | Compliance procedures | Formal, regulated |
| ADR | Architectural decisions | Single decision, immutable |
| Design doc | Project planning | Full project, living document |

### Building Knowledge That Compounds
1. Capture during work, not after
2. Progressive disclosure (index → summary → full)
3. Make it searchable
4. Version it
5. Categorize
6. Link to real examples
7. Include verification steps
8. Include pitfalls
9. Review periodically
10. Share via hub

---

## 7. DECISION-MAKING FRAMEWORKS

### RACI / RAPID / DACI
- RACI: Responsible, Accountable, Consulted, Informed
- RAPID: Recommend, Agree, Perform, Input, Decide
- DACI: Driver, Approver, Contributor, Informed
- For AI: explicitly separate roles — "As Recommender..." "As Decider..." "As Performer..."

### OODA Loop
Observe → Orient → Decide → Act → Loop
- Speed of iteration > perfection of each step
- For AI: Observe (read state) → Orient (understand problem) → Decide (plan) → Act (implement) → Loop (verify)

### First Principles Thinking
1. Identify the problem
2. Strip away assumptions
3. Find the fundamentals (irreducible truths)
4. Build up from there

### Inversion
- "How would this fail?" instead of "how do I succeed?"
- Pre-mortem before starting: imagine failure, then prevent each mode

---

## 8. MAKING THE AGENT SMARTER

### What Differentiates Great Agents
1. Learning loop (creates skills from experience)
2. Progressive disclosure (load only what's needed)
3. Plan-first workflows (write plan before executing)
4. Parallel execution (subagents for parallel work)
5. Memory system (persistent across sessions)
6. Tool ecosystem (rich integration)
7. Context files (project context shapes conversations)
8. Self-correction (save corrections as skills)

### When to Think vs Act Fast
Think step-by-step when: novel/complex, designing, high error cost, multi-step, debugging
Act fast when: well-understood (have skill), low error cost, iterating on feedback, have clear plan
Balance: Plan deeply, execute fast. Re-plan when hitting unknowns.

### 20 Practical Steps the Agent Can Take RIGHT NOW
1. Use /plan before any complex task
2. Save skills from every non-trivial task (5+ tool calls with success)
3. Use progressive disclosure (don't load everything)
4. Apply 2-4x estimation multiplier
5. Write explicit non-goals in every plan
6. Run a pre-mortem before completing
7. Use the self-review checklist before marking done
8. Write ADRs for architectural decisions
9. Create skill bundles for recurring multi-skill workflows
10. Re-read your own skills periodically
11. Track actual vs estimated time
12. Use OODA loop for fast iteration
13. Use inversion for risk management
14. Delegate to subagents for parallel work
15. Update plans when reality differs
16. Document alternatives considered
17. Use reference class forecasting
18. Review from multiple angles (security, performance, user, maintainer)
19. Include verification steps in skills
20. Include pitfalls in skills