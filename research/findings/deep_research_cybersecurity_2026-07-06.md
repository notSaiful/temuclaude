# Deep Research: Full-Stack Cybersecurity for Temuclaude

## Executive Summary

This report synthesizes research from arXiv (cs.CR), OWASP, AISI, Anthropic, NDSS, IBM, HiddenLayer, and the autonomous-cybersecurity-system skill to produce a comprehensive, full-stack cybersecurity defense and offense strategy for Temuclaude. The core insight from the literature is that cybersecurity capability does not scale linearly with model size — a well-architected system using free or cheap models can match or exceed a frontier model that lacks the same system architecture {cite index="0-0:2"}. The competitive moat is the scaffolding: guardrails, shared memory, feedback loops, escalation gating, and continuous self-healing, not the base model weights. Temuclaude's existing daemon-based research swarm provides the ideal substrate for extending into a 24/7 cybersecurity research and defense system.

## Section 1: The Threat Landscape

### 1.1 Claude Mythos and the Frontier

Anthropic's Claude Mythos Preview, announced April 7, 2026, represents the current frontier of AI cybersecurity capability. The AI Security Institute (AISI) evaluated Mythos and found it could execute multi-stage attacks on vulnerable networks and discover and exploit vulnerabilities autonomously — tasks that would take human professionals days of work {cite index="3-0:3"}. Project Glasswing, Anthropic's accompanying initiative, revealed that Mythos has already found thousands of high-severity vulnerabilities, including some in every major operating system and web browser {cite index="4-0:2"}. Mythos achieves 73% success on expert-level CTFs and was the first model to solve a 32-step corporate network attack end-to-end {cite index="0-0:1"}.

The critical limitation of Mythos is that it is a static model. It does not learn from its discoveries. Each engagement starts from scratch, with no memory, no feedback loop, and no self-improvement. This is precisely the gap that Temuclaude can exploit. By building a self-improving system that learns from every attack and every defense, Temuclaude can surpass Mythos over time, even with weaker base models.

### 1.2 OWASP Standards

Prompt injection remains the number one security vulnerability in OWASP's Top 10 for LLM Applications 2025, holding the same position it had in 2023 when the list debuted {cite index="7-0:2"}. Microsoft has reported indirect prompt injection as the most widely used AI attack technique, and researchers have achieved 100% evasion success against Azure Prompt Shield and Meta Prompt Guard {cite index="7-0:3"}. The persistence of prompt injection as the top threat reflects a fundamental architectural vulnerability: LLMs process instructions and data through the same channel, making separation inherently difficult.

The 2026 update introduced the OWASP Top 10 for Agentic Applications, a new standard addressing the unique threats of autonomous AI agents {cite index="1-0:2"}. This covers agent identity spoofing, unauthorized tool access, memory poisoning, agent-to-agent attacks, MCP protocol exploitation, skill and package supply chain attacks, unbounded autonomy, and context manipulation. Temuclaude, as a multi-agent orchestration system, falls squarely under this new standard and must implement defenses for all ten categories.

### 1.3 The Lifecycle Vulnerability Taxonomy

A systematic survey published in June 2026 organized LLM vulnerabilities across eight lifecycle stages: data collection, pretraining, post-training alignment, model packaging and supply chain, retrieval and memory, prompting and inference, tool and agent execution, and deployment and maintenance {cite index="6-0:8"}. Unlike earlier taxonomies that list isolated attack names, this systematization emphasizes where trust boundaries fail, how untrusted data becomes executable instruction, how delegated authority amplifies model errors, and why point defenses rarely suffice. The key insight is that security must be addressed at every stage, not just at inference time. A single defense, no matter how good, will be bypassed because attackers can target any stage of the lifecycle.

## Section 2: Input Defense (Prompt Injection and Jailbreak Prevention)

### 2.1 The Cognitive Firewall

The Cognitive Firewall, introduced in July 2026, represents the most promising runtime defense architecture for multi-turn attacks {cite index="5-0:2"}. It interposes an independent oversight model between the user and the protected target model, decomposing safety assessment into four categorical gates. The intent gate identifies the operational objective of a request, the zero-trust context gate treats claimed roles and permissions as unverified evidence, the consistency gate detects escalation and decomposition across turns, and the output risk gate inspects candidate responses before release. Gate decisions are combined through escalation rather than score averaging, allowing any confident danger signal to block an interaction while preserving an auditable rationale.

In experiments on four jailbreak benchmarks, the Cognitive Firewall substantially reduced attack success across single-turn, multi-turn, authority-based, and human-crafted attacks. It lowered attack success to 2 percent or below on three attack sets and to 14 percent on the most difficult human-crafted set, while maintaining an 8 percent false positive rate on benign requests. The escalation-based combination is critical: it means a single gate detecting danger can block the entire interaction, rather than all gates needing to agree. This is fundamentally different from score averaging, where a strong danger signal from one gate can be diluted by weak signals from others.

