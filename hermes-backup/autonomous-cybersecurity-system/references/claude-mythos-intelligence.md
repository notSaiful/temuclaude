# Claude Mythos Intelligence — Compiled Research

From 27 sources scraped July 6, 2026. Full report at `/Users/saiful/cybersecurity-research/BEATING_MYTHOS_full_report.md`.

## Mythos Architecture

- General-purpose LLM, NOT specialized for security — cyber skills emerged from improved coding/reasoning
- 1M token context window, 128k max single-turn output
- Permanently enabled adaptive thinking
- "effort" parameter (high default, xhigh for complex)
- Fable 5 = Mythos 5 with safety guardrails (refusal on offensive cyber, bio, data extraction)
- $10/M input, $50/M output tokens
- Leaked system prompt: modular architecture (budget, claude_behavior, memory_system, persistent_storage, mcp_app_suggestions, past_chats_tools, preferences_info, memory_user_edits, computer_use, request_evaluation_checklist, search_instructions, tool_schemas, anthropic_api_in_artifacts, citation_system)

## AISI Evaluation Results

- Expert-level CTF: 73% success (no model could do these before April 2025)
- "The Last Ones" (TLO): 32-step corporate network attack — Mythos solved 3/10 end-to-end
- Completed avg 22/32 steps; Opus 4.6 completed avg 16
- Scales with token budget (up to 100M tokens tested)
- Could NOT complete OT/ICS "Cooling Tower" range (stuck on IT sections)

## Landmark Vulnerabilities Found

1. **27-year-old OpenBSD TCP SACK bug** — remote crash via signed integer overflow. Two bugs combined: (a) kernel doesn't check SACK block start is within send window, (b) NULL pointer deref when SACK block deletes only hole and appends new one. TCP sequence numbers are 32-bit and wrap around; (int)(a-b)<0 comparison overflows at 2^31 distance. Cost: under $50 for successful run, $20,000 total across codebase.

2. **16-year-old FFmpeg bug** — 1 line of code, hit by fuzzer 5M times without detection.

3. **FreeBSD NFS unauthenticated root** — 20-gadget ROP chain across 6 sequential RPC packets, ~4 hours compute.

4. **Linux kernel privilege escalation** — chained multiple vulns, user→root.

5. **Browser exploit** — chained 4 vulns, JIT heap spray escaping renderer+OS sandboxes.

6. **Firefox JS engine** — 181 working exploits + 29 register control. Opus 4.6: only 2.

7. **OSS-Fuzz corpus** — 595 tier 1-2 crashes, full control flow hijack on 10 fully-patched targets (tier 5). Previous models: zero tier 5.

8. **Project Glasswing total**: 10,000+ high/critical vulns found by 150 partner orgs.

## Mythos Limitations (AISLE Analysis)

- 3.6B-param open model ($0.11/M tokens) recovered same FreeBSD analysis
- 5.1B active model recovered OpenBSD SACK chain
- Capability is "jagged" — doesn't scale linearly with model size
- No stable "best model" across cyber tasks — rankings reshuffle per task
- The MOAT is the system/scaffolding, not the model
- Cloudflare: other frontier models found same bugs, fell short at exploit chain stitching
- Organic refusals inconsistent — same task framed differently = different outcome
- Mythos is STATIC — no learning between engagements, no memory, no feedback loop

## The Testing Scaffold Mythos Uses

1. Launch isolated container with project under test + source code
2. Invoke model, prompt to find security vulnerability
3. Model reads code → hypothesizes vulns → runs project to confirm/reject → adds debug logic → outputs bug report with PoC
4. Each agent focuses on different file (rank files 1-5 by likelihood of bugs)
5. Final agent confirms: "I have received the following bug report. Can you please confirm if it's real and interesting?"
6. Filters out minor problems, focuses on severe vulnerabilities

## Autonomous Ecosystem (70+ tools, Hadrian catalog)

- **Excalibur** (PentestGPT V2): 4/5 AD hosts compromised for $28.50
- **RapidPen**: IP-to-shell in 200-400s for $0.30-$0.60/run
- **CAI** (Alias Robotics): 156x cost reduction, 3600x faster than human ($109 vs $17,218)
- **AutoPentester**: 27pp improvement over PentestGPT
- Current autonomy: Level 3-4 (Mayoral Vilches taxonomy), Level 5 = fully unsupervised
- Parallelization (not sophistication) changes economics — AI runs recon across all subdomains/ports/services simultaneously

## Self-Improving SecOps (Simbian)

- Red + Blue share one memory (Context Lake)
- Every attack makes defense sharper
- MITRE ATT&CK coverage: 33% → 56% → 83% across 3 cycles (90 days)
- Shadow → assisted → autonomous deployment
- Every agent decision logged and overridable
- "Self-improving, not self-driving"

## Recursive Self-Improvement (CSA Report, Jun 2026)

- Anthropic: Claude writes ~80% of production code
- 8x code merge rate vs 2021-2025 baseline
- Apr 2026: 800 bug fixes in days = 4 years human engineering
- OpenAI GPT-5.3-Codex: debugged own training process
- RSI-adjacent: AI materially accelerates AI development under human supervision
- Full autonomous RSI still speculative but partial RSI is operational

## LLM Vulnerability Detection Research (2025-2026)

Key papers from Awesome-LLMs-for-Vulnerability-Detection (1.1k stars):
- VulnGym: project-level vulnerability benchmark
- VulTriage: triple-path context augmentation
- Multi-Agent harnesses for vuln discovery
- QRS: rule-synthesizing neuro-symbolic triad (LLM generates rules, symbolic engine validates, permanent additions)
- AgenticSCR: autonomous secure code review
- MulVul: retrieval-augmented multi-agent detection
- VulnLLM-R: specialized reasoning LLM with agent scaffold
- LLMxCPG: code property graph-guided detection (Usenix 2025)
- CVE-Bench: benchmarking LLM SE agents
- CLeVeR: multi-modal contrastive learning for vulnerability code representation

## RL for Cybersecurity Environments

- CSLE (Cyber Security Learning Environment)
- Continuous CyberBattleSim (Microsoft + GNNs/LLMs)
- MininetGym (SDN-based RL for cybersecurity)
- CyGym (game-theoretic RL for network defense)

## Key Frameworks

- NIST AI RMF
- OWASP Top 10 for LLM Applications (2025)
- OWASP Top 10 for Agentic Applications (2026)
- MITRE ATLAS
- CSA Agentic AI Red Teaming
- Microsoft Agentic Failure-Mode Taxonomy v2.0
- DARPA AI Cyber Challenge
- Mayoral Vilches 6-level AI pentesting autonomy taxonomy

## Sources (27 total)

AISI (aisi.gov.uk), ArmorCode, Wikipedia, Anthropic Glasswing, Anthropic News, Radware, Pluralsight, Arctic Wolf, Picus Security, CNBC, GitHub/asgeirtj (leaked prompts, 50.3k stars), GitHub/huhusmang (Awesome-LLMs-for-Vuln-Detection, 1.1k stars), GitHub/requie (AI-Red-Teaming-Guide, 330 stars), Medium/Tahir Balarabe, Cycode, XBOW, Hadrian, Cloudflare, CodeRabbit, Astra, Promptfoo, AISLE, EndorLabs, Simbian, CSA, 4sAPI, GitHub/Kim-Hammar (awesome-rl-for-cybersecurity, 1.1k stars).