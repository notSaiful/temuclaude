# Self-Improving Red-Blue Architecture Blueprint

Detailed design for the 5-layer autonomous cybersecurity system described in SKILL.md.

## Layer 1: Offensive Swarm

### Agent Specializations

Each agent type targets a specific vulnerability class:

| Agent Type | Vulnerability Class | Key Techniques |
|-----------|---------------------|----------------|
| memory-corruption | buffer overflow, use-after-free, double-free | fuzzing, crash analysis, ROP chain construction |
| injection | SQLi, XSS, command injection, LDAP injection | payload generation, WAF bypass, blind injection timing |
| auth-bypass | broken auth, JWT flaws, session fixation | token analysis, replay attacks, privilege escalation |
| privesc | Linux kernel, Windows, container escape | race conditions, kernel exploits, capability abuse |
| sandbox-escape | browser renderer, OS sandbox, VM escape | JIT spray, type confusion, shared memory abuse |
| supply-chain | dependency confusion, typosquatting, malicious packages | package analysis, SBOM diffing, CI/CD poisoning |
| logic-flaws | business logic, race conditions, TOCTOU | state machine analysis, concurrent request testing |
| crypto | weak ciphers, padding oracles, key management | known-plaintext, timing attacks, certificate validation |

### Parallelization Strategy

- Run N agents concurrently across different files/repos (not sequential)
- Each agent shares findings in real-time via shared memory
- File ranking: multi-model approach (different models rank files, disagreements prioritized)
- Cost target: $0.10-$1.00 per file analyzed using free/cheap models

### The Confirmation Loop (Improved from Mythos)

Mythos uses a single confirmation agent. Improvement:
1. Execution agent actually attempts exploit in sandbox (not just judgment)
2. If exploit succeeds → verified finding
3. If exploit fails → feed failure back to offensive agent for refinement
4. Repeat until success or budget exhausted

## Layer 2: Defensive Shield

### Patch Generation Pipeline

1. Receive verified vulnerability report
2. Locate vulnerable code (may span multiple files)
3. Generate candidate patches (multiple approaches per vuln)
4. Verify each patch against original exploit
5. Select best patch (minimal change, passes all tests, blocks exploit)
6. Deploy to staging environment
7. Run full regression suite
8. If regressions → refine patch; if clean → ready for production

### Self-Healing Code Progression (from CodeRabbit)

| Level | Description | Production-Ready? |
|-------|-------------|-------------------|
| 1 | Detection + rollback | YES |
| 2 | Deterministic recovery | YES |
| 3 | Narrow AI repair (human approves) | YES (security patching) |
| 4 | Strengthen verification | In progress |
| 5 | Bounded AI autonomy in CI | Partial |
| 6 | Full agent-driven PR repair | NO (needs human oversight) |

Key risk: **test overfitting** — AI patch passes every test but is semantically incorrect. Mitigate with property-based testing and semantic equivalence checking.

## Layer 3: Verification Loop

The offensive swarm re-attacks patched code:
- Can the original exploit be modified to bypass the patch?
- Did the patch introduce new vulnerabilities (regression vulns)?
- Are there adjacent code paths that share the same pattern but weren't patched?
- Does the patch break any security properties (e.g., adds a dangerous fallback)?

If bypass found → new finding → feeds back to defensive shield → repeat.

## Layer 4: Knowledge Distillation

### Neuro-Symbolic Rule Extraction (QRS approach)

When offensive agent discovers a new vulnerability pattern:
1. LLM generates candidate detection rule (natural language + code pattern)
2. Symbolic engine validates rule against known vulnerability database
3. Validated rule added to:
   - Defensive scanner's rule set (future scans detect this pattern)
   - Offensive agent's "known patterns to try" list (test other codebases)
4. Rule becomes permanent, inspectable, modifiable — not a one-off finding

### Training Data Generation

Every cycle produces:
- (vulnerable_code, vulnerability_description, exploit, patch) tuples
- (false_positive, reason) pairs for triage training
- (attack_chain, reasoning_steps) for chain construction training
- (model_performance, task_type) records for dynamic routing

## Layer 5: Capability Upgrade

### Escalation Gating Rules

```
IF defensive_coverage(current_techniques) >= 90%:
    AND offensive_success_rate(current_techniques) <= 10%:
    THEN introduce next_technique_level
ELSE:
    continue_improving_defense(current_techniques)
```

Never escalate offense before defense has mastered current level.

### Upgrade Mechanisms

1. **Prompt updates** — Add new attack patterns, detection rules, and lessons to agent system prompts
2. **Tool enhancements** — New tools for new vulnerability classes (e.g., binary analysis, firmware RE)
3. **Model fine-tuning** — Distilled training data used for LoRA/QLoRA fine-tuning of base models
4. **Architecture improvements** — New agent types, better memory queries, improved coordination

## Shared Memory Schema (Context Lake)

```
vulnerability_signatures:
  - id: UUID
  - pattern: code_pattern (AST + text)
  - class: vulnerability_class
  - severity: 1-5 (CVSS)
  - exploit: PoC code
  - proof: execution trace
  - patch: code diff
  - verification: pass/fail/bypass
  - discovered_by: agent_id
  - discovered_at: timestamp
  - codebase_fingerprint: hash

attack_chains:
  - id: UUID
  - steps: [vulnerability_signature_ids]
  - reasoning: [step_connections]
  - target_impact: description
  - mitre_attack: [technique_ids]

false_positives:
  - pattern: code_pattern
  - reason: explanation
  - agent_id: who flagged it
  - resolution: not_a_bug / low_severity / duplicate

coverage_map:
  - mitre_attack_technique: TXXXX
  - detectable: bool
  - exploitable: bool
  - defended: bool
  - last_tested: timestamp
  - detection_rules: [rule_ids]

model_performance:
  - model: model_name
  - task_type: scanning|detection|triage|patch|exploit
  - success_rate: float
  - cost_per_task: float
  - sample_count: int
```

## Free-Model Routing Strategy

```python
def route_task(task_type, codebase_complexity):
    """Route task to cheapest model that historically performs well."""
    perf = memory.query_model_performance(task_type)
    candidates = [m for m in perf if m.success_rate > THRESHOLD]
    candidates.sort(key=lambda m: m.cost_per_task)
    return candidates[0] if candidates else FRONTIER_MODEL_FALLBACK

# Tiered strategy:
# Tier 1 (free/cheap, 3.6B-7B): broad-spectrum scanning, triage, false-positive filtering
# Tier 2 (mid-tier, 13B-70B): detailed analysis, exploit construction, patch generation
# Tier 3 (frontier, only when needed): complex exploit chains, novel vulnerability discovery
```

## Cycle Metrics

Track per cycle:
- Findings discovered, by severity and novelty
- Patches generated, verified, deployed
- Bypasses found (re-attack success)
- Coverage improvement (MITRE ATT&CK delta)
- Cost per finding (API tokens consumed)
- Cycle time (start to finish)
- False positive rate
- Model performance breakdown

Goal: cycle time compresses from days → hours → minutes. Ultimate goal: cycle time < human attacker exploitation time.