For Temuclaude, the Cognitive Firewall maps directly to the existing orchestrator architecture. The four gates can be implemented as pre-dispatch checks in the orchestrator's complete method, running before the model panel is invoked. The zero-trust context gate is particularly relevant because Temuclaude's agent system already tracks user roles and permissions — extending this to treat all claims as unverified evidence is a natural extension. The consistency gate leverages Temuclaude's existing session memory to detect escalation patterns across turns.

### 2.2 Constitutional Classifiers (HaloGuard)

HaloGuard 1.0, released in July 2026, provides an open-weights implementation of the constitutional-classifier paradigm for input safety {cite index="8-0:3"}. It achieves state-of-the-art performance on English and multilingual prompt-safety benchmarks at roughly one-tenth the model size of current leading open guard models. The safety constitution consists of 46 policies and 2,940 subcategories, driving synthetic data generation with exhaustive one-to-one paired counterfactuals that hold topic and vocabulary fixed while flipping intent. The HaloGuard 1.0-0.8B variant attains the best average F1 score of 90.9 of any open guard evaluated, outperforming baselines up to 27B parameters (over 30 times larger) while holding the false-positive rate to 4.3 and the false-negative rate to 9.5.

The critical innovation is the always-on adversarial red-teaming protocol that continuously hardens the guard against both common and sophisticated attacks. This is not a static classifier — it is continuously tested by an adversarial system and improved based on the results. This mirrors the Silmaril approach of self-healing defense and aligns with Temuclaude's daemon-based architecture, where a continuous security daemon can run adversarial tests against the guard and update it.

### 2.3 Training-Free Guardrails (kNNGuard)

kNNGuard, also from July 2026, takes a fundamentally different approach by requiring no fine-tuning at all {cite index="9-0:2"}. It utilizes the activation space of an off-the-shelf LLM, extracting hidden activations from a small bank of 50 safe and 50 unsafe prompts. It performs multi-layer kNN classification, fusing activation-space and embedding-space scores. Across six domains spanning topical and security prompts, kNNGuard achieves competitive or superior F1 scores compared to fine-tuned state-of-the-art guardrails while running 2.7 times faster than the best comparable guardrail, and 10 times faster than a fine-tuned safety classifier without gradient updates or fine-tuning.

Domain adaptation requires only updating the labeled bank, which can be constructed in under 10 seconds — several orders of magnitude faster than retraining a guardrail. For Temuclaude, this means that when a new type of attack is discovered by the offensive swarm, the defense can be updated in seconds by simply adding new examples to the labeled bank. No retraining, no fine-tuning, no GPU needed. This is the fastest defense update cycle possible and aligns perfectly with the self-improving architecture.

### 2.4 Self-Healing Injection Defense (Silmaril)

Silmaril, a Y Combinator P26 startup launched in 2026, is the first self-healing prompt injection defense {cite index="10-0:2"}. It catches 2 times more attacks at a 10 times lower latency than leading guardrails. Current defenses rely on recognizing known patterns and catch at best 61% of real-world attacks. Silmaril understands the application's attack surface and retrains continuously, blocking novel attack patterns in under an hour. It protects the entire AI stack: inputs, tool calls, MCP, connectors, and internal agents.

The key architectural insight is that static defenses fail because attackers generate new attack types faster than security teams can update rules. A self-healing defense closes this gap by continuously learning from new attacks. For Temuclaude, this means implementing a feedback loop where newly discovered attack patterns (from the red team daemon or from production logs) are immediately fed back into the classifier to update its detection capability. The daemon-based swarm architecture is ideal for this — a security daemon can run continuously, processing new attack patterns and updating the defense model.

## Section 3: Model Defense (Adversarial Robustness and Alignment)

### 3.1 HARC: Harmfulness-Refusal Coupling

HARC, introduced in July 2026, addresses the fundamental question of why jailbreaks succeed and how to prevent them at the model level {cite index="11-0:2"}. Prior work showed that aligned LLMs encode harmfulness and refusal as separable directions in the residual stream at prompt-side token positions. Jailbreaks succeed by suppressing either the refusal or the harmfulness direction before any token is generated, with distinct attack classes occupying separable regions of the harmfulness-refusal plane. HARC (Harmfulness-And-Refusal Coupling) is a fine-tuning method that pairs the two directions across both prompt and response positions, making it impossible for an attacker to suppress one without the other.

