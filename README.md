# TemuClaude

TemuClaude is a small, OpenAI-compatible API that routes each request to one of three models:

- **GLM 5.2** — general reasoning, analysis, and planning
- **Kimi K3** — code generation, autonomous agents, deployment, and multi-agent workflows
- **Grok 4.5** — debugging, code review, security review, and repair

The router makes one primary model call per request. The other two models are availability fallbacks, not an always-on panel. This keeps latency, cost, and failure modes understandable.

## API

```bash
curl https://temuclaude.com/v1/chat/completions \
  -H "Authorization: Bearer $TEMUCLAUDE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "temuclaude/temuclaude",
    "messages": [{"role":"user","content":"Implement a reliable deployment workflow"}]
  }'
```

## Development

```bash
git clone https://github.com/notSaiful/temuclaude.git
cd temuclaude/website
cp .env.example .env
npm install
npm run dev
```

Only `OPENROUTER_API_KEY` is required to run model calls locally. Supabase credentials are required for production API-key persistence.
