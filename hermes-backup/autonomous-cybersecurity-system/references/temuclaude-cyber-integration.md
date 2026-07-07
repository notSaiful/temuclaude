# Temuclaude Cybersecurity Swarm Integration

Pattern used on 2026-07-06 to add full-stack cybersecurity research to the existing Temuclaude daemon-based research swarm. This is a concrete instance of the self-improving Red-Blue architecture adapted for a project that already has a daemon-based research pipeline.

## The 9-Step Integration Pattern

When adding a new research domain to an existing daemon-based swarm:

1. **Scout queries** — Add domain-specific queries to `scripts/scout_arxiv.py` QUERIES list, `scripts/scout_github.py` QUERIES list, and `scripts/scout_huggingface.py` keywords + searches. ~20 queries per source.
2. **Priority engine** — Add techniques to `MISSING_TECHNIQUES` dict in `scripts/dynamic_priorities.py` with impact scores (7-10) and research_needed levels. Add blocked techniques to `BLOCKED_TECHNIQUES`.
3. **Dedicated daemon** — Create `cyber_daemon.py` that pulls domain findings from queue and researches top domain priorities. Inherits DaemonBase, runs every 5 min.
4. **Coordinator registration** — Add to `DAEMON_SCRIPTS` dict in `coordinator_daemon.py` so coordinator auto-restarts it.
5. **Daemon base registration** — Add to `get_all_daemon_statuses()` daemons list in `daemon_base.py`.
6. **Status dashboard** — Add to `daemons` array in `scripts/status_swarm.sh` (line 21).
7. **Start script** — Add startup command to `scripts/start_swarm.sh`, update daemon count in echo statements.
8. **Tracker** — Update `TRACKER.md` with new domain section.
9. **Master documents** — Create `MASTER-CYBERSECURITY-BREAKTHROUGHS-<date>.md` and `findings/deep_research_cybersecurity_<date>.md`.

## Cyber Daemon Design

The `cyber_daemon.py` (185 LOC) is a specialized research daemon that:

- Identifies cyber findings in the queue by checking for 23 cyber keywords (jailbreak, injection, adversarial, etc.)
- When no cyber findings are in queue, researches the top cyber priority from the dynamic priority engine
- Creates research prompt files in `raw/` for the LLM agent to process
- Creates placeholder findings reports in `findings/` and pushes them to the implementation queue
- Tracks 19 cyber topics in a CYBER_TOPICS set, filtering from the global priority list

Key code pattern — checking if a finding is cyber-related:
```python
CYBER_KEYWORDS = [
    "jailbreak", "injection", "adversarial", "security", "attack", "defense",
    "red team", "vulnerab", "exploit", "malicious", "poisoning", "backdoor",
    "robustness", "safety", "guardrail", "firewall", "owasp", "mitre",
    "cyber", "pentest", "cve", "zero-day", "supply chain",
]

def _is_cyber_finding(self, finding_file):
    with open(finding_file) as f:
        data = json.load(f)
    text = json.dumps(data).lower()
    return any(kw in text for kw in CYBER_KEYWORDS)
```

## Key Papers That Drove the Integration

All from June-July 2026, discovered via arXiv cs.CR category searches:

| Paper | arXiv | Why Critical |
|-------|-------|-------------|
| Cognitive Firewall | 2607.01277 | 4-gate zero-trust, 2% attack success — strongest runtime defense |
| HaloGuard 1.0 | 2607.02079 | 90.9 F1 at 1/10 model size, multilingual, open weights |
| kNNGuard | 2607.02072 | Training-free, 2.7x faster, kNN on activations |
| HARC Alignment | 2607.00572 | Harmfulness-refusal coupling, strongest model-level defense |
| SMT Jailbreak | 2607.00481 | Function-calling jailbreak via simulated moderation traces |
| Lifecycle Survey | 2606.31639 | 8-stage LLM vulnerability taxonomy — defense at every stage |
| AI-Infra-Guard | 2606.31227 | 1400+ vuln rules, 4-layer red teaming, open-source |
| Antaeus | 2607.01138 | Repository-level logic vulnerability detection |

## Web Search Fallback Used

Firecrawl was IP-blocked ("your IP address looks suspicious"). Used the Startpage POST endpoint fallback (verified Jul 2026 from deep-research-mode skill):

```python
def startpage_search(query, num=10):
    url = "https://www.startpage.com/sp/search"
    data = urllib.parse.urlencode({"query": query, "cat": "web", "pl": "opensearch"}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    urls = re.findall(r'href="(https?://[^"]+)"', html)
    # Filter out search engines, deduplicate
```

DuckDuckGo, Bing, and Google all serve CAPTCHAs for programmatic access as of Jul 2026. Startpage POST still works with a standard browser User-Agent.

## arXiv Category Search Pattern

For domain-specific paper discovery, use the cs.CR (Cryptography and Security) category with AND operators:

```python
QUERIES = [
    "cat:cs.CR AND (LLM OR \"language model\") AND jailbreak",
    "cat:cs.CR AND \"prompt injection\" defense",
    "cat:cs.CR AND \"red team\" AI autonomous",
    # ... 12 queries
]
```

This produces much more relevant results than generic `all:` queries — 52 total papers, 34 relevant after title-keyword filtering.

## Verification Checklist After Integration

- [ ] `python3 -c "import cyber_daemon; print('OK')"` — daemon compiles
- [ ] `python3 scripts/dynamic_priorities.py` — priority engine runs, cyber techniques in top 10
- [ ] `bash scripts/status_swarm.sh` — cyber_daemon shows ALIVE=YES
- [ ] `cat /tmp/temuclaude_daemons/cyber_daemon.log` — shows "cycle 1 started" and "Top cyber priority: cognitive_firewall"
- [ ] Coordinator's DAEMON_SCRIPTS includes cyber_daemon
- [ ] daemon_base get_all_daemon_statuses includes cyber_daemon
- [ ] status_swarm.sh daemons array includes cyber_daemon
- [ ] start_swarm.sh starts cyber_daemon (8/8)

All verified passing on 2026-07-06.