Because the intervention is confined to the harmfulness-refusal subspace, it leaves the rest of the residual stream intact and does not degrade general capability or inflate over-refusal. Across extensive experiments, HARC achieves the strongest robustness-capability-usability trade-off among six baselines spanning the major training-time and inference-time safety methods. The harmfulness and refusal directions transfer across five model families and two scales without architectural changes. For Temuclaude, this requires a fine-tuning pipeline (currently blocked by infrastructure) but represents the strongest model-level defense available.

### 3.2 Function-Calling Jailbreak Defense

The SMT (Simulated Moderation Traces) attack framework, published July 2026, reveals a structural vulnerability in stateful, function-calling LLM environments {cite index="12-0:3"}. Developer-defined schemas, structured arguments, and untrusted tool outputs are interleaved into a single shared model context, blurring the boundary between trusted control logic and untrusted data. Adversarial intent can be distributed across a multi-turn execution path, bypassing single-message safety checks. SMT consistently achieves the highest average attack success rate across prominent commercial LLMs from five providers.

The defense is architectural: validate function-call schemas strictly, treat all tool outputs as untrusted data (never as instructions), and separate trusted control logic from untrusted data in the model's context. Temuclaude's function-calling system must enforce these boundaries at the orchestrator level, sanitizing tool outputs before they enter the model's context and validating all function-call schemas against a strict allowlist.

## Section 4: Agent Defense (Tool-Use, MCP, and Agentic Security)

### 4.1 AI-Infra-Guard: Layered Red Teaming

AI-Infra-Guard, published June 2026, is the only open-source framework to span all layers of AI infrastructure security {cite index="13-0:3"}. It organizes AI red teaming around the observation that the attack surface of an AI agent is stratified across layers — infrastructure, protocol and tool, agent behavior, and model — and no single detection paradigm fits all of them. The framework matches a paradigm to each layer: deterministic rule matching over 75+ AI components and 1,400+ vulnerability rules, LLM-driven agentic auditing of MCP servers and agent-skill packages, multi-turn black-box agent red teaming, and a jailbreak harness with 26+ attack operators over 16 datasets.

For Temuclaude, AI-Infra-Guard provides both a framework for testing its own security and a reference architecture for implementing layered defenses. The 1,400+ vulnerability rules can be integrated as a scanning daemon that continuously checks Temuclaude's own infrastructure. The MCP server auditing capability is directly relevant because Temuclaude uses MCP for tool integration. The agent-skill package scanning addresses the supply chain risk of loading third-party skills.

### 4.2 The Self-Improving Red-Blue Loop

The autonomous-cybersecurity-system skill defines a five-layer architecture for self-improving cyber defense {cite index="0-0:5"}. The offensive swarm consists of hundreds of parallel attack agents, each specialized for a vulnerability class, all sharing findings through a central memory. The defensive shield receives vulnerability reports, generates patches, verifies patches against the original exploit, and deploys to staging. The verification loop re-attacks patched code to find bypasses or adjacent vulnerabilities. Knowledge distillation converts every finding, patch, bypass, and failure into structured data: detection rules, exploit patterns, prompt improvements, and fine-tuning examples. The capability upgrade feeds distilled knowledge back into agents via prompt updates, tool enhancements, and model fine-tuning.

The critical design principle is escalation gating: the system never escalates offensive techniques before defense has mastered the current level. Escalation happens on three axes — technique (basic bugs to complex chains like ROP and sandbox escapes), scope (single function to cross-module to cross-service to supply chain), and autonomy (shadow to assisted to bounded to full). This gating prevents the system from creating vulnerabilities faster than it can patch them, which would make it a liability rather than an asset.

For Temuclaude, this architecture maps onto the existing daemon swarm. The scout daemon becomes the vulnerability scanner, the distiller becomes the severity triager, the research daemon becomes the deep vulnerability analyst, the integrator becomes the patch generator, and the coordinator becomes the Red-Blue cycle manager. A new security daemon can be added specifically to run the Red-Blue loop, managing the escalation gating and knowledge distillation.

## Section 5: Code Defense (Vulnerability Detection and Self-Healing)

### 5.1 Antaeus: Logic Vulnerability Detection

Antaeus, published July 2026, addresses a gap in LLM-based vulnerability detection: logic vulnerabilities {cite index="14-0:3"}. Memory-safety bugs and established vulnerability classes can be detected through property violations, but logic vulnerabilities require inferring application-specific security invariants and implicit assumptions about intended behavior. Even frontier agentic models struggle because these invariants are often implicit and buried among unrelated code.

Antaeus follows a repository-scale pipeline: function prioritization using lightweight repo-wide security signals, context-grounded reasoning that combines local code context with a repository-level view, comparative validation to prune false positives, and structured reporting. It identifies security-sensitive sinks, derives safety conditions for safe execution, and checks whether they are locally satisfied. For Temuclaude, this provides a way to scan its own codebase for logic vulnerabilities that traditional security scanners miss.

