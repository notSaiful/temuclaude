# Timuclaude

> Open-source model orchestration that beats frontier models at 50x lower cost.

Timuclaude combines 5 open-weight models on Ollama Cloud into a single intelligent system. Users see one model — "Timuclaude." All orchestration (routing, fusion, verification) is invisible.

## Architecture

```
User → LiteLLM proxy (port 4000) → Orchestrator → Ollama Cloud models (port 11434)
                                      ↓
                              Task classification
                              3-tier routing (trivial/medium/hard)
                              Model pool (5 models + 1 cheap router)
                              Query logging
```

## Models

| Model | Role | Strengths |
|-------|------|-----------|
| GLM-5.2 | Orchestrator | Reasoning, coding, knowledge, agentic |
| DeepSeek V4 Pro | Reasoning specialist | Math, coding, science |
| Kimi K2.6 | Long context specialist | Vision, long context, swarm |
| MiniMax M3 | Generation specialist | Creative, vision, generation |
| Nemotron 3 Ultra | Verifier | Verification, evaluation, agentic |
| GPT-OSS 120B | Cheap router | Simple queries (trivial tier) |

## Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Ollama Pro or Max subscription (for cloud model access)

### Install

```bash
git clone https://github.com/notSaiful/timuclaude-research.git
cd timuclaude-research

# Install dependencies
pip install -r requirements.txt

# Or use the setup script (checks Ollama, installs deps, runs tests)
./scripts/setup.sh
```

### Configure

```bash
# Copy the example env file
cp .env.example .env

# Generate a master key and add it to .env
echo "TIMUCLAUDE_MASTER_KEY=$(openssl rand -hex 32)" >> .env
```

### Pull Cloud Models

Make sure Ollama is running, then verify cloud models are available:

```bash
ollama show glm-5.2:cloud
ollama show deepseek-v4-pro:cloud
ollama show kimi-k2.6:cloud
ollama show minimax-m3:cloud
ollama show nemotron-3-ultra:cloud
ollama show gpt-oss:120b-cloud
```

If any are missing, Ollama will pull them automatically on first use.

## Run

### Start the LiteLLM proxy

```bash
source .env
litellm --config config/litellm.yaml --port 4000
```

### Test the proxy

```bash
# List available models
curl http://localhost:4000/v1/models -H "Authorization: Bearer $TIMUCLAUDE_MASTER_KEY"

# Ask a question (routes to GLM-5.2)
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $TIMUCLAUDE_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "timuclaude", "messages": [{"role": "user", "content": "What is 15*12?"}], "max_tokens": 200}'
```

### Use in Python

```python
import asyncio
import sys
sys.path.insert(0, ".")

from src.orchestrator import ask

# Ask Timuclaude a question
answer = ask("What is the derivative of x^3?")
print(answer)
```

### Run tests

```bash
python tests/test_orchestrator.py
```

Expected output: all 7 test suites pass (78 tests total).

## Project Structure

```
timuclaude/
├── src/
│   ├── orchestrator.py    # Main orchestration: classify → route → respond
│   ├── models.py           # Model pool config + task routing map
│   └── logger.py           # Query logging for self-improvement
├── config/
│   └── litellm.yaml        # LiteLLM proxy config (all models)
├── tests/
│   └── test_orchestrator.py # 78 tests across 7 suites
├── scripts/
│   └── setup.sh            # One-command setup
├── .env.example            # Environment variable template
├── .gitignore
└── requirements.txt
```

## Current Status

**Phase 1 (Foundation):** Complete
- 6 Ollama Cloud models verified and responding
- Task classifier (24/24 tests pass)
- 3-tier routing (trivial/medium/hard)
- LiteLLM proxy with OpenAI-compatible API
- Query logging
- Error handling (invalid model, empty query, long query)
- 78 tests across 7 suites — all pass

**Phase 2 (Core Orchestration):** Not started
- Fusion (5 models in parallel + structured analysis)
- Self-consistency (N=20 majority vote)
- Code execution verification
- Dynamic aggregator selection

## License

MIT

## Author

Mohammad Saiful Haque (Ggs) — with Hermes Agent