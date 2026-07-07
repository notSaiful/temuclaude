---
name: autonomous-cybersecurity-system
description: "Research, design, and build autonomous AI-powered cybersecurity systems with self-improving Red-Blue attack-defense loops. Covers frontier model cyber capabilities (Claude Mythos, XBOW, AISLE), autonomous pentesting ecosystems, vulnerability detection pipelines, exploit chain construction, and the architecture for a system that attacks itself, patches what it finds, and escalates attacks over time. Use when the user asks about AI cybersecurity, code scanning, vulnerability detection, red teaming, penetration testing, self-healing code, or building a self-improving cyber defense system."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cybersecurity, autonomous, red-team, blue-team, vulnerability-detection, self-improving, ai-security, pentesting]
    related_skills: [deep-research-mode, research-swarm-orchestration, continuous-research-swarm, safety-hardening, system-prompt-analysis]
---

# Autonomous Cybersecurity System

Research, design, and build autonomous AI-powered cybersecurity systems that surpass frontier model capabilities through self-improving Red-Blue loops.

## When to Load This Skill

- User asks about AI cybersecurity capabilities, Claude Mythos, or frontier model security
- User wants to build a code scanner, vulnerability detector, or autonomous pentesting system
- User wants a self-attacking, self-patching, self-improving cyber defense system
- User mentions red team / blue team, exploit chains, CTF, ROP, sandbox escapes
- User wants to compare their model's cybersecurity abilities against frontier models
- User asks about autonomous hacking agents, XBOW, AISLE, or similar systems

## The Core Insight: The Moat Is the System, Not the Model

AISLE (autonomous security analyzer, 180+ CVEs across 30+ projects) tested Claude Mythos's showcase vulnerabilities on small open-weight models and found that 3.6B-parameter models costing $0.11/M tokens recovered the same analysis. Cybersecurity capability is "jagged" — it does not scale linearly with model size, and there is no stable best model across tasks. The competitive advantage comes from the scaffolding (agent harness, memory, feedback loops, escalation engine), not the base model weights. This means a well-architected system using free/cheap models can match or exceed a frontier model that lacks the same system architecture.

## Claude Mythos — What to Beat

Claude Mythos Preview (Anthropic, Apr 7 2026) is the current frontier. Key metrics:
- 73% success on expert-level CTFs (AISI evaluation)
- First model to solve a 32-step corporate network attack end-to-end (3/10 attempts)
- 10,000+ high/critical vulnerabilities found via Project Glasswing
- 83% first-attempt exploit reproduction rate
- Found 27-year-old OpenBSD bug, 16-year-old FFmpeg bug, FreeBSD NFS 20-gadget ROP chain
- 1M token context, 128k max output, $10/M input, $50/M output

Mythos's critical limitation: it is a STATIC model. It does not learn from its discoveries. Each engagement starts from scratch. No memory, no feedback loop, no self-improvement. This is the gap to exploit.

## The Self-Improving Red-Blue Loop Architecture

Five layers operating in a continuous cycle:

1. **Offensive Swarm** — Hundreds of parallel attack agents, each specialized for a vulnerability class (memory corruption, injection, auth bypass, privesc, sandbox escape, supply chain, logic flaws). All share findings through central memory. Parallelization, not sophistication alone, is what changes economics (Hadrian: 70+ AI pentesting tools, Excalibur compromised 4/5 AD hosts for $28.50).

2. **Defensive Shield** — Agents receive vulnerability reports, generate patches, verify patches against the original exploit, deploy to staging.

3. **Verification Loop** — Offensive swarm re-attacks patched code to find bypasses or adjacent vulnerabilities exposed by the patch.

4. **Knowledge Distillation** — Every finding, patch, bypass, and failure converted to structured data: detection rules, exploit patterns, prompt improvements, fine-tuning examples. Neuro-symbolic approach (LLMxCPG, QRS) converts discoveries into permanent reusable rules.

5. **Capability Upgrade** — Distilled knowledge fed back into agents via prompt updates, tool enhancements, model fine-tuning. Raises baseline for next cycle.

## Escalation Engine (Critical Design)