### 5.2 Extending the Adversarial Verifier

Temuclaude already has an adversarial verifier (src/ui_ux/adversarial_verifier.py, 256 LOC) that spawns a breaker subagent to find bugs and a fixer subagent to fix them. Currently, this is used for code quality — the breaker looks for broken functionality, accessibility violations, performance issues, visual bugs, and logic errors. Extending this to cybersecurity is straightforward: add a security-focused breaker that attempts to jailbreak, inject prompts, exploit tool outputs, and find authorization bypasses. The fixer then patches the vulnerabilities found. This loop, running continuously as a daemon, becomes a self-attacking system that finds and fixes its own security weaknesses.

## Section 6: Supply Chain and Infrastructure Defense

### 6.1 Model Supply Chain Security

The lifecycle survey identifies model packaging and supply chain as a critical vulnerability stage {cite index="6-0:5"}. Models downloaded from HuggingFace or other registries can be poisoned, backdoored, or compromised. The defense is multi-layered: hash signing and verification on model load, weight diff analysis against known-good baselines, behavioral testing on every model update (run safety benchmarks to detect backdoors), and dependency scanning for all packages.

Temuclaude uses models from multiple providers via cloud APIs, which reduces but does not eliminate supply chain risk. The API providers themselves can be compromised, and the model responses can be manipulated. Runtime integrity verification — checking that responses match expected quality and safety baselines — provides a defense against this. If a model suddenly starts producing unsafe outputs, the safety monitor can flag it and switch to an alternative model.

### 6.2 Backdoor Attack Detection

Multiple July 2026 papers address backdoor attacks. Pmeta-TLA uses meta-learning with timbre leakage to inject backdoors into speech classification models {cite index="15-0:2"}. ReShift injects reasoning-level backdoors into vision-language models through aha-moment manipulation {cite index="16-0:2"}. These attacks are difficult to detect because they activate only on specific triggers that may not appear in standard safety tests. Defense requires trigger pattern detection in training data, weight analysis for dormant backdoors, and behavioral testing with known trigger patterns.

## Section 7: Integration with the Existing Swarm

### 7.1 Daemon Architecture Extension

The existing Temuclaude research swarm runs seven daemons: scout, distiller, three research daemons, integrator, and coordinator. Adding cybersecurity research requires extending each of these daemons with cybersecurity queries and priorities, plus adding a dedicated security research daemon that runs the Red-Blue loop.

The scout daemon currently cycles through arXiv, GitHub, and HuggingFace scouts with queries focused on orchestration, reasoning, multi-agent systems, and cost optimization. Adding 20+ cybersecurity queries covering jailbreak defense, prompt injection, adversarial robustness, autonomous red teaming, vulnerability detection, supply chain attacks, backdoor attacks, and agentic security expands the scout's coverage without requiring structural changes.

The dynamic priority engine currently tracks 12 implemented techniques, 7 missing techniques, 12 blocked techniques, and 10 saturated areas. Adding 15+ cybersecurity techniques as missing or blocked items, with impact scores of 8-10 (security is critical), raises cybersecurity to the top of the research priority queue. The marketing strategy remains the highest priority (145 points), but cybersecurity techniques like the Cognitive Firewall and self-healing guard will rank at 90-115 points, placing them in the top 5.

### 7.2 The Cyber Security Daemon

A new dedicated daemon, cyber_daemon.py, will run the continuous security research and defense loop. It will pull cybersecurity findings from the queue, research them deeply, generate implementation plans for new defenses, and queue them for the integrator. It will also run the Red-Blue loop: spawning attack agents to test Temuclaude's own defenses, spawning defense agents to patch any vulnerabilities found, and distilling the results into knowledge for the next cycle.

This daemon will be registered with the coordinator, which will monitor its health and restart it if it dies. The coordinator's DAEMON_SCRIPTS mapping will be updated to include the new cyber daemon, and its get_all_daemon_statuses function will track it.

## Conclusion

The research reveals that Temuclaude can achieve unbeatable cybersecurity through a layered, self-improving architecture that leverages its existing daemon-based swarm. The key findings are: the Cognitive Firewall provides the strongest runtime defense (2% attack success), HaloGuard and kNNGuard provide fast, multilingual input classification, HARC provides the strongest model-level alignment defense, AI-Infra-Guard provides the framework for continuous self-testing, and the self-improving Red-Blue loop provides the architecture for continuous improvement. The competitive advantage comes from the scaffolding, not the model weights — a well-architected system using free models can match or exceed a frontier model. By extending the existing swarm with cybersecurity research queries, priority items, and a dedicated security daemon, Temuclaude can build full-stack, unbeatable cybersecurity capabilities that get stronger every day.