Escalation happens on three axes, GATED BY DEFENSIVE SUCCESS (not time):
- **Technique**: basic bugs → complex chains (ROP, JIT spray, sandbox escape)
- **Scope**: single-function → cross-module → cross-service → supply chain
- **Autonomy**: shadow → assisted → bounded → full (Mayoral Vilches Level 1-5 taxonomy)

NEVER escalate offense before defense has mastered the current level. Otherwise the system creates vulnerabilities faster than it can patch them.

## Shared Memory (Context Lake)

All agents query a central memory in real time. Stores:
- Vulnerability signatures (pattern, exploit, proof, patch, verification status)
- Attack chains (how low-severity bugs combine into critical exploits)
- False positive patterns (dead ends to avoid)
- Defensive coverage maps (MITRE ATT&CK per technique: detectable? exploitable? defended?)
- Model performance records (which model best on which task → dynamic routing)
- Environment fingerprints (codebase characteristics → pattern transfer)

## Free-Model Economic Strategy

Use tiered model strategy to minimize cost:
- Free/cheap small models (3.6B-7B) for broad-spectrum scanning and triage (high volume, $0.11/M tokens)
- Mid-tier models for detailed analysis and exploit construction
- Frontier models only for complex exploit chain construction and novel vulnerability discovery

LLM orchestration (combining multiple cheap models) can match frontier model performance at 5-15% cost. Different models excel at different tasks — route dynamically based on historical performance data.

## Safety Architecture

A system that autonomously finds and exploits vulnerabilities is itself a weapon. Required controls:
- **Scope enforcement**: all operations bounded to authorized targets, violations trigger shutdown
- **Proof containment**: exploits generated in isolated sandboxes, no network access
- **Decision logging**: every agent decision in immutable audit log
- **Human override**: every action overridable, override feeds back as training signal
- **Graduated deployment**: shadow → assisted → autonomous, per skill per environment
- **AI-on-AI red teaming**: the security system itself must be regularly attacked by a separate red team agent (prompt injection, tool misuse, memory poisoning, model supply chain attacks)

## Frameworks and Standards

- NIST AI RMF
- OWASP Top 10 for LLM Applications (2025)
- OWASP Top 10 for Agentic Applications (2026)
- MITRE ATLAS (adversarial threat landscape for AI)
- CSA Agentic AI Red Teaming
- Microsoft Agentic Failure-Mode Taxonomy v2.0
- DARPA AI Cyber Challenge
- Mayoral Vilches 6-level AI pentesting autonomy taxonomy

## Existing Systems to Study

- **XBOW** — #1 on HackerOne, 14,000+ zero days, multi-agent coordinator/executor architecture
- **AISLE** — model-agnostic pipeline, 180+ CVEs, decomposes cyber into 5 modular tasks
- **Simbian** — Red+Blue share one memory (Context Lake), MITRE coverage 33%→83% in 90 days
- **Cloudflare** — tested Mythos on 50+ repos, found exploit chain construction is the key differentiator
- **Hadrian** — cataloged 70 AI offensive tools in 18 months, parallelization changes economics

## Integration with Existing Swarm

The Temuclaude research swarm infrastructure (daemon-based, self-healing coordinator) can be extended for cybersecurity. Scouts → vulnerability scanners, rankers → severity triagers, auto-integrator → patch generator, coordinator → Red-Blue cycle manager. Daemon-based is superior to cron for long-running stateful cyber operations.

## LLM Defense in Depth (6-Layer Architecture)

Beyond the offensive Red-Blue loop, the system must DEFEND ITSELF against attacks from other models (Mythos, GPT-5, Gemini attacking simultaneously). This requires a 6-layer defense-in-depth architecture around the LLM:

1. **Guard** — Input sanitization (strip zero-width chars, control chars, unicode homoglyphs), injection detection (16 attack patterns + typoglycemia + encoding detection), canary tokens (embed in system prompt, detect leakage in output), SmoothLLM perturbation
2. **Taint Tracking** — Mark external content as tainted, never let it enter the instruction channel, quarantine sources with repeated injection patterns
3. **Adaptive Honeypot** — Generate fake secrets/endpoints/vulnerabilities, lure attackers into traps, collect intelligence on techniques, share with all defense layers
4. **Counter-Attack** — Fingerprint attacks (pattern hash, technique, source signature), adapt defenses in real-time, detect swarm attacks (10+ in 5 min → counter-attack mode)
5. **Output Firewall** — Detect/redact secrets (API keys, JWT, private keys), PII (emails, phones, SSNs, credit cards), canary token leakage, system prompt content. Block if too many secrets leaked.
6. **Virtual Chamber** — Network-enforced isolation per session, least-privilege tool permissions, rate limiting, auto-quarantine after violations. "An enclave enforces what it CANNOT reach."

The core principle from tldrsec: "Assume prompt injection will succeed. Design every layer to limit the damage." No single defense works — every layer must assume the previous was bypassed.

Built and tested at `/Users/saiful/temuclaude/`: 7 modules (guard, taint_tracker, honeypot, counter_attack, output_firewall, virtual_chamber, security_pipeline), 100 new tests, 274 total passing.

## 5 World-Shaking Breakthroughs for Unbreakable Defense

1. **AI Swarm Attacks Are Real** — GTG-1002 (Nov 2025) used autonomous agents to attack 30 orgs simultaneously, 80-90% autonomous, zero victims noticed. Need agents to fight agents at machine speed.
2. **FHE for LLMs** — arXiv:2604.12168: FHE-secured Llama 3 at 98% accuracy, 80 tok/sec on consumer CPU. Prompt injection becomes mathematically impossible. Quantum-resistant.
3. **Trusted Execution Environments** — arXiv:2606.31408: CPU+GPU TEE where even K8s admin can't read the model. Remote attestation proves integrity.
4. **AI-Generated Adaptive Honeypots** — Honeypots that learn from every attack, evolve in real-time. Defense becomes active.
5. **Zero Trust Enclaves** — Virtual Chambers enforce network-level isolation. Structural security, not behavioral.

## Reference Files

- `references/claude-mythos-intelligence.md` — Compiled research findings on Claude Mythos capabilities, limitations, leaked system prompt architecture, and the autonomous cybersecurity ecosystem (27 sources, Jul 2026)
- `references/self-improving-architecture.md` — Detailed blueprint for the 5-layer self-improving Red-Blue loop, including shared memory schema, escalation gating, and free-model routing strategy
- `references/temuclaude-cyber-integration.md` — Concrete integration pattern for adding cybersecurity research to an existing daemon-based research swarm (9-step pattern, cyber daemon design, arXiv cs.CR search pattern, Startpage search fallback, verification checklist)
- `references/llm-defense-in-depth.md` — The 6-layer LLM defense architecture (guard, taint tracking, honeypot, counter-attack, output firewall, virtual chamber) with implementation details, attack taxonomy, and the 5 breakthroughs for unbreakable defense. Built and tested: 7 modules, 100 tests at `/Users/saiful/temuclaude/`

## Pitfalls

- **Do NOT use DuckDuckGo/Bing/Google for programmatic search** — all serve CAPTCHAs as of Jul 2026. Use Startpage POST endpoint instead (see `deep-research-mode` skill's fallback search reference).
- **Do NOT escalate offensive techniques before defense has mastered current level** — this creates an unpatchable vulnerability backlog.
- **Do NOT rely on a single model for all cyber tasks** — capability is jagged, different models excel at different tasks. Use dynamic routing based on historical performance.
- **Do NOT skip the verification loop** — a patch that passes tests but is semantically incorrect (test overfitting) is worse than no patch because it creates false confidence.
- **Do NOT deploy autonomous exploitation without scope enforcement** — an autonomous attack agent without hard scope boundaries is a liability.

## Maintenance

Update when:
- New frontier cybersecurity models are released (Mythos successors, competing models)
- New autonomous attack tools or architectures emerge
- The self-improving system is built and produces cycle metrics
- Frameworks/standards are updated (OWASP, MITRE ATLAS, etc.)
- User feedback identifies gaps in the architecture